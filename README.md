# Load Balancer Simulation

This project is a simple Python-based load balancer demo. It includes:

- backend server instances that respond to requests
- a load balancer that distributes traffic using different algorithms
- a client that sends requests to the load balancer
- a GUI controller for starting and stopping the components

## Project Files

- [backend_server.py](backend_server.py) – starts one or more backend servers
- [load_balancer.py](load_balancer.py) – runs the load balancer and visualization UI
- [client.py](client.py) – sends traffic to the load balancer
- [gui_controller.py](gui_controller.py) – GUI wrapper to launch everything more easily

## Requirements

This project uses Python 3 and requires these packages:

- requests
- psutil
- matplotlib
- networkx

Install them with:

```bash
python3 -m pip install requests psutil matplotlib networkx
```

## Running the Project

### Option 1: Use the GUI controller (easiest)

Run:

```bash
python3 gui_controller.py
```

Then:

1. Choose the number of backend servers
2. Click "Start Servers"
3. Select a load balancing algorithm
4. Click "Start Load Balancer"
5. Select the same algorithm in the Client tab
6. Click "Start Client"

### Option 2: Run from the terminal

Start one or more backend servers:

```bash
python3 backend_server.py 9001
python3 backend_server.py 9002
```

Start the load balancer:

```bash
python3 load_balancer.py 9001 9002 voting
```

You can replace `voting` with any supported algorithm such as:

- `round_robin`
- `least_connections`
- `ip_hashing`
- `most_frequent`
- `weighted_round_robin`
- `least_response_time`
- `resource_based`
- `random`
- `specified_ip_hash`

Start the client:

```bash
python3 client.py --algorithm round_robin
```

## Notes

- The load balancer listens on port `8001` by default.
- Backend servers default to ports `9001`, `9002`, and so on.
- If `matplotlib` is not installed, the visualization UI will still run in a reduced form.
