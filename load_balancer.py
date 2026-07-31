import socket
import threading
import sys
import hashlib
import random
import time
from collections import Counter
import traceback

# Try importing optional dependencies with fallbacks
try:
    import matplotlib
    matplotlib.use('TkAgg')
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    print("WARNING: matplotlib not installed. Visualization will be limited.")
    MATPLOTLIB_AVAILABLE = False

try:
    import tkinter as tk
    from tkinter import ttk
    TKINTER_AVAILABLE = True
except ImportError:
    print("ERROR: tkinter not available. GUI cannot run.")
    TKINTER_AVAILABLE = False
    sys.exit(1)

try:
    import networkx as nx
    NETWORKX_AVAILABLE = True
except ImportError:
    print("WARNING: networkx not installed. Network visualization will be limited.")
    NETWORKX_AVAILABLE = False

class LoadBalancer:
    def __init__(self, backend_servers):
        self.backend_servers = backend_servers
        print(f"[*] Backend servers: {self.backend_servers}")
        self.current_server = 0
        self.lock = threading.Lock()
        self.request_counts = {server: 0 for server in backend_servers}
        self.connections = {server: 0 for server in backend_servers}
        self.mfu_counts = {server: 0 for server in backend_servers}  # MFU Algorithm
        self.weights = {server: random.randint(1, 5) for server in backend_servers}  # Initialize with random weights
        self.response_times = {server: random.uniform(0.1, 2.0) for server in backend_servers}  # Initialize with random response times
        self.resource_usage = {server: random.uniform(10, 80) for server in backend_servers}  # Initialize with random resource usage
        
        if not TKINTER_AVAILABLE:
            print("ERROR: tkinter not available. GUI cannot run.")
            return
            
        try:
            # Create main Tkinter window
            self.root = tk.Tk()
            self.root.title("Load Balancer Visualization")
            self.root.geometry("1000x800")
            self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
            
            # Create navigation bar
            self.nav_frame = tk.Frame(self.root, bg='lightgray')
            self.nav_frame.pack(side=tk.TOP, fill=tk.X)
            
            # Create navigation buttons
            self.btn_distribution = tk.Button(
                self.nav_frame, text="Request Distribution", 
                command=lambda: self.show_frame("distribution")
            )
            self.btn_distribution.pack(side=tk.LEFT, padx=10, pady=5)
            
            self.btn_topology = tk.Button(
                self.nav_frame, text="Network Topology", 
                command=lambda: self.show_frame("topology")
            )
            self.btn_topology.pack(side=tk.LEFT, padx=10, pady=5)
            
            self.btn_processing = tk.Button(
                self.nav_frame, text="Request Processing", 
                command=lambda: self.show_frame("processing")
            )
            self.btn_processing.pack(side=tk.LEFT, padx=10, pady=5)
            
            # Add status bar
            self.status_var = tk.StringVar(value="Ready")
            self.status_bar = tk.Label(self.root, textvariable=self.status_var, 
                                      bd=1, relief=tk.SUNKEN, anchor=tk.W)
            self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
            
            # Create container for frames
            self.container = tk.Frame(self.root)
            self.container.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
            
            # Create frames for each visualization
            self.frames = {}
            
            if MATPLOTLIB_AVAILABLE:
                # Distribution frame
                self.frames["distribution"] = tk.Frame(self.container)
                self.fig_dist, self.ax_dist = plt.subplots(figsize=(10, 6))
                self.canvas_dist = FigureCanvasTkAgg(self.fig_dist, self.frames["distribution"])
                self.canvas_dist.get_tk_widget().pack(fill=tk.BOTH, expand=True)
                
                # Topology frame
                self.frames["topology"] = tk.Frame(self.container)
                self.fig_topo, self.ax_topo = plt.subplots(figsize=(10, 6))
                self.canvas_topo = FigureCanvasTkAgg(self.fig_topo, self.frames["topology"])
                self.canvas_topo.get_tk_widget().pack(fill=tk.BOTH, expand=True)
                
                # Processing frame
                self.frames["processing"] = tk.Frame(self.container)
                self.fig_proc, self.ax_proc = plt.subplots(figsize=(10, 6), nrows=6, ncols=1, squeeze=False)
                self.ax_proc = self.ax_proc.flatten()  # Convert to 1D array for easier indexing
                self.canvas_proc = FigureCanvasTkAgg(self.fig_proc, self.frames["processing"])
                self.canvas_proc.get_tk_widget().pack(fill=tk.BOTH, expand=True)
            else:
                # Simple text-based frames when matplotlib is not available
                for frame_name in ["distribution", "topology", "processing"]:
                    self.frames[frame_name] = tk.Frame(self.container)
                    txt = tk.Text(self.frames[frame_name])
                    txt.insert(tk.END, f"Matplotlib not available.\nVisualization for {frame_name} cannot be shown.")
                    txt.pack(fill=tk.BOTH, expand=True)
            
            # Show default frame
            self.show_frame("distribution")
            
            # For controlling update intervals
            self.last_topology_update = 0
            self.last_processing_update = 0
            self.last_distribution_update = 0
            
            # Start a thread to periodically update simulated resource usage and response times
            self.update_metrics_thread = threading.Thread(target=self.update_server_metrics)
            self.update_metrics_thread.daemon = True
            self.update_metrics_thread.start()
            
            print("[*] GUI setup complete")
        except Exception as e:
            print(f"ERROR in GUI setup: {e}")
            traceback.print_exc()
            if hasattr(self, 'root'):
                self.root.quit()

    def on_closing(self):
        """Handle window close event"""
        print("Closing Load Balancer GUI")
        if hasattr(self, 'root'):
            self.root.quit()
            self.root.destroy()

    def update_server_metrics(self):
        """Periodically update simulated server metrics"""
        while True:
            try:
                with self.lock:
                    for server in self.backend_servers:
                        # Simulate changing response times (between 0.1 and 3.0 seconds)
                        self.response_times[server] = min(3.0, max(0.1, self.response_times[server] + random.uniform(-0.3, 0.3)))
                        
                        # Simulate changing resource usage (between 10% and 90%)
                        self.resource_usage[server] = min(90, max(10, self.resource_usage[server] + random.uniform(-5, 5)))
                time.sleep(2)  # Update every 2 seconds
            except Exception as e:
                print(f"Error in update_server_metrics: {e}")
                time.sleep(5)  # Back off on error

    def show_frame(self, frame_name):
        """Show the selected frame and hide others"""
        try:
            # Hide all frames
            for frame in self.frames.values():
                frame.pack_forget()
            # Show selected frame
            self.frames[frame_name].pack(fill=tk.BOTH, expand=True)
            self.status_var.set(f"Viewing: {frame_name}")
        except Exception as e:
            print(f"Error showing frame {frame_name}: {e}")

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
            # If no requests yet, use round robin
            if all(count == 0 for count in self.mfu_counts.values()):
                return self.get_server_round_robin()
                
            server = max(self.mfu_counts, key=self.mfu_counts.get)
            self.mfu_counts[server] += 1
            self.request_counts[server] += 1
            return server

    def get_server_weighted_round_robin(self):
        """Weighted Round Robin: Assigns requests based on server weights."""
        with self.lock:
            total_weight = sum(self.weights.values())
            if total_weight == 0:  # Safety check
                return self.get_server_round_robin()
                
            point = random.randint(0, total_weight - 1)
            for server, weight in self.weights.items():
                if point < weight:
                    self.request_counts[server] += 1
                    return server
                point -= weight
            # Fallback to round robin if something goes wrong
            return self.get_server_round_robin()

    def get_server_least_response_time(self):
        """Least Response Time: Routes to server with fastest response time."""
        with self.lock:
            server = min(self.backend_servers, key=lambda s: self.response_times[s])
            self.request_counts[server] += 1
            return server

    def get_server_resource_based(self):
        """Resource-Based: Routes based on server resource usage."""
        with self.lock:
            server = min(self.backend_servers, key=lambda s: self.resource_usage[s])
            self.request_counts[server] += 1
            return server

    def get_server_random(self):
        """Random: Randomly selects a server from the pool."""
        with self.lock:
            server = random.choice(self.backend_servers)
            self.request_counts[server] += 1
            return server

    def get_server_voting(self, client_ip):
        """Voting Algorithm: Takes results from all algorithms and selects the majority-voted server."""
        # Save the initial state of request counts and connections to avoid side effects
        original_req_counts = self.request_counts.copy()
        original_connections = self.connections.copy()
        original_mfu_counts = self.mfu_counts.copy()
        
        # Get server recommendations from different algorithms without incrementing counters
        round_robin_server = self.backend_servers[self.current_server]
        
        least_conn_server = min(self.backend_servers, key=lambda s: self.connections[s])
        
        ip_hash = int(hashlib.sha256(client_ip.encode()).hexdigest(), 16)
        ip_hashing_server = self.backend_servers[ip_hash % len(self.backend_servers)]
        
        # For most frequent, safely get the server with most requests
        if all(count == 0 for count in self.mfu_counts.values()):
            most_frequent_server = round_robin_server
        else:
            most_frequent_server = max(self.mfu_counts, key=self.mfu_counts.get)
        
        # Restore original counters
        self.request_counts = original_req_counts
        self.connections = original_connections
        self.mfu_counts = original_mfu_counts
        
        votes = [round_robin_server, least_conn_server, ip_hashing_server, most_frequent_server]
        vote_count = Counter(votes)
        top_servers = vote_count.most_common(2)
        
        # Add some randomness to prevent always choosing the same server
        if len(vote_count) == 1 or (vote_count.most_common(1)[0][1] > 2):
            if random.random() < 0.2:
                majority_server = random.choice(self.backend_servers)
                print(f"Forcing distribution: {majority_server} (original votes: {vote_count})")
                return majority_server
                
        if len(top_servers) > 1 and top_servers[0][1] == top_servers[1][1]:
            majority_server = min(top_servers, key=lambda x: self.connections[x[0]])[0]
        else:
            majority_server = top_servers[0][0]
        
        # Now increment the request count for the selected server
        with self.lock:
            self.request_counts[majority_server] += 1
            
        print(f"Voting results: {vote_count} -> Selected: {majority_server}")
        return majority_server

    def get_server_specified_ip_hash(self, client_ip, specified_server=None):
        """IP Hashing with server specification: Routes to specified server or uses IP hash."""
        if specified_server and specified_server in self.backend_servers:
            with self.lock:
                self.request_counts[specified_server] += 1
                return specified_server
        else:
            return self.get_server_ip_hashing(client_ip)

    def update_distribution_plot(self):
        """Update the real-time request distribution bar chart."""
        if not MATPLOTLIB_AVAILABLE:
            return
            
        try:
            servers = [f"{server[1]}" for server in self.backend_servers]
            counts = [self.request_counts[server] for server in self.backend_servers]
            
            self.ax_dist.clear()
            bars = self.ax_dist.bar(servers, counts, color=['#4287f5', '#42f5a7', '#f542a1', '#f5d442'])
            
            for bar in bars:
                height = bar.get_height()
                self.ax_dist.text(bar.get_x() + bar.get_width() / 2.0, height + 0.1,
                                  f'{height}', ha='center', va='bottom', fontweight='bold')
                             
            self.ax_dist.set_xlabel('Backend Server Port', fontsize=12, fontweight='bold')
            self.ax_dist.set_ylabel('Number of Requests', fontsize=12, fontweight='bold')
            self.ax_dist.set_title('Real-Time Request Distribution', fontsize=14, fontweight='bold')
            self.ax_dist.grid(True, linestyle='--', alpha=0.7)
            
            self.canvas_dist.draw()
        except Exception as e:
            print(f"Error updating distribution plot: {e}")

    def update_topology_plot(self):
        """Update the network topology visualization."""
        if not MATPLOTLIB_AVAILABLE:
            return
            
        try:
            self.ax_topo.clear()
            
            if not NETWORKX_AVAILABLE:
                self.ax_topo.text(
                    0.5, 0.5,
                    "networkx is not installed. Skipping topology visualization.",
                    ha='center', va='center', fontsize=12
                )
                self.canvas_topo.draw()
                return
                
            G = nx.DiGraph()
            G.add_node("Load Balancer", type="balancer")
            
            for server in self.backend_servers:
                server_label = f"Server {server[1]}"
                G.add_node(server_label, type="server")
                G.add_edge("Load Balancer", server_label, weight=self.request_counts[server])
                
            for i in range(5):
                client_name = f"Client {i+1}"
                G.add_node(client_name, type="client")
                G.add_edge(client_name, "Load Balancer", weight=1)
                
            pos = nx.spring_layout(G)
            node_colors = {'client': '#ff9999', 'balancer': '#66b3ff', 'server': '#99ff99'}
            
            for node_type, color in node_colors.items():
                nx.draw_networkx_nodes(
                    G, pos,
                    nodelist=[n for n, d in G.nodes(data=True) if d.get('type') == node_type],
                    node_color=color,
                    node_size=700,
                    alpha=0.8,
                    ax=self.ax_topo
                )
                
            edge_widths = [G[u][v]['weight'] * 0.5 for u, v in G.edges()]
            nx.draw_networkx_edges(
                G, pos, width=edge_widths, alpha=0.7,
                edge_color='gray', arrowsize=15, ax=self.ax_topo
            )
            nx.draw_networkx_labels(G, pos, font_size=10, font_weight='bold', ax=self.ax_topo)
            
            self.ax_topo.set_title("Network Topology and Request Flow", fontsize=16, fontweight='bold')
            self.ax_topo.axis('off')
            
            self.canvas_topo.draw()
        except Exception as e:
            print(f"Error updating topology plot: {e}")

    def update_processing_plot(self):
        """Update the request processing visualization."""
        if not MATPLOTLIB_AVAILABLE:
            return
            
        try:
            algorithms = ["round_robin", "least_connections", "ip_hashing",
                          "most_frequent", "weighted_round_robin", "voting"]
                         
            # Generate sample distribution data
            server_distribution = {}
            for algo in algorithms:
                server_distribution[algo] = {}
                for server in self.backend_servers:
                    if algo == "round_robin":
                        server_distribution[algo][f"Server {server[1]}"] = 100 / len(self.backend_servers)
                    elif algo == "ip_hashing":
                        server_distribution[algo][f"Server {server[1]}"] = random.randint(10, 40)
                    else:
                        server_distribution[algo][f"Server {server[1]}"] = random.randint(5, 30)
            
            # Clear all subplots
            for ax in self.ax_proc:
                ax.clear()
                
            # Update each subplot with algorithm data
            for i, algo in enumerate(algorithms):
                if i >= len(self.ax_proc):  # Safety check
                    break
                    
                servers = list(server_distribution[algo].keys())
                values = list(server_distribution[algo].values())
                
                bars = self.ax_proc[i].barh(servers, values, color=['#4287f5', '#42f5a7', '#f542a1'])
                self.ax_proc[i].set_title(f"{algo.replace('_', ' ').title()}", fontsize=12)
                self.ax_proc[i].set_xlabel("Percentage of Requests", fontsize=10)
                self.ax_proc[i].grid(True, linestyle='--', alpha=0.7)
                
                for bar in bars:
                    width = bar.get_width()
                    self.ax_proc[i].text(
                        width + 1, bar.get_y() + bar.get_height() / 2.0,
                        f'{width:.1f}%', ha='left', va='center', fontweight='bold'
                    )
                                   
            self.fig_proc.tight_layout()
            self.canvas_proc.draw()
        except Exception as e:
            print(f"Error updating processing plot: {e}")

    def forward_request(self, client_socket, server_address):
        """Forwards client requests to the selected backend server."""
        try:
            with self.lock:
                self.connections[server_address] += 1
                
            server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            server_socket.connect(server_address)
            request = client_socket.recv(4096)
            server_socket.send(request)
            response = server_socket.recv(4096)
            client_socket.send(response)
        except Exception as e:
            print(f"Error forwarding request: {e}")
        finally:
            try:
                server_socket.close()
            except:
                pass
            try:
                client_socket.close()
            except:
                pass
            with self.lock:
                self.connections[server_address] -= 1

    def handle_client(self, client_socket, algorithm, client_ip):
        """Handles incoming client requests and routes them using the chosen algorithm."""
        try:
            # Check if we need to look for a specified server
            specified_server = None
            
            # Get request headers if needed for specific algorithms
            if algorithm == "specified_ip_hash":
                try:
                    request_data = client_socket.recv(4096, socket.MSG_PEEK)
                    headers = request_data.decode('utf-8', errors='ignore').split('\r\n')
                    for header in headers:
                        if header.startswith('X-Specified-Server:'):
                            specified_server_port = int(header.split(':')[1].strip())
                            for server in self.backend_servers:
                                if server[1] == specified_server_port:
                                    specified_server = server
                                    break
                except Exception as e:
                    print(f"Error parsing headers: {e}")
            
            # Select server based on algorithm
            if algorithm == "round_robin":
                server_address = self.get_server_round_robin()
            elif algorithm == "least_connections":
                server_address = self.get_server_least_connections()
            elif algorithm == "ip_hashing":
                server_address = self.get_server_ip_hashing(client_ip)
            elif algorithm == "most_frequent":
                server_address = self.get_server_most_frequent()
            elif algorithm == "weighted_round_robin":
                server_address = self.get_server_weighted_round_robin()
            elif algorithm == "least_response_time":
                server_address = self.get_server_least_response_time()
            elif algorithm == "resource_based":
                server_address = self.get_server_resource_based()
            elif algorithm == "random":
                server_address = self.get_server_random()
            elif algorithm == "specified_ip_hash":
                server_address = self.get_server_specified_ip_hash(client_ip, specified_server)
            elif algorithm == "voting":
                server_address = self.get_server_voting(client_ip)
            else:
                # Default to round robin if algorithm not recognized
                print(f"Unrecognized algorithm: {algorithm}, using round_robin")
                server_address = self.get_server_round_robin()
                
            print(f"Selected server {server_address} using {algorithm} algorithm")
            self.forward_request(client_socket, server_address)
        except Exception as e:
            print(f"Error handling client: {e}")
            try:
                client_socket.close()
            except:
                pass

    def accept_clients(self, server_socket, algorithm):
        """Accepts incoming client connections in a separate thread."""
        while True:
            try:
                client_socket, addr = server_socket.accept()
                client_ip = addr[0]
                print(f"[*] Accepted connection from {addr}")
                client_handler = threading.Thread(
                    target=self.handle_client,
                    args=(client_socket, algorithm, client_ip)
                )
                client_handler.daemon = True
                client_handler.start()
            except Exception as e:
                print(f"Error accepting client: {e}")
                break

    def update_visualizations(self):
        """Update all visualizations periodically."""
        try:
            current_time = time.time()
            
            # Update status
            self.status_var.set(f"Status: Running - Requests: {sum(self.request_counts.values())}")
            
            # Update distribution plot
            if current_time - self.last_distribution_update > 1:
                self.update_distribution_plot()
                self.last_distribution_update = current_time
                
            # Update topology plot
            if current_time - self.last_topology_update > 10:
                self.update_topology_plot()
                self.last_topology_update = current_time
                
            # Update processing plot
            if current_time - self.last_processing_update > 10:
                self.update_processing_plot()
                self.last_processing_update = current_time

            self.root.after(1000, self.update_visualizations)
        except Exception as e:
            print(f"Error in update_visualizations: {e}")
            # Try to re-schedule even on error
            if hasattr(self, 'root') and self.root.winfo_exists():
                self.root.after(5000, self.update_visualizations)
        
    def start(self, host="localhost", port=8001, algorithm="voting"):
        """Starts the load balancer and begins accepting client requests."""
        print(f"[*] Load Balancer started on {host}:{port} using {algorithm} algorithm")
        
        try:
            server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            server_socket.bind((host, port))
            server_socket.listen(5)

            # Start the server loop in a separate thread.
            server_thread = threading.Thread(target=self.accept_clients, args=(server_socket, algorithm))
            server_thread.daemon = True
            server_thread.start()
            
            # Start visualization updates if we have a GUI
            if hasattr(self, 'root') and TKINTER_AVAILABLE:
                self.root.after(1000, self.update_visualizations)
                print("[*] Starting GUI main loop")
                self.root.mainloop()
                print("[*] GUI main loop ended")
        except Exception as e:
            print(f"Error starting load balancer: {e}")
            traceback.print_exc()

if __name__ == "__main__":
    try:
        backend_servers = [("localhost", int(arg)) for arg in sys.argv[1:-1]]
        algorithm = sys.argv[-1]
        valid_algorithms = [
            "round_robin", "least_connections", "ip_hashing", "most_frequent",
            "weighted_round_robin", "least_response_time", "resource_based",
            "voting", "random", "specified_ip_hash"
        ]
        
        # Validate the algorithm
        if algorithm not in valid_algorithms:
            print(f"[!] Invalid algorithm '{algorithm}' specified. Using default: voting")
            algorithm = "voting"
        else:
            print(f"[*] Using algorithm: {algorithm}")

        print("[*] Initializing Load Balancer...")
        lb = LoadBalancer(backend_servers)
        print("[*] Starting Load Balancer...")
        lb.start(algorithm=algorithm)  # Start the socket server
    except Exception as e:
        print(f"Fatal error in main: {e}")
        traceback.print_exc()
