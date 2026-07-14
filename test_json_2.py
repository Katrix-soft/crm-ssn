import sys
sys.path.append("api-crm")
import ssn_test as db
from fastapi.encoders import jsonable_encoder

records = db.obtener_todos_db()
if records:
    print("Primer registro raw db:", records[0])
else:
    print("La BD local esta vacía")
