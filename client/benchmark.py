# client/benchmark.py
"""
Benchmark Script: REST vs gRPC Performance Comparison

This script compares the performance and data transfer efficiency between 
REST (HTTP/JSON) and gRPC (Protocol Buffers) implementations for a book catalog service.

Metrics measured:
- Latency: Time taken for round-trip requests (in milliseconds)
- Data size: Total bytes transferred (request + response)

The script tests two operations:
1. Adding a book (write operation)
2. Listing all books (read operation)
"""

import time
import json
import requests
import grpc
import sys
import os

# Add grpc_server to path to import generated Protocol Buffer modules
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'grpc_server'))

import book_pb2
import book_pb2_grpc

# Server endpoints for REST and gRPC services
REST_URL = "http://localhost:5000/books"
GRPC_ADDR = "localhost:50051"

# --- Helper Functions: Measure full round-trip latency and data size ---

def rest_add_book(title, author, year):
    """
    Add a book via REST API and measure performance.
    
    Args:
        title (str): Book title
        author (str): Book author
        year (int): Publication year
    
    Returns:
        tuple: (latency_ms, total_bytes, response_json)
            - latency_ms: Round-trip time in milliseconds
            - total_bytes: Request size + response size in bytes
            - response_json: Server response as JSON dict
    """
    # Prepare JSON payload and calculate request size
    payload = {"title": title, "author": author, "year": year}
    req_bytes = len(json.dumps(payload).encode('utf-8'))
    
    # Send POST request and measure time
    start = time.perf_counter()
    r = requests.post(REST_URL, json=payload)
    elapsed = (time.perf_counter() - start) * 1000  # Convert to milliseconds
    
    # Calculate response size and total bytes transferred
    resp_bytes = len(r.content)
    total_bytes = req_bytes + resp_bytes
    return elapsed, total_bytes, r.json()

def grpc_add_book(title, author, year):
    """
    Add a book via gRPC and measure performance.
    
    Args:
        title (str): Book title
        author (str): Book author
        year (int): Publication year
    
    Returns:
        tuple: (latency_ms, total_bytes, book_object)
            - latency_ms: Round-trip time in milliseconds
            - total_bytes: Request size + response size in bytes
            - book_object: Server response as Protocol Buffer Book object
    """
    # Create Protocol Buffer request message and calculate its serialized size
    req = book_pb2.AddBookRequest(title=title, author=author, year=year)
    req_bytes = req.ByteSize()
    
    # Establish gRPC channel, send request, and measure time
    with grpc.insecure_channel(GRPC_ADDR) as channel:
        stub = book_pb2_grpc.BookCatalogStub(channel)
        start = time.perf_counter()
        resp = stub.AddBook(req)
        elapsed = (time.perf_counter() - start) * 1000  # Convert to milliseconds
    
    # Calculate response size and total bytes transferred
    resp_bytes = resp.ByteSize()
    total_bytes = req_bytes + resp_bytes
    return elapsed, total_bytes, resp.book

def rest_list():
    """
    Retrieve all books via REST API and measure performance.
    
    Returns:
        tuple: (latency_ms, total_bytes, books_list)
            - latency_ms: Round-trip time in milliseconds
            - total_bytes: Request size + response size in bytes
            - books_list: List of books as JSON array
    """
    # Send GET request and measure time
    start = time.perf_counter()
    r = requests.get(REST_URL)
    elapsed = (time.perf_counter() - start) * 1000  # Convert to milliseconds
    
    # Calculate request size (URL + body) and response size
    req_bytes = len(r.request.url.encode()) + len(r.request.body or b"")
    resp_bytes = len(r.content)
    total_bytes = req_bytes + resp_bytes
    return elapsed, total_bytes, r.json()

