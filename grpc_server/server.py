# grpc_server/server.py
import grpc
import json
import os
from concurrent import futures

import book_pb2
import book_pb2_grpc

DB_PATH = os.path.join(os.path.dirname(__file__), "books.json")

def load_books():
    if not os.path.exists(DB_PATH):
        return []
    with open(DB_PATH, "r") as f:
        return json.load(f)

def save_books(books):
    with open(DB_PATH, "w") as f:
        json.dump(books, f, indent=2)

class BookCatalogServicer(book_pb2_grpc.BookCatalogServicer):
    def ListBooks(self, request, context):
        books = load_books()
        pb_books = [
            book_pb2.Book(id=b["id"], title=b["title"], author=b["author"], year=b["year"])
            for b in books
        ]
        return book_pb2.ListBooksResponse(books=pb_books)

    def AddBook(self, request, context):
        books = load_books()
        new_id = max((b["id"] for b in books), default=0) + 1
        book = {
            "id": new_id,
            "title": request.title,
            "author": request.author,
            "year": request.year
        }
        books.append(book)
        save_books(books)
        return book_pb2.AddBookResponse(
            book=book_pb2.Book(id=book["id"], title=book["title"],
                               author=book["author"], year=book["year"])
        )

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    book_pb2_grpc.add_BookCatalogServicer_to_server(BookCatalogServicer(), server)
    server.add_insecure_port('[::]:50051')
    server.start()
    print("gRPC server running on port 50051")
    server.wait_for_termination()

if __name__ == '__main__':
    serve()