import sys
import socket
import asyncio
import random
import psutil
import signal

class BackendServer:
    def __init__(self, host="localhost", port=9001):
        self.host = host
        self.port = port
        self.response_time = 0
        self.resource_usage = 0
        self.should_run = True
        self.server = None

    async def handle_client(self, reader, writer):
        start_time = asyncio.get_event_loop().time()
        request = await reader.read(4096)
        print(f"[*] Received request on {self.port}")

        await asyncio.sleep(random.randint(1, 5))  # Simulate processing delay

        response = f"HTTP/1.1 200 OK\n\nHello from backend server {self.port}"
        writer.write(response.encode())
        await writer.drain()

        end_time = asyncio.get_event_loop().time()
        self.response_time = end_time - start_time

        writer.close()
        await writer.wait_closed()

    async def monitor_resources(self):
        while self.should_run:
            cpu_usage = psutil.cpu_percent()
            memory_usage = psutil.virtual_memory().percent
            self.resource_usage = (cpu_usage + memory_usage) / 2
            await asyncio.sleep(5)

    async def start(self):
        self.server = await asyncio.start_server(self.handle_client, self.host, self.port)
        resource_monitor = asyncio.create_task(self.monitor_resources())

        addr = self.server.sockets[0].getsockname()
        print(f"[*] Backend Server started on {addr}")

        async with self.server:
            await self.server.serve_forever()

    def shutdown(self):
        print(f"[!] Shutting down backend server on port {self.port}")
        self.should_run = False
        if self.server:
            self.server.close()

if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 9001
    server = BackendServer(port=port)

    loop = asyncio.get_event_loop()

    # Register signal handlers for graceful shutdown
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, server.shutdown)

    try:
        loop.run_until_complete(server.start())
    except (KeyboardInterrupt, SystemExit):
        pass
    finally:
        print("[*] Backend server cleanup complete.")
        loop.run_until_complete(loop.shutdown_asyncgens())
        loop.close()
