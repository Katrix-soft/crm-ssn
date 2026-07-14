import time
from ssn_test import obtener_todos_db

t0 = time.time()
records = obtener_todos_db()
print(f"Time taken: {time.time() - t0:.2f} seconds")
print(f"Records: {len(records)}")
