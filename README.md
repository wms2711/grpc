# gRPC vs REST – Hands-on Demo

## Start servers (in separate terminals)

```bash
# REST (Flask)
cd rest_server
python server.py

# gRPC
cd grpc_server
python server.py

# Run benchmark
cd client
python benchmark.py