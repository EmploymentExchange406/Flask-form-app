import base64

with open("flaskformdataproject-38167ba1ba59.json", "rb") as f:
    encoded = base64.b64encode(f.read()).decode("utf-8")

with open("encoded.txt", "w") as f:
    f.write(encoded)

print("✅ Encoded JSON saved to 'encoded.txt'")
