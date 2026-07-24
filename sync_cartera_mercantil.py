import asyncio
import sqlite3
import re
from datetime import datetime, timedelta
from typing import List, Dict, Any

from mercantil_andina import MercantilAndinaClient
import ssn_test  # Para DB_PATH

def extract_cuenta(companias: str) -> str:
    """Extrae el número de cuenta de Mercantil Andina del string de compañías."""
    if not companias:
        return None
    match = re.search(r"Mercantil Andina \(Cta:\s*(\d+)\)", companias)
    if match:
        return match.group(1)
    return None

def get_producers_with_mercantil() -> List[Dict]:
    conn = sqlite3.connect(ssn_test.DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT matricula, nombre, companias FROM productores_detalle WHERE companias LIKE '%Mercantil Andina (Cta:%'")
    rows = cursor.fetchall()
    conn.close()
    
    return [
        {
            "matricula": str(r[0]),
            "nombre": r[1],
            "cuenta": extract_cuenta(r[2])
        }
        for r in rows if extract_cuenta(r[2])
    ]

def get_or_create_cliente(cursor: sqlite3.Cursor, asegurado: Dict, client: MercantilAndinaClient) -> int:
    """Busca un cliente por DNI/CUIT y si no existe lo crea."""
    dni_cuil = asegurado.get("documento", {}).get("numero")
    nombre = asegurado.get("nombre", "")
    
    if not dni_cuil:
        # Si no hay documento, intentamos buscar por nombre exacto
        cursor.execute("SELECT id FROM clientes WHERE nombre = ?", (nombre,))
        row = cursor.fetchone()
        if row: return row[0]
        # Crear sin documento
        cursor.execute("INSERT INTO clientes (nombre) VALUES (?)", (nombre,))
        return cursor.lastrowid
        
    cursor.execute("SELECT id FROM clientes WHERE dni_cuil = ?", (dni_cuil,))
    row = cursor.fetchone()
    if row:
        return row[0]
        
    # El cliente no existe, lo creamos
    # Podríamos llamar a get_cliente_por_doc para enriquecer, pero por ahora insertamos lo básico
    # para no saturar la API. El usuario puede pedir sincronización profunda de clientes luego.
    cursor.execute(
        "INSERT INTO clientes (nombre, dni_cuil) VALUES (?, ?)", 
        (nombre, dni_cuil)
    )
    return cursor.lastrowid

def insert_or_update_poliza(cursor: sqlite3.Cursor, operacion: Dict, cliente_id: int, matricula: str, cuota: Dict):
    """Inserta o actualiza una póliza en la base de datos."""
    poliza_num = str(operacion.get("poliza"))
    rama = operacion.get("rama", {}).get("nombre", "")
    vigencia_desde = operacion.get("vigencia", {}).get("desde", "")
    vigencia_hasta = operacion.get("vigencia", {}).get("hasta", "")
    
    # Cuota / Prima
    prima = 0.0
    premio = 0.0
    if cuota and cuota.get("costo"):
        prima = cuota["costo"].get("prima", 0.0)
        premio = cuota["costo"].get("premio", 0.0)

    # Revisar si ya existe
    cursor.execute("SELECT id FROM polizas WHERE nro_poliza = ?", (poliza_num,))
    row = cursor.fetchone()
    
    if row:
        # Actualizar
        cursor.execute("""
            UPDATE polizas SET
                vigencia_desde = ?, vigencia_hasta = ?, prima = ?, premio = ?, estado = ?
            WHERE id = ?
        """, (vigencia_desde, vigencia_hasta, prima, premio, "Vigente", row[0]))
    else:
        # Insertar
        cursor.execute("""
            INSERT INTO polizas (
                cliente_id, pas_matricula, compania, ramo, nro_poliza, 
                vigencia_desde, vigencia_hasta, prima, premio, estado
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            cliente_id, matricula, "Mercantil Andina", rama, poliza_num,
            vigencia_desde, vigencia_hasta, prima, premio, "Vigente"
        ))


async def sync_cartera_productor(client: MercantilAndinaClient, db_conn: sqlite3.Connection, prod: Dict):
    cuenta = prod["cuenta"]
    matricula = prod["matricula"]
    nombre = prod["nombre"]
    
    print(f"\nSincronizando cartera de {nombre} (Matrícula: {matricula}, Cuenta: {cuenta})...")
    
    # Consultar operaciones del último año
    hoy = datetime.now()
    hace_unos_dias = hoy - timedelta(days=30)
    
    desde_str = hace_unos_dias.strftime("%Y-%m-%d")
    hasta_str = hoy.strftime("%Y-%m-%d")
    
    page = 1
    size = 50
    total_operaciones = 0
    nuevos_clientes = 0
    
    cursor = db_conn.cursor()
    
    while True:
        try:
            print(f"  -> Obteniendo página {page}...")
            resp = await client.get_operaciones(cuenta, desde_str, hasta_str, size, page)
            
            datos = resp.get("datos", [])
            if not datos:
                break
                
            for op_data in datos:
                operacion = op_data.get("operacion", {})
                cuota = op_data.get("cuota", {})
                asegurado = operacion.get("asegurado", {})
                
                # 1. Gestionar Cliente
                clientes_previos = cursor.execute("SELECT COUNT(*) FROM clientes").fetchone()[0]
                cliente_id = get_or_create_cliente(cursor, asegurado, client)
                clientes_actuales = cursor.execute("SELECT COUNT(*) FROM clientes").fetchone()[0]
                
                if clientes_actuales > clientes_previos:
                    nuevos_clientes += 1
                
                # 2. Gestionar Póliza
                insert_or_update_poliza(cursor, operacion, cliente_id, matricula, cuota)
                total_operaciones += 1
                
            db_conn.commit()
            
            total_paginas = resp.get("total_paginas", 1)
            if page >= total_paginas:
                break
                
            page += 1
            
        except Exception as e:
            print(f"  [ERROR] Falló la obtención de la página {page}: {e}")
            break
            
    print(f"✓ {nombre}: {total_operaciones} operaciones procesadas. {nuevos_clientes} nuevos clientes registrados.")


async def run_sync_cartera():
    print("Iniciando Sincronización Masiva de Cartera (Mercantil Andina)...")
    
    producers = get_producers_with_mercantil()
    if not producers:
        print("No se encontraron productores asociados a Mercantil Andina en la base de datos.")
        return
        
    print(f"Se encontraron {len(producers)} productores para sincronizar.")
    
    client = MercantilAndinaClient()
    conn = sqlite3.connect(ssn_test.DB_PATH)
    
    for prod in producers:
        await sync_cartera_productor(client, conn, prod)
        
    conn.close()
    print("\n=========================================")
    print("Sincronización de Cartera Finalizada.")
    print("=========================================\n")


if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    asyncio.run(run_sync_cartera())
