import requests
import threading
import argparse
import time

def make_request(url, algorithm, specified_server=None):
    """
    Makes 200 GET requests to the given URL using the provided load balancing algorithm.
    Optionally adds a specified server header if provided.
    """
    for _ in range(200):
        try:
            headers = {"X-Load-Balancing-Algorithm": algorithm}
            if specified_server:
                headers["X-Specified-Server"] = specified_server

            response = requests.get(url, headers=headers)
            print(f"Response: {response.status_code}, Algorithm: {algorithm}")
        except requests.exceptions.ConnectionError:
            print("Failed to connect")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Load Balancer Client")
    parser.add_argument("--algorithm", default="", help="Load balancing algorithm to use")
    parser.add_argument("--server", help="Specify server to use (for specified_ip_hash algorithm)")
    args = parser.parse_args()

    url = "http://localhost:8001"
    threads = []

    for _ in range(40):
        thread = threading.Thread(target=make_request, args=(url, args.algorithm, args.server))
        thread.start()
        threads.append(thread)

    for thread in threads:
        thread.join()

