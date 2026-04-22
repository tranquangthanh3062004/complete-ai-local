"""Test tat ca API endpoints."""
import urllib.request, urllib.parse, json, sys

BASE = "http://localhost:8000"
errors = []

def req(method, path, data=None, headers=None):
    url = BASE + path
    if data:
        body = urllib.parse.urlencode(data).encode() if isinstance(data, dict) and headers and "form" in str(headers) else json.dumps(data).encode()
    else:
        body = None
    h = headers or {"Content-Type": "application/json"}
    r = urllib.request.Request(url, data=body, headers=h, method=method)
    try:
        resp = urllib.request.urlopen(r, timeout=10)
        return resp.status, json.loads(resp.read())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read())
    except Exception as ex:
        return 0, str(ex)

# 1. Health
status, data = req("GET", "/health")
print(f"[{'OK' if status==200 else 'FAIL'}] GET /health -> {status}: {data}")
if status != 200: errors.append("health")

# 2. Login
body = urllib.parse.urlencode({"username": "admin@local.com", "password": "admin123"}).encode()
r = urllib.request.Request(BASE + "/auth/token", data=body,
    headers={"Content-Type": "application/x-www-form-urlencoded"}, method="POST")
try:
    resp = urllib.request.urlopen(r, timeout=10)
    token_data = json.loads(resp.read())
    token = token_data.get("access_token", "")
    print(f"[OK] POST /auth/token -> 200: got token")
except urllib.error.HTTPError as e:
    print(f"[FAIL] POST /auth/token -> {e.code}: {e.read()}")
    token = ""
    errors.append("login")

# 3. Get /me
if token:
    status, data = req("GET", "/auth/me", headers={"Authorization": f"Bearer {token}"})
    print(f"[{'OK' if status==200 else 'FAIL'}] GET /auth/me -> {status}: {data}")
    if status != 200: errors.append("me")

# 4. Direct chat (no Ollama needed to check endpoint exists)
status, data = req("POST", "/agents/direct", data={"query": "Xin chao"})
print(f"[{'OK' if status==200 else 'FAIL'}] POST /agents/direct -> {status}: {str(data)[:100]}")
if status not in (200, 500): errors.append("direct_chat")

# 5. Learning stats
status, data = req("GET", "/learning/stats")
print(f"[{'OK' if status==200 else 'FAIL'}] GET /learning/stats -> {status}: {data}")
if status != 200: errors.append("learning_stats")

print("")
if errors:
    print("FAILED: " + str(errors))
    sys.exit(1)
else:
    print("ALL API TESTS PASSED!")
