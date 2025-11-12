# gRPC vs REST Performance Comparison

A hands-on demonstration comparing REST (HTTP/JSON) and gRPC (Protocol Buffers) implementations of a book catalog service, measuring latency and data transfer efficiency.

## Project Structure

```
grpc/
├── proto/              # Protocol Buffer definitions
│   └── book.proto      # Service and message schemas
├── rest_server/        # Flask REST API implementation
│   ├── server.py       # HTTP/JSON endpoints
│   └── books.json      # Shared JSON database
├── grpc_server/        # gRPC server implementation
│   ├── server.py       # RPC service implementation
│   ├── book_pb2.py     # Generated protobuf messages
│   ├── book_pb2_grpc.py # Generated service stubs
│   └── books.json      # Shared JSON database
└── client/             # Benchmarking and seeding tools
    ├── benchmark.py    # Performance comparison script
    └── seeder.py       # Data population utility
```

## Features

- **Two identical APIs**: Same operations (ListBooks, AddBook) in REST and gRPC
- **Shared storage**: Both servers use the same `books.json` for fair comparison
- **Performance metrics**: Measures latency (ms) and data size (bytes)
- **Auto-seeding**: Optional realistic data population for testing

## Prerequisites

```bash
python -m venv venv
pip install -r requirements.txt
```

Dependencies: `flask`, `grpcio`, `grpcio-tools`, `requests`

## Quick Start

### 1. Generate Protocol Buffers (if modified)

```bash
python -m grpc_tools.protoc -I proto --python_out=grpc_server --grpc_python_out=grpc_server proto/book.proto
```

### 2. Start Both Servers (in separate terminals)

```bash
# Terminal 1: REST server (port 5000)
cd rest_server
python server.py

# Terminal 2: gRPC server (port 50051)
cd grpc_server
python server.py
```

### 3. Run Benchmark

```bash
cd client
python benchmark.py
```

## Expected Results

The benchmark tests two operations:
- **AddBook**: Write operation with ~50-100 bytes payload
- **ListBooks**: Read operation, size varies with catalog size

Typical improvements with gRPC:
- **Latency**: 1.5-3x faster (binary serialization, HTTP/2)
- **Data size**: 2-4x smaller (Protocol Buffers vs JSON)

## API Reference

### REST Endpoints

```bash
# List all books
GET http://localhost:5000/books

# Add a book
POST http://localhost:5000/books
Content-Type: application/json
{"title": "Book Title", "author": "Author Name", "year": 2020}
```

### gRPC Service

```protobuf
service BookCatalog {
  rpc ListBooks(ListBooksRequest) returns (ListBooksResponse);
  rpc AddBook(AddBookRequest) returns (AddBookResponse);
}
```

## Utilities

### Data Seeder

Populate both servers with sample books:

```bash
cd client
python seeder.py
```

Or use programmatically:

```python
from seeder import CatalogSeeder, DEFAULT_BOOKS
seeder = CatalogSeeder()
seeder.seed_both(DEFAULT_BOOKS)
```

## Key Differences

| Aspect | REST | gRPC |
|--------|------|------|
| Protocol | HTTP/1.1 | HTTP/2 |
| Data format | JSON (text) | Protocol Buffers (binary) |
| Schema | Optional (OpenAPI) | Required (.proto) |
| Code generation | Manual | Automatic |
| Streaming | Limited | Built-in (unary, server, client, bidirectional) |
| Browser support | Native | Requires proxy (gRPC-Web) |

## Why gRPC is Faster

1. **Binary serialization**: Protocol Buffers are more compact than JSON
2. **HTTP/2 multiplexing**: Multiple requests over single connection
3. **Efficient parsing**: No JSON string parsing overhead
4. **Schema-first**: Strong typing eliminates runtime validation

## Use Cases

**Choose REST when:**
- Building public APIs
- Browser-first applications
- Simple CRUD operations
- Human-readable debugging is priority

**Choose gRPC when:**
- Microservice communication
- High-performance requirements
- Strong typing needed
- Streaming data (real-time features)

## License

MIT