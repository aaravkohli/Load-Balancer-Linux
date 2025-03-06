import sys
import socket
import asyncio
import random

class BackendServer:
    def __init__(self, host="localhost", port=9001):
        self.host = host
        self.port = port

    async def handle_client(self, reader, writer):
        request = await reader.read(4096)
        print(f"[*] Received request on {self.port}")

        await asyncio.sleep(random.randint(1, 5))  # Simulate processing delay

        response = f"HTTP/1.1 200 OK\n\nHello from backend server {self.port}"
        writer.write(response.encode())
        await writer.drain()
        writer.close()
        await writer.wait_closed()

    async def start(self):
        server = await asyncio.start_server(self.handle_client, self.host, self.port)
        addr = server.sockets[0].getsockname()
        print(f"[*] Backend Server started on {addr}")

        async with server:
            await server.serve_forever()

if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 9001
    server = BackendServer(port=port)
    asyncio.run(server.start())

