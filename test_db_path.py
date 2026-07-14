import ssn_test as db
print("DB_PATH in ssn_test is:", db.DB_PATH)
import os
print("Exists:", os.path.exists(db.DB_PATH))
if os.path.exists(db.DB_PATH):
    print("Size:", os.path.getsize(db.DB_PATH))
    import sqlite3
    conn = sqlite3.connect(db.DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    print("Tables:", cursor.fetchall())
    conn.close()
