#!/usr/bin/env python3
"""
sync_crm.py
---------------------------------------------------------------------------------------------------
Sincroniza los datos de productores enriquecidos desde la base SQLite local principal
hacia los entornos del CRM (API CRM SQLite, App Escritorio Desktop y PostgreSQL).
"""

import os
import sys
import sqlite3

SRC_DB = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "productores_scraped.db")

TARGET_DBS = [
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "api-crm", "data", "productores_scraped.db"),
    os.path.expanduser("~/.katrixbroker/data/productores_scraped.db")
]

PG_DSN = os.getenv("DATABASE_URL", "postgresql://postgres:Nachax5$@127.0.0.1:5432/pas")

def sincronizar_sqlites():
    if not os.path.exists(SRC_DB):
        print(f"❌ Base de origen no encontrada: {SRC_DB}")
        return

    conn_src = sqlite3.connect(SRC_DB)
    cur_src = conn_src.cursor()
    cur_src.execute("SELECT * FROM productores_detalle")
    cols = [desc[0] for desc in cur_src.description]
    rows = cur_src.fetchall()
    conn_src.close()

    print(f"📦 Registros encontrados en base origen ({SRC_DB}): {len(rows)}")

    for target in TARGET_DBS:
        os.makedirs(os.path.dirname(target), exist_ok=True)
        print(f"🔄 Sincronizando hacia: {target}...")
        conn_tgt = sqlite3.connect(target)
        cur_tgt = conn_tgt.cursor()

        cur_tgt.execute("""
            CREATE TABLE IF NOT EXISTS productores_detalle (
                matricula TEXT PRIMARY KEY,
                nombre TEXT,
                documento TEXT,
                cuit TEXT,
                ramo TEXT,
                provincia TEXT,
                telefono TEXT,
                email TEXT,
                resolucion TEXT,
                fecha_resolucion TEXT,
                scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                domicilio TEXT,
                localidad TEXT,
                cod_postal TEXT,
                estado_contacto TEXT DEFAULT 'Sin contactar',
                observaciones TEXT,
                companias TEXT,
                sociedades TEXT,
                usuario_id INTEGER,
                en_organizacion INTEGER DEFAULT 0
            )
        """)

        cur_tgt.execute("PRAGMA table_info(productores_detalle)")
        tgt_cols = [r[1] for r in cur_tgt.fetchall()]
        for col in cols:
            if col not in tgt_cols:
                cur_tgt.execute(f"ALTER TABLE productores_detalle ADD COLUMN {col} TEXT")

        placeholders = ", ".join(["?"] * len(cols))
        cols_str = ", ".join(cols)
        update_str = ", ".join([f"{c}=EXCLUDED.{c}" for c in cols if c != "matricula"])

        upsert_sql = f"""
            INSERT INTO productores_detalle ({cols_str})
            VALUES ({placeholders})
            ON CONFLICT(matricula) DO UPDATE SET {update_str}
        """

        cur_tgt.executemany(upsert_sql, rows)
        conn_tgt.commit()

        cur_tgt.execute("SELECT COUNT(*) FROM productores_detalle")
        tot = cur_tgt.fetchone()[0]
        conn_tgt.close()

        print(f"  ✓ {target} actualizado con éxito ({tot} registros).")

def sincronizar_postgres():
    try:
        import psycopg2
        from psycopg2.extras import execute_batch
    except ImportError:
        print("⚠️ psycopg2 no está instalado, omitiendo sync de PostgreSQL.")
        return

    try:
        pg_conn = psycopg2.connect(PG_DSN)
        pg_conn.autocommit = True
        pg_cur = pg_conn.cursor()

        pg_cur.execute("""
            CREATE TABLE IF NOT EXISTS productores_detalle (
                matricula TEXT PRIMARY KEY,
                nombre TEXT,
                documento TEXT,
                cuit TEXT,
                ramo TEXT,
                provincia TEXT,
                telefono TEXT,
                email TEXT,
                resolucion TEXT,
                fecha_resolucion TEXT,
                scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                domicilio TEXT,
                localidad TEXT,
                cod_postal TEXT,
                estado_contacto TEXT DEFAULT 'Sin contactar',
                observaciones TEXT,
                companias TEXT,
                sociedades TEXT,
                usuario_id INTEGER,
                en_organizacion INTEGER DEFAULT 0
            );
        """)

        sq_conn = sqlite3.connect(SRC_DB)
        sq_cur = sq_conn.cursor()
        sq_cur.execute("""
            SELECT matricula, nombre, documento, cuit, ramo, provincia, telefono, email, 
                   resolucion, fecha_resolucion, domicilio, localidad, cod_postal, 
                   estado_contacto, observaciones, companias, sociedades, usuario_id, en_organizacion 
            FROM productores_detalle
        """)
        rows = sq_cur.fetchall()
        sq_conn.close()

        print(f"🐘 Sincronizando {len(rows)} registros hacia PostgreSQL (`pas`)...")

        upsert_pg = """
            INSERT INTO productores_detalle (matricula, nombre, documento, cuit, ramo, provincia, telefono, email, resolucion, fecha_resolucion, domicilio, localidad, cod_postal, estado_contacto, observaciones, companias, sociedades, usuario_id, en_organizacion)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (matricula) DO UPDATE SET
                nombre = EXCLUDED.nombre,
                documento = EXCLUDED.documento,
                cuit = EXCLUDED.cuit,
                ramo = EXCLUDED.ramo,
                provincia = EXCLUDED.provincia,
                telefono = EXCLUDED.telefono,
                email = EXCLUDED.email,
                resolucion = EXCLUDED.resolucion,
                fecha_resolucion = EXCLUDED.fecha_resolucion,
                domicilio = EXCLUDED.domicilio,
                localidad = EXCLUDED.localidad,
                cod_postal = EXCLUDED.cod_postal,
                estado_contacto = EXCLUDED.estado_contacto,
                observaciones = EXCLUDED.observaciones,
                companias = EXCLUDED.companias,
                sociedades = EXCLUDED.sociedades,
                usuario_id = EXCLUDED.usuario_id,
                en_organizacion = EXCLUDED.en_organizacion;
        """
        execute_batch(pg_cur, upsert_pg, rows, page_size=1000)

        pg_cur.execute("SELECT COUNT(*) FROM productores_detalle;")
        cnt = pg_cur.fetchone()[0]
        print(f"  ✓ PostgreSQL `pas.productores_detalle` actualizado ({cnt} registros).")
        pg_conn.close()
    except Exception as ex:
        print(f"⚠️ Nota sobre PostgreSQL: {ex}")

if __name__ == "__main__":
    print("🚀 Iniciando sincronización de datos al CRM...")
    sincronizar_sqlites()
    sincronizar_postgres()
    print("✨ Sincronización completada exitosamente.")
