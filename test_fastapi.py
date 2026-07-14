import sys
sys.path.append("api-crm")
from api import list_pas
from pydantic import BaseModel
import asyncio
from fastapi import Request

class MockUser:
    user_id = 1
    role = "admin"
    matricula = None

# We can call list_pas directly since it's just a Python function!
try:
    res = list_pas(q=None, provincia=None, ramo=None, estado_contacto=None, mostly_complete=None, sort_by="matricula", sort_desc=False, page=1, page_size=5, current=MockUser())
    print(res.items[0].dict() if hasattr(res.items[0], 'dict') else res.items[0].model_dump())
except Exception as e:
    import traceback
    traceback.print_exc()
