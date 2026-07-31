import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import subprocess
import os
import signal

class LoadBalancerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Load Balancer Controller")
        self.processes = {}
        self.backend_ports = []

        # Algorithm mapping to handle naming inconsistencies
        self.ALGORITHM_MAP = {
            "least_connection": "least_connections",
            "ip_hash": "ip_hashing",
            "mfu": "most_frequent"
        }

        self.setup_gui()

    def setup_gui(self):
        notebook = ttk.Notebook(self.root)
        notebook.pack(fill='both', expand=True)

        self.setup_servers_tab(notebook)
        self.setup_load_balancer_tab(notebook)
        self.setup_client_tab(notebook)

        help_button = ttk.Button(self.root, text="Help", command=self.show_help)
        help_button.pack(side=tk.BOTTOM, pady=5)

    def setup_servers_tab(self, notebook):
        server_tab = ttk.Frame(notebook)
        notebook.add(server_tab, text="Backend Servers")

        ttk.Label(server_tab, text="Number of Servers:").grid(row=0, column=0, sticky='w')
        self.server_count = tk.IntVar(value=2)
        tk.Spinbox(server_tab, from_=1, to=10, textvariable=self.server_count, width=5).grid(row=0, column=1)

        ttk.Button(server_tab, text="Start Servers", command=self.start_servers).grid(row=1, column=0, pady=5)
        ttk.Button(server_tab, text="Stop Servers", command=self.stop_servers).grid(row=1, column=1, pady=5)

    def setup_load_balancer_tab(self, notebook):
        lb_tab = ttk.Frame(notebook)
        notebook.add(lb_tab, text="Load Balancer")

        ttk.Label(lb_tab, text="Algorithm:").grid(row=0, column=0, sticky='w')
        self.lb_algorithm = tk.StringVar()
        algorithm_menu = ttk.Combobox(lb_tab, textvariable=self.lb_algorithm, state='readonly')
        algorithm_menu['values'] = (
            "round_robin", "least_connections", "ip_hashing", "most_frequent", 
            "weighted_round_robin", "least_response_time", "resource_based",
            "voting", "random", "specified_ip_hash"
        )
        algorithm_menu.grid(row=0, column=1)
        algorithm_menu.bind("<<ComboboxSelected>>", 
                          lambda e: (self.update_lb_fields(e), self.update_algorithm_description()))

        self.extra_lb_input_label = ttk.Label(lb_tab, text="Extra Info:")
        self.extra_lb_input_entry = ttk.Entry(lb_tab)

        # Add visualization options
        viz_frame = ttk.LabelFrame(lb_tab, text="Visualization Options")
        viz_frame.grid(row=4, column=0, columnspan=2, sticky='ew', pady=10)

        ttk.Label(viz_frame, text="Update Interval (sec):").grid(row=0, column=0, sticky='w')
        self.update_interval = tk.IntVar(value=5)
        tk.Spinbox(viz_frame, from_=1, to=30, textvariable=self.update_interval, width=5).grid(row=0, column=1)

        # Add a description field
        self.algorithm_description = tk.StringVar()
        description_frame = ttk.LabelFrame(lb_tab, text="Algorithm Description")
        description_frame.grid(row=3, column=0, columnspan=2, sticky='ew', pady=10)

        description_label = ttk.Label(
            description_frame, 
            textvariable=self.algorithm_description,
            wraplength=400
        )
        description_label.pack(padx=5, pady=5)

        ttk.Button(lb_tab, text="Start Load Balancer", command=self.start_load_balancer).grid(row=2, column=0, pady=5)
        ttk.Button(lb_tab, text="Stop Load Balancer", command=self.stop_load_balancer).grid(row=2, column=1, pady=5)

    def setup_client_tab(self, notebook):
        client_tab = ttk.Frame(notebook)
        notebook.add(client_tab, text="Client")

        ttk.Label(client_tab, text="Algorithm:").grid(row=0, column=0, sticky='w')
        self.client_algorithm = tk.StringVar()
        client_alg_menu = ttk.Combobox(client_tab, textvariable=self.client_algorithm, state='readonly')
        client_alg_menu['values'] = (
            "round_robin", "least_connections", "ip_hashing", "most_frequent", 
            "weighted_round_robin", "least_response_time", "resource_based",
            "voting", "random", "specified_ip_hash"
        )
        client_alg_menu.grid(row=0, column=1)
        client_alg_menu.bind("<<ComboboxSelected>>", self.update_client_fields)

        self.extra_client_input_label = ttk.Label(client_tab, text="Extra Info:")
        self.extra_client_input_entry = ttk.Entry(client_tab)

        ttk.Button(client_tab, text="Start Client", command=self.start_client).grid(row=2, column=0, pady=5)
        ttk.Button(client_tab, text="Stop Client", command=self.stop_client).grid(row=2, column=1, pady=5)

        self.client_output = scrolledtext.ScrolledText(client_tab, height=10)
        self.client_output.grid(row=3, column=0, columnspan=2, pady=5)

    def update_algorithm_description(self):
        descriptions = {
            "round_robin": "Distributes requests sequentially across servers in a circular order.",
            "least_connections": "Routes to the server with the fewest active connections.",
            "ip_hashing": "Maps clients to servers based on their IP address hash.",
            "most_frequent": "Routes to the server that has handled the most requests (Most Frequently Used).",
            "weighted_round_robin": "Like round robin but considers server weights.",
            "least_response_time": "Routes to the server with the fastest response time.",
            "resource_based": "Routes based on server CPU and memory usage.",
            "voting": "Uses multiple algorithms and picks the majority choice.",
            "random": "Randomly selects a server for each request.",
            "specified_ip_hash": "Allows client to specify a server, falls back to IP hash."
        }

        algo = self.lb_algorithm.get()
        self.algorithm_description.set(descriptions.get(algo, "No description available"))

    def update_lb_fields(self, event):
        algo = self.lb_algorithm.get()
        self.extra_lb_input_label.grid_remove()
        self.extra_lb_input_entry.grid_remove()

        if algo in ["ip_hashing", "ip_hash", "specified_ip_hash"]:
            self.extra_lb_input_label.config(text="IP Address:" if algo != "specified_ip_hash" else "Server:")
            self.extra_lb_input_label.grid(row=1, column=0)
            self.extra_lb_input_entry.grid(row=1, column=1)

    def update_client_fields(self, event):
        algo = self.client_algorithm.get()
        self.extra_client_input_label.grid_remove()
        self.extra_client_input_entry.grid_remove()

        if algo in ["ip_hashing", "ip_hash", "specified_ip_hash"]:
            self.extra_client_input_label.config(text="IP Address:" if algo != "specified_ip_hash" else "Server:")
            self.extra_client_input_label.grid(row=1, column=0)
            self.extra_client_input_entry.grid(row=1, column=1)

    def start_servers(self):
        self.backend_ports = []
        for i in range(self.server_count.get()):
            port = 9001 + i
            proc = subprocess.Popen(["python3", "backend_server.py", str(port)])
            self.processes[f"server_{port}"] = proc
            self.backend_ports.append(port)
        messagebox.showinfo("Servers Started", f"Started {self.server_count.get()} backend servers")

    def stop_servers(self):
        for key in list(self.processes.keys()):
            if key.startswith("server_"):
                self.processes[key].terminate()
                self.processes[key].wait()
                del self.processes[key]
        messagebox.showinfo("Servers Stopped", "All backend servers have been stopped")

    def start_load_balancer(self):
        if not self.backend_ports:
            messagebox.showerror("Error", "No backend servers running. Please start servers first.")
            return

        algo = self.lb_algorithm.get()
        mapped_algo = self.ALGORITHM_MAP.get(algo, algo)

        args = ["python3", "load_balancer.py"] + [str(p) for p in self.backend_ports]

        if mapped_algo == "specified_ip_hash":
            if self.extra_lb_input_entry.get():
                args += [mapped_algo, self.extra_lb_input_entry.get()]
            else:
                messagebox.showerror("Error", "Please specify a server for specified_ip_hash algorithm.")
                return
        else:
            args.append(mapped_algo)

        proc = subprocess.Popen(args)
        self.processes["load_balancer"] = proc
        messagebox.showinfo("Load Balancer Started", f"Load balancer started with {algo} algorithm")

    def stop_load_balancer(self):
        if "load_balancer" in self.processes:
            self.processes["load_balancer"].terminate()
            self.processes["load_balancer"].wait()
            del self.processes["load_balancer"]
            messagebox.showinfo("Load Balancer Stopped", "Load balancer has been stopped")
        else:
            messagebox.showinfo("Info", "No load balancer is currently running")

    def start_client(self):
        algo = self.client_algorithm.get()
        mapped_algo = self.ALGORITHM_MAP.get(algo, algo)

        args = ["python3", "client.py", "--algorithm", mapped_algo]

        if algo in ["ip_hashing", "ip_hash", "specified_ip_hash"]:
            if self.extra_client_input_entry.get():
                args += ["--server", self.extra_client_input_entry.get()]

        self.client_output.delete(1.0, tk.END)
        self.client_output.insert(tk.END, f"Starting client with algorithm: {algo}\n")
        self.client_output.see(tk.END)

        proc = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        self.processes["client"] = proc
        self.root.after(100, lambda: self.read_output(proc))

    def read_output(self, proc):
        if proc.poll() is None:
            line = proc.stdout.readline()
            if line:
                self.client_output.insert(tk.END, line)
                self.client_output.see(tk.END)
            self.root.after(100, lambda: self.read_output(proc))
        else:
            self.client_output.insert(tk.END, "Client process completed.\n")
            self.client_output.see(tk.END)

    def stop_client(self):
        if "client" in self.processes:
            self.processes["client"].terminate()
            self.processes["client"].wait()
            del self.processes["client"]
            self.client_output.insert(tk.END, "Client stopped by user.\n")
            self.client_output.see(tk.END)
        else:
            messagebox.showinfo("Info", "No client is currently running")

    def show_help(self):
        help_window = tk.Toplevel(self.root)
        help_window.title("Load Balancer Help")
        help_window.geometry("600x500")

        text = scrolledtext.ScrolledText(help_window, width=70, height=25)
        text.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

        help_content = """
# Load Balancer Algorithms

- round_robin: Routes requests sequentially to each server in turn
- least_connections: Routes to the server with the fewest active connections
- ip_hashing: Consistently routes clients to the same server based on IP
- most_frequent: Routes to the server that has handled the most requests
- weighted_round_robin: Like round robin but with server weights
- least_response_time: Routes to the server with the fastest response time
- resource_based: Routes based on server CPU and memory usage
- voting: Combines multiple algorithms and selects the majority choice
- random: Randomly selects a server for each request
- specified_ip_hash: Allows client to specify a server, falls back to IP hash

# Additional Parameters

- IP Address (for ip_hash/ip_hashing): Client IP used for consistent hashing
- Server (for specified_ip_hash): Specific server to route to (optional)

# Usage Instructions

1. Start Backend Servers: Select the number of servers and click "Start Servers"
2. Start Load Balancer: Select an algorithm and provide any required extra info
3. Start Client: Select the same algorithm as the load balancer for testing

The load balancer visualizations will display real-time statistics on request distribution,
network topology, and algorithm performance comparisons.
"""

        text.insert(tk.END, help_content)
        text.config(state=tk.DISABLED)

    def __del__(self):
        for proc in self.processes.values():
            try:
                proc.terminate()
                proc.wait()
            except:
                pass

if __name__ == "__main__":
    root = tk.Tk()
    root.geometry("600x500")
    app = LoadBalancerGUI(root)
    root.protocol("WM_DELETE_WINDOW", lambda: (app.__del__(), root.destroy()))
    root.mainloop()
