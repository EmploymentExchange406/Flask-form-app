import json

with open("registration-466210-4946687b0717.json", "r") as f:
    data = json.load(f)

with open(".env", "w") as f:
    escaped = json.dumps(data)
    f.write(f"GOOGLE_CREDS={escaped}")
