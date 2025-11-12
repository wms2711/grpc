# client/seeder.py
"""
Data Seeder for Book Catalog Servers

This module provides a utility class to populate both REST and gRPC book catalog
servers with sample data. It's designed to ensure consistent test data across
both implementations for accurate benchmarking and testing.

Key Features:
- Seeds both REST and gRPC servers with identical data
- Uses object-oriented design for reusable seeding logic
- Maintains persistent connections for efficient bulk operations
- Can be used as a module or run as a standalone script
"""
import json
import os
from typing import List, Dict

import requests
import grpc
import sys

# Make the generated protobuf modules importable
# This adds the grpc_server directory to Python's import path
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "grpc_server"))
import book_pb2
import book_pb2_grpc


class CatalogSeeder:
    """
    Encapsulates seeding logic for REST and gRPC book catalog servers.
    
    This class provides methods to populate both server implementations
    with sample book data. It maintains persistent connections for efficiency
    and ensures data consistency across both servers.
    
    Attributes:
        REST_URL (str): Base URL for the REST API endpoint
        GRPC_ADDR (str): Address and port for the gRPC server
        _rest_session: Persistent HTTP session for REST requests
        _grpc_channel: Lazy-loaded gRPC channel
        _stub: Lazy-loaded gRPC service stub
    """

    REST_URL = "http://localhost:5000/books"
    GRPC_ADDR = "localhost:50051"

    def __init__(self):
        """
        Initialize the seeder with a persistent REST session.
        
        The gRPC channel is created lazily on first use to avoid
        connection overhead if only REST seeding is needed.
        """
        self._rest_session = requests.Session()
        self._grpc_channel = None
        self._stub = None

    # --------------------------------------------------------------------- #
    # REST helpers
    # --------------------------------------------------------------------- #
    def _rest_add(self, title: str, author: str, year: int) -> Dict:
        """
        Add a single book to the REST server.
        
        Args:
            title: Book title
            author: Book author
            year: Publication year
        
        Returns:
            Dict containing the created book with server-assigned ID
        
        Raises:
            requests.HTTPError: If the server returns an error status
        """
        payload = {"title": title, "author": author, "year": year}
        r = self._rest_session.post(self.REST_URL, json=payload)
        r.raise_for_status()  # Raise exception for HTTP errors
        return r.json()

    # --------------------------------------------------------------------- #
    # gRPC helpers (lazy channel creation)
    # --------------------------------------------------------------------- #
    def _get_grpc_stub(self):
        """
        Get or create the gRPC service stub.
        
        Uses lazy initialization: the gRPC channel and stub are only created
        on first access. This avoids unnecessary connection overhead if the
        seeder is only used for REST operations.
        
        Returns:
            BookCatalogStub: The gRPC service stub for making RPC calls
        """
        if self._stub is None:
            # Create insecure channel (no TLS) for local development
            self._grpc_channel = grpc.insecure_channel(self.GRPC_ADDR)
            self._stub = book_pb2_grpc.BookCatalogStub(self._grpc_channel)
        return self._stub

    def _grpc_add(self, title: str, author: str, year: int) -> book_pb2.Book:
        """
        Add a single book to the gRPC server.
        
        Args:
            title: Book title
            author: Book author
            year: Publication year
        
        Returns:
            book_pb2.Book: The created book as a Protocol Buffer object
        """
        # Create Protocol Buffer request message
        req = book_pb2.AddBookRequest(title=title, author=author, year=year)
        # Make RPC call and extract the book from the response
        resp = self._get_grpc_stub().AddBook(req)
        return resp.book

    # --------------------------------------------------------------------- #
    # Public API
    # --------------------------------------------------------------------- #
    def seed_rest(self, books: List[Dict]) -> List[Dict]:
        """
        Add multiple books to the REST server.
        
        Args:
            books: List of book dictionaries with 'title', 'author', 'year' keys
        
        Returns:
            List of created book dictionaries including server-assigned IDs
        """
        return [self._rest_add(b["title"], b["author"], b["year"]) for b in books]

    def seed_grpc(self, books: List[Dict]) -> List[book_pb2.Book]:
        """
        Add multiple books to the gRPC server.
        
        Args:
            books: List of book dictionaries with 'title', 'author', 'year' keys
        
        Returns:
            List of created books as Protocol Buffer Book objects
        """
        return [self._grpc_add(b["title"], b["author"], b["year"]) for b in books]

    def seed_both(self, books: List[Dict]) -> None:
        """
        Seed BOTH REST and gRPC servers with identical data.
        
        This method ensures both server implementations have the same book
        catalog, which is essential for accurate benchmarking and testing.
        Since both servers share the same underlying books.json file,
        this guarantees identical database state.
        
        Args:
            books: List of book dictionaries to add to both servers
        
        Note:
            Seeds REST first (simpler protocol) then mirrors with gRPC.
            Progress messages are printed to stdout.
        """
        print("Seeding REST …")
        self.seed_rest(books)
        print("Seeding gRPC …")
        self.seed_grpc(books)
        print(f"Added {len(books)} books to both servers.")

    def close(self):
        """
        Close any open gRPC channel and clean up resources.
        
        Should be called when done with the seeder to properly
        release network resources. The REST session closes automatically.
        """
        if self._grpc_channel:
            self._grpc_channel.close()


# ------------------------------------------------------------------------- #
# Convenience – run as a script
# ------------------------------------------------------------------------- #

# Default sample books for testing and benchmarking
# Includes classic programming books with realistic metadata
DEFAULT_BOOKS = [
    {"title": "Clean Code", "author": "Robert C. Martin", "year": 2008},
    {"title": "The Pragmatic Programmer", "author": "Andrew Hunt", "year": 1999},
    {"title": "Design Patterns", "author": "Gang of Four", "year": 1994},
    {"title": "gRPC Up and Running", "author": "Kasun Indrasiri", "year": 2020},
]

if __name__ == "__main__":
    """
    Standalone script mode: Seeds both servers with default books.
    
    Usage:
        python seeder.py
    
    This allows quick population of test data without writing additional code.
    Ensures proper cleanup of gRPC connections via try/finally block.
    """
    seeder = CatalogSeeder()
    try:
        seeder.seed_both(DEFAULT_BOOKS)
    finally:
        seeder.close()  # Always clean up, even if seeding fails