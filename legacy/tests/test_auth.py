from modules import auth
result = auth.check_existing_token()
ok = result.get("ok", False)
username = result.get("username", "none")
print(f"ok={ok}, username={username}")