def grpc_list():
    """
    Retrieve all books via gRPC and measure performance.
    
    Returns:
        tuple: (latency_ms, total_bytes, books_list)
            - latency_ms: Round-trip time in milliseconds
            - total_bytes: Request size + response size in bytes
            - books_list: List of books as dicts (converted from protobuf)
    """
    # Create empty Protocol Buffer request (no parameters needed for list)
    req = book_pb2.ListBooksRequest()
    req_bytes = req.ByteSize()
    
    # Establish gRPC channel, send request, and measure time
    with grpc.insecure_channel(GRPC_ADDR) as channel:
        stub = book_pb2_grpc.BookCatalogStub(channel)
        start = time.perf_counter()
        resp = stub.ListBooks(req)
        elapsed = (time.perf_counter() - start) * 1000  # Convert to milliseconds
    
    # Calculate response size and total bytes transferred
    resp_bytes = resp.ByteSize()
    total_bytes = req_bytes + resp_bytes
    
    # Convert Protocol Buffer Book objects to Python dicts for easier comparison
    books = [{"id": b.id, "title": b.title, "author": b.author, "year": b.year} for b in resp.books]
    return elapsed, total_bytes, books

# --- OPTIONAL: seed realistic data (uncomment to enable) ---
# Import seeder module to populate both servers with sample books
# This ensures consistent data for benchmarking across multiple runs
from seeder import CatalogSeeder, DEFAULT_BOOKS
CatalogSeeder().seed_both(DEFAULT_BOOKS)
# -------------------------------------------------------

# --- Warm-up (avoid cold start) ---
def warmup():
    """
    Warm up both REST and gRPC servers before benchmarking.
    
    This prevents cold start effects from skewing the first measurement.
    Makes a simple request to each server to initialize connections,
    load code, and prepare caches.
    """
    print("Warming up servers...")
    try:
        # Warm up REST server
        requests.get(REST_URL)
        
        # Warm up gRPC server
        with grpc.insecure_channel(GRPC_ADDR) as channel:
            stub = book_pb2_grpc.BookCatalogStub(channel)
            stub.ListBooks(book_pb2.ListBooksRequest())
    except:
        pass  # Ignore errors during warmup
    time.sleep(1)  # Brief pause to ensure servers are ready

# --- Benchmark ---
def benchmark():
    """
    Main benchmark function that compares REST vs gRPC performance.
    
    Tests two key operations:
    1. Adding a new book (write operation)
    2. Listing all books (read operation)
    
    For each operation, measures and compares:
    - Latency (milliseconds)
    - Data transfer size (bytes)
    - Performance improvements (speedup and size reduction ratios)
    """
    # Warm up servers to avoid cold start bias
    warmup()
    
    # --- Test 1: Add Book Operation ---
    print("\n=== Adding a book ===")
    # Execute add operation via both REST and gRPC
    rest_lat, rest_sz, rest_book = rest_add_book("gRPC Up and Running", "Ming Shen", 2020)
    grpc_lat, grpc_sz, grpc_book = grpc_add_book("gRPC Up and Running", "Ming Shen", 2020)

    # Display results with latency and size metrics
    print(f"REST  -> {rest_lat:.2f} ms, total {rest_sz} bytes")
    print(f"gRPC  -> {grpc_lat:.2f} ms, total {grpc_sz} bytes")
    # Calculate and display performance improvements
    print(f"Speedup: {rest_lat/grpc_lat:.1f}x, Size reduction: {rest_sz/grpc_sz:.1f}x\n")

    # --- Test 2: List Books Operation ---
    print("=== Listing books ===")
    # Execute list operation via both REST and gRPC
    rest_lat, rest_sz, _ = rest_list()
    grpc_lat, grpc_sz, _ = grpc_list()

    # Display results with latency and size metrics
    print(f"REST list  -> {rest_lat:.2f} ms, total {rest_sz} bytes")
    print(f"gRPC list  -> {grpc_lat:.2f} ms, total {grpc_sz} bytes")
    # Calculate and display performance improvements
    print(f"Speedup: {rest_lat/grpc_lat:.1f}x, Size reduction: {rest_sz/grpc_sz:.1f}x")

if __name__ == "__main__":
    benchmark()