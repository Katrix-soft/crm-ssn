import sys
sys.path.append("api-crm")
from fastapi.testclient import TestClient
from api import app

client = TestClient(app)

response = client.get("/pas/?page=1&page_size=2")
print("Response status:", response.status_code)
print("Response JSON:", response.json())
