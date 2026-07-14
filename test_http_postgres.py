import sys
import os
from dotenv import load_dotenv

# Load env before importing api to force Postgres connection if configured
load_dotenv("api-crm/.env")

sys.path.insert(0, os.path.abspath("api-crm"))
from fastapi.testclient import TestClient
from api import app, create_token
import ssn_test

print("DATABASE_URL in env:", os.environ.get("DATABASE_URL"))
print("psycopg2 available:", ssn_test.psycopg2 is not None)

token = create_token(data={"username": "admin", "role": "admin", "user_id": 1, "matricula": None})
client = TestClient(app)
response = client.get("/pas/?page=1&page_size=5", headers={"Authorization": f"Bearer {token}"})
print("STATUS:", response.status_code)
print("PAYLOAD:", response.json() if response.status_code == 200 else response.text)
