# client/benchmark.py
import time
import json
import requests
import grpc
import sys
import os

# Add grpc_server to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'grpc_server'))

import book_pb2
import book_pb2_grpc

REST_URL = "http://localhost:5000/books"
GRPC_ADDR = "localhost:50051"

# --- Helper: Measure full round-trip size ---
def rest_add_book(title, author, year):
    payload = {"title": title, "author": author, "year": year}
    req_bytes = len(json.dumps(payload).encode('utf-8'))
    
    start = time.perf_counter()
    r = requests.post(REST_URL, json=payload)
    elapsed = (time.perf_counter() - start) * 1000
    
    resp_bytes = len(r.content)
    total_bytes = req_bytes + resp_bytes
    return elapsed, total_bytes, r.json()

def grpc_add_book(title, author, year):
    req = book_pb2.AddBookRequest(title=title, author=author, year=year)
    req_bytes = req.ByteSize()
    
    with grpc.insecure_channel(GRPC_ADDR) as channel:
        stub = book_pb2_grpc.BookCatalogStub(channel)
        start = time.perf_counter()
        resp = stub.AddBook(req)
        elapsed = (time.perf_counter() - start) * 1000
    
    resp_bytes = resp.ByteSize()
    total_bytes = req_bytes + resp_bytes
    return elapsed, total_bytes, resp.book

def rest_list():
    start = time.perf_counter()
    r = requests.get(REST_URL)
    elapsed = (time.perf_counter() - start) * 1000
    req_bytes = len(r.request.url.encode()) + len(r.request.body or b"")
    resp_bytes = len(r.content)
    total_bytes = req_bytes + resp_bytes
    return elapsed, total_bytes, r.json()

def grpc_list():
    req = book_pb2.ListBooksRequest()
    req_bytes = req.ByteSize()
    
    with grpc.insecure_channel(GRPC_ADDR) as channel:
        stub = book_pb2_grpc.BookCatalogStub(channel)
        start = time.perf_counter()
        resp = stub.ListBooks(req)
        elapsed = (time.perf_counter() - start) * 1000
    
    resp_bytes = resp.ByteSize()
    total_bytes = req_bytes + resp_bytes
    books = [{"id": b.id, "title": b.title, "author": b.author, "year": b.year} for b in resp.books]
    return elapsed, total_bytes, books

# --- OPTIONAL: seed realistic data (uncomment to enable) ---
from seeder import CatalogSeeder, DEFAULT_BOOKS
CatalogSeeder().seed_both(DEFAULT_BOOKS)
# -------------------------------------------------------

# --- Warm-up (avoid cold start) ---
def warmup():
    print("Warming up servers...")
    try:
        requests.get(REST_URL)
        with grpc.insecure_channel(GRPC_ADDR) as channel:
            stub = book_pb2_grpc.BookCatalogStub(channel)
            stub.ListBooks(book_pb2.ListBooksRequest())
    except:
        pass
    time.sleep(1)

# --- Benchmark ---
def benchmark():
    warmup()
    
    print("\n=== Adding a book ===")
    rest_lat, rest_sz, rest_book = rest_add_book("gRPC Up and Running", "Ming Shen", 2020)
    grpc_lat, grpc_sz, grpc_book = grpc_add_book("gRPC Up and Running", "Ming Shen", 2020)

    print(f"REST  -> {rest_lat:.2f} ms, total {rest_sz} bytes")
    print(f"gRPC  -> {grpc_lat:.2f} ms, total {grpc_sz} bytes")
    print(f"Speedup: {rest_lat/grpc_lat:.1f}x, Size reduction: {rest_sz/grpc_sz:.1f}x\n")

    print("=== Listing books ===")
    rest_lat, rest_sz, _ = rest_list()
    grpc_lat, grpc_sz, _ = grpc_list()

    print(f"REST list  -> {rest_lat:.2f} ms, total {rest_sz} bytes")
    print(f"gRPC list  -> {grpc_lat:.2f} ms, total {grpc_sz} bytes")
    print(f"Speedup: {rest_lat/grpc_lat:.1f}x, Size reduction: {rest_sz/grpc_sz:.1f}x")

if __name__ == "__main__":
    benchmark()