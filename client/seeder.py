# client/seeder.py
"""
OOP Seeder – adds realistic books to *both* servers without touching the
original code.
"""
import json
import os
from typing import List, Dict

import requests
import grpc
import sys

# Make the generated protobuf modules importable
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "grpc_server"))
import book_pb2
import book_pb2_grpc


class CatalogSeeder:
    """Encapsulates seeding logic for REST and gRPC servers."""

    REST_URL = "http://localhost:5000/books"
    GRPC_ADDR = "localhost:50051"

    def __init__(self):
        self._rest_session = requests.Session()
        self._grpc_channel = None
        self._stub = None

    # --------------------------------------------------------------------- #
    # REST helpers
    # --------------------------------------------------------------------- #
    def _rest_add(self, title: str, author: str, year: int) -> Dict:
        payload = {"title": title, "author": author, "year": year}
        r = self._rest_session.post(self.REST_URL, json=payload)
        r.raise_for_status()
        return r.json()

    # --------------------------------------------------------------------- #
    # gRPC helpers (lazy channel creation)
    # --------------------------------------------------------------------- #
    def _get_grpc_stub(self):
        if self._stub is None:
            self._grpc_channel = grpc.insecure_channel(self.GRPC_ADDR)
            self._stub = book_pb2_grpc.BookCatalogStub(self._grpc_channel)
        return self._stub

    def _grpc_add(self, title: str, author: str, year: int) -> book_pb2.Book:
        req = book_pb2.AddBookRequest(title=title, author=author, year=year)
        resp = self._get_grpc_stub().AddBook(req)
        return resp.book

    # --------------------------------------------------------------------- #
    # Public API
    # --------------------------------------------------------------------- #
    def seed_rest(self, books: List[Dict]) -> List[Dict]:
        """Add books via REST. Returns the created objects."""
        return [self._rest_add(b["title"], b["author"], b["year"]) for b in books]

    def seed_grpc(self, books: List[Dict]) -> List[book_pb2.Book]:
        """Add books via gRPC. Returns the created protobuf objects."""
        return [self._grpc_add(b["title"], b["author"], b["year"]) for b in books]

    def seed_both(self, books: List[Dict]) -> None:
        """
        Seed **both** servers with the same data.
        Uses REST first (simpler) then mirrors with gRPC to guarantee
        identical DB state (both servers read/write the same `books.json`).
        """
        print("Seeding REST …")
        self.seed_rest(books)
        print("Seeding gRPC …")
        self.seed_grpc(books)
        print(f"Added {len(books)} books to both servers.")

    def close(self):
        """Close any open gRPC channel."""
        if self._grpc_channel:
            self._grpc_channel.close()


# ------------------------------------------------------------------------- #
# Convenience – run as a script
# ------------------------------------------------------------------------- #
DEFAULT_BOOKS = [
    {"title": "Clean Code", "author": "Robert C. Martin", "year": 2008},
    {"title": "The Pragmatic Programmer", "author": "Andrew Hunt", "year": 1999},
    {"title": "Design Patterns", "author": "Gang of Four", "year": 1994},
    {"title": "gRPC Up and Running", "author": "Kasun Indrasiri", "year": 2020},
]

if __name__ == "__main__":
    seeder = CatalogSeeder()
    try:
        seeder.seed_both(DEFAULT_BOOKS)
    finally:
        seeder.close()