# rest_server/server.py
from flask import Flask, jsonify, request
import json
import os

app = Flask(__name__)
DB_PATH = os.path.join(os.path.dirname(__file__), "books.json")

def load_books():
    if not os.path.exists(DB_PATH):
        return []
    with open(DB_PATH, "r") as f:
        return json.load(f)

def save_books(books):
    with open(DB_PATH, "w") as f:
        json.dump(books, f, indent=2)

@app.route("/books", methods=["GET"])
def list_books():
    return jsonify(load_books())

@app.route("/books", methods=["POST"])
def add_book():
    data = request.get_json()
    books = load_books()
    new_id = max((b["id"] for b in books), default=0) + 1
    book = {
        "id": new_id,
        "title": data["title"],
        "author": data["author"],
        "year": data["year"]
    }
    books.append(book)
    save_books(books)
    return jsonify(book), 201

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)