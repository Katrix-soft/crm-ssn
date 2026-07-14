import sys
import os
sys.path.insert(0, os.path.abspath("api-crm"))
from fastapi.testclient import TestClient
from api import app, create_access_token
import sqlite3

token = create_access_token(data={"sub": "admin", "role": "admin", "user_id": 1, "matricula": None})

client = TestClient(app)
response = client.get("/pas/?page=1&page_size=5", headers={"Authorization": f"Bearer {token}"})
if response.status_code == 200:
    items = response.json().get("items", [])
    if items:
        print("Primer registro devuelto a la UI:")
        print(items[0])
    else:
        print("No items")
else:
    print(response.json())
