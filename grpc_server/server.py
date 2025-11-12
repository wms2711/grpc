# grpc_server/server.py
"""
gRPC Book Catalog Server

This module implements a gRPC server for managing a book catalog using Protocol Buffers.
The server provides high-performance RPC endpoints for listing and adding books, with
data persisted to a JSON file for simplicity.

Service Definition:
- ListBooks: Retrieves all books in the catalog
- AddBook: Adds a new book with auto-generated ID

Key Features:
- Protocol Buffer serialization for efficient data transfer
- Thread pool for concurrent request handling
- JSON file-based persistence shared with REST server
- Automatic ID generation for new books

Compare with REST server (rest_server/server.py) for performance benchmarking.
"""
import grpc
import json
import os
from concurrent import futures

import book_pb2
import book_pb2_grpc

# Path to the shared JSON database file
DB_PATH = os.path.join(os.path.dirname(__file__), "books.json")

def load_books():
    """
    Load books from the JSON database file.
    
    Returns:
        list: List of book dictionaries with 'id', 'title', 'author', 'year' keys.
              Returns empty list if file doesn't exist.
    
    Note:
        This file is shared with the REST server for fair benchmarking comparison.
    """
    if not os.path.exists(DB_PATH):
        return []
    with open(DB_PATH, "r") as f:
        return json.load(f)

def save_books(books):
    """
    Save books to the JSON database file.
    
    Args:
        books (list): List of book dictionaries to persist
    
    Note:
        Uses indentation for human-readable JSON output.
        Changes are immediately written to disk (no caching).
    """
    with open(DB_PATH, "w") as f:
        json.dump(books, f, indent=2)

class BookCatalogServicer(book_pb2_grpc.BookCatalogServicer):
    """
    Implementation of the BookCatalog gRPC service.
    
    This servicer handles RPC calls defined in book.proto and implements
    the business logic for book management operations. It inherits from
    the auto-generated base class and overrides service methods.
    """
    
    def ListBooks(self, request, context):
        """
        RPC handler: Retrieve all books in the catalog.
        
        Args:
            request (ListBooksRequest): Empty request message (no parameters needed)
            context: gRPC context with metadata and state
        
        Returns:
            ListBooksResponse: Protocol Buffer message containing list of Book objects
        
        Process:
            1. Load books from JSON database
            2. Convert each dict to Protocol Buffer Book message
            3. Return response with all books
        """
        # Load books from persistent storage
        books = load_books()
        
        # Convert JSON dicts to Protocol Buffer Book messages
        pb_books = [
            book_pb2.Book(id=b["id"], title=b["title"], author=b["author"], year=b["year"])
            for b in books
        ]
        
        # Return Protocol Buffer response
        return book_pb2.ListBooksResponse(books=pb_books)

    def AddBook(self, request, context):
        """
        RPC handler: Add a new book to the catalog.
        
        Args:
            request (AddBookRequest): Contains title, author, and year fields
            context: gRPC context with metadata and state
        
        Returns:
            AddBookResponse: Protocol Buffer message with the newly created Book
        
        Process:
            1. Load existing books from database
            2. Generate unique ID (max existing ID + 1)
            3. Create new book dict from request data
            4. Append to books list and save to disk
            5. Return the created book as Protocol Buffer message
        """
        # Load current books from persistent storage
        books = load_books()
        
        # Generate next available ID (auto-increment)
        new_id = max((b["id"] for b in books), default=0) + 1
        
        # Create new book dict from Protocol Buffer request fields
        book = {
            "id": new_id,
            "title": request.title,
            "author": request.author,
            "year": request.year
        }
        
        # Add to catalog and persist to disk
        books.append(book)
        save_books(books)
        
        # Return Protocol Buffer response with created book
        return book_pb2.AddBookResponse(
            book=book_pb2.Book(id=book["id"], title=book["title"],
                               author=book["author"], year=book["year"])
        )

def serve():
    """
    Initialize and start the gRPC server.
    
    Server Configuration:
    - Thread pool: 10 concurrent workers for handling multiple requests
    - Port: 50051 (binds to all interfaces via [::])
    - Security: Insecure channel (no TLS) for local development
    
    The server runs indefinitely until interrupted (Ctrl+C) or terminated.
    
    Process:
        1. Create gRPC server with thread pool executor
        2. Register BookCatalogServicer implementation
        3. Bind to port 50051 on all network interfaces
        4. Start accepting requests
        5. Block until server termination
    """
    # Create server with thread pool for concurrent request handling
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    
    # Register our service implementation with the server
    book_pb2_grpc.add_BookCatalogServicer_to_server(BookCatalogServicer(), server)
    
    # Bind to port 50051 on all interfaces ([::] includes IPv4 and IPv6)
    server.add_insecure_port('[::]:50051')
    
    # Start the server and begin accepting requests
    server.start()
    print("gRPC server running on port 50051")
    
    # Block here until server is terminated (Ctrl+C or kill signal)
    server.wait_for_termination()

if __name__ == '__main__':
    """
    Entry point: Start the gRPC server when run as a script.
    
    Usage:
        python server.py
    
    The server will run in the foreground and log requests to stdout.
    Stop with Ctrl+C or by terminating the process.
    """
    serve()