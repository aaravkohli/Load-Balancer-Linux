import socket
import threading
import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
import sys
import hashlib
from collections import Counter

class LoadBalancer:
    def __init__(self, backend_servers):
        self.backend_servers = backend_servers
        print(f"[*] Backend servers: {self.backend_servers}")
        self.current_server = 0
        self.lock = threading.Lock()
        self.request_counts = {server: 0 for server in backend_servers}
        self.connections = {server: 0 for server in backend_servers}
        self.mfu_counts = {server: 0 for server in backend_servers}  # MFU Algorithm
        self.fig, self.ax = plt.subplots()
        self.ax.set_xlabel('Backend Server Port')
        self.ax.set_ylabel('Number of Requests')
        self.ax.set_title('Real-Time Request Distribution')
        plt.ion()

    def get_server_round_robin(self):
        """Round Robin: Assigns requests cyclically."""
        with self.lock:
            server = self.backend_servers[self.current_server]
            self.current_server = (self.current_server + 1) % len(self.backend_servers)
            self.request_counts[server] += 1
        return server

    def get_server_least_connections(self):
        """Least Connections: Assigns request to the server with the fewest connections."""
        with self.lock:
            server = min(self.backend_servers, key=lambda s: self.connections[s])
            self.connections[server] += 1
            self.request_counts[server] += 1
        return server

    def get_server_ip_hashing(self, client_ip):
        """IP Hashing: Maps requests to servers based on client IP."""
        ip_hash = int(hashlib.sha256(client_ip.encode()).hexdigest(), 16)
        index = ip_hash % len(self.backend_servers)
        with self.lock:
            server = self.backend_servers[index]
            self.request_counts[server] += 1
        return server

    def get_server_most_frequent(self):
        """Most Frequently Used (MFU): Picks the server that has handled the most requests so far."""
        with self.lock:
            server = max(self.mfu_counts, key=self.mfu_counts.get)
            self.mfu_counts[server] += 1
            self.request_counts[server] += 1
        return server

    def get_server_voting(self, client_ip):
        """Voting Algorithm: Takes results from all algorithms and selects the majority-voted server."""
        round_robin_server = self.get_server_round_robin()
        least_conn_server = self.get_server_least_connections()
        ip_hashing_server = self.get_server_ip_hashing(client_ip)
        most_frequent_server = self.get_server_most_frequent()

        # Collect votes from all algorithms
        votes = [round_robin_server, least_conn_server, ip_hashing_server, most_frequent_server]
        vote_count = Counter(votes)

        # Get the server with the highest votes
        majority_server = vote_count.most_common(1)[0][0]

        # Tiebreaker: Use Least Connections
        if len(vote_count) > 1 and vote_count.most_common(2)[0][1] == vote_count.most_common(2)[1][1]:
            majority_server = self.get_server_least_connections()

        print(f"Voting results: {vote_count} -> Selected: {majority_server}")

        return majority_server

    def update_plot(self):
        """Update the real-time request distribution graph."""
        servers = [f"{server[1]}" for server in self.backend_servers]
        counts = [self.request_counts[server] for server in self.backend_servers]
        self.ax.clear()
        self.ax.bar(servers, counts, color='blue')
        self.ax.set_xlabel('Backend Server Port')
        self.ax.set_ylabel('Number of Requests')
        self.ax.set_title('Real-Time Request Distribution')
        plt.draw()
        plt.pause(0.1)

    def forward_request(self, client_socket, server_address):
        """Forwards client requests to the selected backend server."""
        try:
            server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            server_socket.connect(server_address)

            request = client_socket.recv(4096)
            server_socket.send(request)

            response = server_socket.recv(4096)
            client_socket.send(response)
        finally:
            server_socket.close()
            client_socket.close()
            with self.lock:
                self.connections[server_address] -= 1

    def handle_client(self, client_socket, algorithm, client_ip):
        """Handles incoming client requests and routes them using the chosen algorithm."""
        if algorithm == "round_robin":
            server_address = self.get_server_round_robin()
        elif algorithm == "least_connections":
            server_address = self.get_server_least_connections()
        elif algorithm == "ip_hashing":
            server_address = self.get_server_ip_hashing(client_ip)
        elif algorithm == "most_frequent":
            server_address = self.get_server_most_frequent()
        elif algorithm == "voting":
            server_address = self.get_server_voting(client_ip)
        else:
            server_address = self.get_server_voting(client_ip)  # Default to voting

        self.forward_request(client_socket, server_address)

    def start(self, host="localhost", port=8001, algorithm="voting"):
        """Starts the load balancer and listens for incoming client requests."""
        print(f"[*] Load Balancer started on {host}:{port} using {algorithm} algorithm")
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.bind((host, port))
        server_socket.listen(5)

        while True:
            client_socket, addr = server_socket.accept()
            client_ip = addr[0]
            print(f"[*] Accepted connection from {addr}")

            client_handler = threading.Thread(
                target=self.handle_client,
                args=(client_socket, algorithm, client_ip)
            )
            client_handler.start()
            self.update_plot()

if __name__ == "__main__":
    backend_servers = []
    for arg in sys.argv[1:-1]:  
        backend_servers.append(("localhost", int(arg)))
    algorithm = sys.argv[-1]
    if algorithm not in ["round_robin", "least_connections", "ip_hashing", "most_frequent", "voting"]:
        print("[!] Invalid algorithm specified. Using default: voting")
        algorithm = "voting"

    lb = LoadBalancer(backend_servers)
    lb.start(algorithm=algorithm)

