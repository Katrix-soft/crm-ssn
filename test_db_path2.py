import sys
sys.path.append("api-crm")
import ssn_test as db
print("DB_PATH in api-crm/ssn_test is:", db.DB_PATH)
import os
print("Exists:", os.path.exists(db.DB_PATH))
if os.path.exists(db.DB_PATH):
    print("Size:", os.path.getsize(db.DB_PATH))
