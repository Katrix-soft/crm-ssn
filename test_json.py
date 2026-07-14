import sys
sys.path.append("api-crm")
import ssn_test as db
from api_models import PASListItem

res = db.obtener_todos_db(user_id=1, role="admin")
r = res[0]
item = PASListItem(
    matricula=r.get("matricula") or r.get("productor_matricula"),
    nombre=r.get("nombre") or r.get("productor_apellido_nombre"),
    ramo=r.get("ramo"),
    provincia=r.get("provincia"),
    localidad=r.get("localidad"),
    telefono=r.get("telefono"),
    email=r.get("email"),
    estado_contacto=r.get("estado_contacto", "Sin contactar"),
    companias=r.get("companias"),
    documento=r.get("documento") or r.get("productor_id"),
    cuit=r.get("cuit") or r.get("productor_id"),
)
print(item.model_dump_json())
