from pydantic import BaseModel, Field
from typing import Optional

class PASListItem(BaseModel):
    matricula: Optional[str] = Field(None, alias="productor_matricula")
    nombre: Optional[str] = Field(None, alias="productor_apellido_nombre")
    
    class Config:
        populate_by_name = True
        allow_population_by_field_name = True

p = PASListItem(matricula="1234", nombre="Pepe")
print("Parsed object:", p.model_dump() if hasattr(p, 'model_dump') else p.dict())
print("Parsed object (by alias):", p.model_dump(by_alias=True) if hasattr(p, 'model_dump') else p.dict(by_alias=True))
