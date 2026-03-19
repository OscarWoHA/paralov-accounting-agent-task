import httpx
import json
import sys
import re

BASE_URL = "https://kkpqfuj-amager.tripletex.dev"
V2 = f"{BASE_URL}/v2"
RPC = f"{BASE_URL}/JSON-RPC"
EMPLOYEE_TOKEN = "eyJ0b2tlbklkIjoyMTQ3NjI4NDgyLCJ0b2tlbiI6IjBhYjc0Yjg1LWZiMDEtNGZkOC1hMWFiLWY5Nzk3MWZiYjA3NiJ9"
AUTH = ("0", EMPLOYEE_TOKEN)

# Step 1: Get session and CSRF token from web UI with basic auth
client = httpx.Client(auth=AUTH, timeout=30, follow_redirects=True)
r = client.get(f"{BASE_URL}/execute/dashboard")
jsessionid = client.cookies.get("JSESSIONID")
html = r.text

# Extract CSRF token
csrf_match = re.search(r'Token["\s:=]+["\']?([a-f0-9]{40,})', html)
csrf_token = csrf_match.group(1) if csrf_match else None
print(f"JSESSIONID: {jsessionid}")
print(f"CSRF Token: {csrf_token}")

# Step 2: Get the full methods list and find module-related ones
r = client.post(RPC, json={"method": "system.listMethods", "params": [], "id": 1})
methods = r.json().get("result", [])
print(f"\nTotal methods: {len(methods)}")

# Filter for module/subscription/api related methods
module_methods = [m for m in methods if any(k in m.lower() for k in ['module', 'subscri', 'api', 'license', 'activate', 'salesforce'])]
print(f"\nModule/API related methods ({len(module_methods)}):")
for m in sorted(module_methods):
    print(f"  {m}")

# Step 3: The JSON-RPC says "session may have timed out" - we need an authenticated session
# Let me try the syncSystem parameter and the CSRF token
print("\n\n=== Trying JSON-RPC with syncSystem and CSRF ===")
headers = {}
if csrf_token:
    headers["X-CSRF-Token"] = csrf_token

# Try with syncSystem parameter in the request
r = client.post(RPC, json={
    "method": "system.listMethods",
    "params": [],
    "id": 1,
    "syncSystem": -1
}, headers=headers)
print(f"listMethods with CSRF: {r.status_code} - result count: {len(r.json().get('result', []))}")

# The session is not logged in. The "system.listMethods" works without login.
# But all other methods need a session.
# Let's find login-related methods
login_methods = [m for m in methods if any(k in m.lower() for k in ['login', 'session', 'auth', 'token'])]
print(f"\nLogin/Session/Auth methods ({len(login_methods)}):")
for m in sorted(login_methods):
    print(f"  {m}")

client.close()
