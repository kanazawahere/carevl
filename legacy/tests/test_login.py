from modules import auth, paths
paths.ensure_directories()

result = auth.login()
ok = result.get("ok", False)
username = result.get("username", "none")
token = result.get("access_token", "")[:20] + "..." if result.get("access_token") else "none"
print(f"ok={ok}, username={username}, token={token}")