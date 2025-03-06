import requests
import threading

def make_request():
    url = "http://localhost:8001"
    for _ in range(200):
        try:
            response = requests.get(url)
            print(f"Response: {response.status_code}")
        except requests.exceptions.ConnectionError:
            print("Failed to connect")

threads = []
for _ in range(40):
    thread = threading.Thread(target=make_request)
    thread.start()
    threads.append(thread)

for thread in threads:
    thread.join()

