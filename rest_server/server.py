# rest_server/server.py
"""
REST API Book Catalog Server

This module implements a RESTful HTTP API for managing a book catalog using Flask.
The server provides JSON-based endpoints for listing and adding books, with data
persisted to a JSON file for simplicity.

API Endpoints:
- GET /books: Retrieve all books in the catalog
- POST /books: Add a new book with auto-generated ID

Key Features:
- JSON serialization for human-readable data transfer
- Flask web framework for easy HTTP handling
- JSON file-based persistence shared with gRPC server
- Automatic ID generation for new books

Compare with gRPC server (grpc_server/server.py) for performance benchmarking.
"""
from flask import Flask, jsonify, request
import json
import os

# Initialize Flask application
app = Flask(__name__)

# Path to the shared JSON database file
DB_PATH = os.path.join(os.path.dirname(__file__), "books.json")

def load_books():
    """
    Load books from the JSON database file.
    
    Returns:
        list: List of book dictionaries with 'id', 'title', 'author', 'year' keys.
              Returns empty list if file doesn't exist.
    
    Note:
        This file is shared with the gRPC server for fair benchmarking comparison.
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

@app.route("/books", methods=["GET"])
def list_books():
    """
    REST endpoint: Retrieve all books in the catalog.
    
    Route: GET /books
    
    Returns:
        JSON response: Array of book objects with status 200
        Example: [{"id": 1, "title": "...", "author": "...", "year": 2020}, ...]
    
    Process:
        1. Load books from JSON database
        2. Serialize to JSON and return with HTTP 200 status
    """
    return jsonify(load_books())

@app.route("/books", methods=["POST"])
def add_book():
    """
    REST endpoint: Add a new book to the catalog.
    
    Route: POST /books
    
    Request Body (JSON):
        {
            "title": "Book Title",
            "author": "Author Name",
            "year": 2020
        }
    
    Returns:
        JSON response: The created book object with auto-generated ID
        Status: 201 Created
        Example: {"id": 5, "title": "...", "author": "...", "year": 2020}
    
    Process:
        1. Parse JSON request body
        2. Load existing books from database
        3. Generate unique ID (max existing ID + 1)
        4. Create new book dict with request data
        5. Append to books list and save to disk
        6. Return created book with 201 status
    """
    # Parse JSON from request body
    data = request.get_json()
    
    # Load current books from persistent storage
    books = load_books()
    
    # Generate next available ID (auto-increment)
    new_id = max((b["id"] for b in books), default=0) + 1
    
    # Create new book dict from request data
    book = {
        "id": new_id,
        "title": data["title"],
        "author": data["author"],
        "year": data["year"]
    }
    
    # Add to catalog and persist to disk
    books.append(book)
    save_books(books)
    
    # Return created resource with 201 Created status
    return jsonify(book), 201

if __name__ == "__main__":
    """
    Entry point: Start the Flask development server when run as a script.
    
    Server Configuration:
    - Host: 0.0.0.0 (accessible from all network interfaces)
    - Port: 5000 (standard Flask development port)
    
    Usage:
        python server.py
    
    The server will run in the foreground and log requests to stdout.
    Stop with Ctrl+C or by terminating the process.
    
    Note:
        This uses Flask's built-in development server. For production,
        use a WSGI server like gunicorn or uwsgi.
    """
    app.run(host="0.0.0.0", port=5000)