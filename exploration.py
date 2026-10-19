import requests

from config import API_BASE_URL, TEST_USER_EMAIL, TEST_USER_PASSWORD

payload = {
    "username": TEST_USER_EMAIL,
    "password": TEST_USER_PASSWORD,
}

response = requests.post(f"{API_BASE_URL}/v1/user/login/usernamepassword", json=payload)

print("status_code:", response.status_code)
print("Content-Type header:", response.headers["Content-Type"])
print("response.text is a raw string, length:", len(response.text))

body = response.json()
print("response.json() is a Python dict, keys:", list(body.keys()))
print("token (masked):", body["token"][:3] + "...<masked>")
