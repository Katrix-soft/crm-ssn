import sys
import os
sys.path.insert(0, os.path.abspath("api-crm"))
from fastapi.testclient import TestClient
from api import app, create_token

token = create_token(data={"username": "admin", "role": "admin", "user_id": 1, "matricula": None})
client = TestClient(app)
response = client.get("/pas/?page=1&page_size=5", headers={"Authorization": f"Bearer {token}"})
print("STATUS:", response.status_code)
print("PAYLOAD:", response.json() if response.status_code == 200 else response.text)
