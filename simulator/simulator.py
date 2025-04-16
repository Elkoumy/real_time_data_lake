import os
import time
import threading
from itertools import cycle
import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry


BASE_URL = os.getenv('BASE_URL', 'http://webservice:8000')
DATA_DIR = os.getenv('DATA_DIR', '/app/data')
SEND_INTERVAL = float(os.getenv('SEND_INTERVAL', '0.1'))

retry_strategy = Retry(
    total=3,
    backoff_factor=1,
    status_forcelist=[429, 500, 502, 503, 504]
)
adapter = HTTPAdapter(max_retries=retry_strategy)
http = requests.Session()
http.mount("http://", adapter)
http.mount("https://", adapter)

def load_files(directory):
    files = []
    try:
        filenames = sorted([f for f in os.listdir(directory) if f.endswith('.json')])
        for filename in filenames:
            filepath = os.path.join(directory, filename)
            files.append(filepath)
        print(f"Loaded {len(files)} files from {directory}")
    except FileNotFoundError:
        print(f"Directory {directory} not found!")
    return files

endpoints = {
    'employee': os.path.join(DATA_DIR, 'employees'),
    'client': os.path.join(DATA_DIR, 'clients'),
    'session': os.path.join(DATA_DIR, 'sessions')
}

loaded_files = {}
for file_type, directory in endpoints.items():
    if files := load_files(directory):
        loaded_files[file_type] = files

def send_file_loop(file_type, file_list, interval):
    for filepath in cycle(file_list):
        filename = os.path.basename(filepath)
        url = f"{BASE_URL}/upload/file/{filename}"
        try:
            with open(filepath, 'rb') as f:
                files_payload = {'file': f}
                response = http.post(url, files=files_payload, timeout=5)
            print(f"Sent file {filename} for {file_type} - Status: {response.status_code}")
        except Exception as e:
            print(f"Error sending file {filename} for {file_type}: {str(e)}")
        finally:
            time.sleep(interval)

threads = []
for file_type, file_list in loaded_files.items():
    thread = threading.Thread(
        target=send_file_loop,
        args=(file_type, file_list, SEND_INTERVAL),
        daemon=True
    )
    thread.start()
    threads.append(thread)

try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    print("\nStopping simulator...")
