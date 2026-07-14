import sys
sys.path.append("api-crm")
import ssn_test as db

records = db.obtener_todos_db()
if records:
    print("Primer registro raw db:", records[0])
    # simulemos lo que hace api.py
    r = records[0]
    matricula = r.get("matricula") or r.get("productor_matricula")
    nombre = r.get("nombre") or r.get("productor_apellido_nombre")
    print(f"matricula calculada: {matricula}")
    print(f"nombre calculado: {nombre}")
else:
    print("La BD local esta vacía")
