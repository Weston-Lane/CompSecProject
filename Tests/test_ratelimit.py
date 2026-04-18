import requests
import urllib3

# This hides the red "InsecureRequestWarning" to keep your console clean
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

url = "https://127.0.0.1:5000/api/login" 

print(f"--- Starting Rate Limit Test against {url} ---")

try:
    for i in range(15):
        # Added a 5-second timeout so it doesn't hang forever
        response = requests.post(
            url, 
            json={"username": "test", "password": "test"}, 
            verify=False,
            timeout=5 
        )
        print(f"Request {i+1:02d}: Status {response.status_code}")
except requests.exceptions.ConnectionError:
    print("ERROR: Could not connect to the server. Is your Flask app actually running?")
except requests.exceptions.Timeout:
    print("ERROR: The request timed out. The server is reachable but not responding.")
except Exception as e:
    print(f"ERROR: An unexpected error occurred: {e}")

print("--- Test Complete ---")