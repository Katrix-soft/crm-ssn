#!/usr/bin/env python3
"""
enriquecer_mendoza_ssn.py
---------------------------------------------------------------------------------------------------
Enriquece los productores de Mendoza consultando en vivo en la SSN utilizando CapSolver.
Completa campos faltantes (Teléfono, Email, Domicilio, Localidad, Resolución).
Estrategia anti-ban y anti-rate limit con delays respetuosos (2.5 - 4s) y cooldown de IP automático.
"""

import os
import sys
import sqlite3
import time
import random
import re
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed

from ssn_test import (
    DB_PATH,
    CAPSOLVER_KEY,
    SSN_URL,
    obtener_sitekey,
    resolver_captcha,
    buscar_en_ssn,
    parsear_resultado,
    guardar_en_db,
    obtener_headers_seguros,
    obtener_proxies_activos
)

# Colores de consola
C_RESET   = "\033[0m"
C_BOLD    = "\033[1m"
C_GREEN   = "\033[1m\033[38;5;46m"    # Verde Neón
C_YELLOW  = "\033[1m\033[38;5;226m"   # Amarillo
C_RED     = "\033[1m\033[38;5;196m"   # Rojo
C_CYAN    = "\033[1m\033[38;5;51m"    # Cyan
C_MAGENTA = "\033[1m\033[38;5;201m"   # Magenta
C_DIM     = "\033[38;5;240m"          # Gris

STOP_ENRICHMENT = False

# Locks para hilos
db_lock = threading.Lock()
sitekey_lock = threading.Lock()
stats_lock = threading.Lock()
print_lock = threading.Lock()

sitekey_cache = None
completados = 0
sin_datos = 0
errores = 0

def obtener_mendoza_incompletos(ramo_tipo: str = "TODOS") -> list[dict]:
    if not os.path.exists(DB_PATH):
        print(f"{C_RED}❌ No se encontró la base de datos en {DB_PATH}{C_RESET}")
        return []
    
    conn = sqlite3.connect(DB_PATH, timeout=30.0)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    ramo_clean = (ramo_tipo or "TODOS").upper()
    if ramo_clean == "PATRIMONIALES":
        ramo_sql = "AND (UPPER(ramo) LIKE '%PATRIMONIALES%' OR UPPER(ramo) LIKE '%PATRIMONIO%')"
    elif ramo_clean == "VIDA":
        ramo_sql = "AND (UPPER(ramo) LIKE '%VIDA%')"
    else:
        ramo_sql = ""

    cursor.execute(f"""
        SELECT matricula, documento, cuit, nombre, provincia, localidad, observaciones, telefono, email, ramo
        FROM productores_detalle 
        WHERE (UPPER(provincia) LIKE '%MENDOZA%' OR UPPER(localidad) IN ('GODOY CRUZ', 'GUAYMALLEN', 'MAIPU', 'SAN RAFAEL', 'LAS HERAS', 'LUJAN DE CUYO', 'MENDOZA', 'RIVADAVIA', 'SAN MARTIN', 'TUNUYAN', 'TUPUNGATO', 'LA PAZ', 'MALARGUE', 'GENERAL ALVEAR', 'SAN CARLOS', 'SANTA ROSA', 'LAVALLE', 'JUNIN'))
          {ramo_sql}
          AND (telefono IS NULL OR telefono = '' OR telefono = '—' OR telefono LIKE 'E-mail%' OR email IS NULL OR email = '' OR email = '—')
          AND (observaciones IS NULL OR observaciones NOT LIKE '%NO_SSN_LIVE%')
        ORDER BY CAST(matricula AS INTEGER) ASC
    """)
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def marcar_no_ssn(matricula: str, obs_actual: str):
    nueva_obs = f"{obs_actual} NO_SSN_LIVE".strip() if obs_actual else "NO_SSN_LIVE"
    try:
        conn = sqlite3.connect(DB_PATH, timeout=30.0)
        cursor = conn.cursor()
        cursor.execute("UPDATE productores_detalle SET observaciones = ? WHERE matricula = ?", (nueva_obs, matricula))
        conn.commit()
        conn.close()
    except Exception as ex:
        with print_lock:
            print(f"Error marcando NO_SSN_LIVE para {matricula}: {ex}")

def procesar_un_productor(prod: dict, idx: int, total_len: int, delay_min: float, delay_max: float):
    global STOP_ENRICHMENT, sitekey_cache, completados, sin_datos, errores
    if STOP_ENRICHMENT:
        return

    mat = prod["matricula"]
    nombre = prod.get("nombre") or "Desconocido"
    obs = prod.get("observaciones") or ""

    with print_lock:
        print(f"{C_BOLD}[{idx}/{total_len}]{C_RESET} Consultando Matrícula {C_CYAN}{mat}{C_RESET} ({nombre})...")

    token = None
    # Intento con CapSolver
    try:
        with sitekey_lock:
            sk = sitekey_cache
        token = resolver_captcha(sk)
    except Exception as ex:
        with print_lock:
            print(f"  {C_RED}❌ Error al resolver Captcha en CapSolver para {mat}: {ex}{C_RESET}")
        try:
            new_sk = obtener_sitekey()
            with sitekey_lock:
                sitekey_cache = new_sk
            token = resolver_captcha(new_sk)
        except Exception:
            with stats_lock:
                errores += 1
            time.sleep(3)
            return

    # Consulta HTTP a SSN
    try:
        html = buscar_en_ssn(mat, "MATRICULA", token)
        
        # Chequear bloqueo HTTP
        if "access denied" in html.lower() or "too many requests" in html.lower() or "429" in html:
            with print_lock:
                print(f"{C_YELLOW}⚠️ Detectado posible Rate Limit de IP. Pausando 5 minutos (cooldown)...{C_RESET}")
            for _ in range(300):
                if STOP_ENRICHMENT:
                    break
                time.sleep(1)
            return

        datos = parsear_resultado(html)

        if datos and (datos.get("telefono") or datos.get("email") or datos.get("cuit") or datos.get("resolucion")):
            datos["matricula"] = mat
            with db_lock:
                guardar_en_db(datos)
            with stats_lock:
                completados += 1
            tel = datos.get("telefono") or "Sin Tel"
            email = datos.get("email") or "Sin Email"
            prov = datos.get("provincia") or "Mendoza"
            res_info = datos.get("resolucion") or ""
            with print_lock:
                print(f"  {C_GREEN}{C_BOLD}✓ [Mat {mat}] ¡REEMPLAZADO EN DB! Tel: {tel} | Email: {email} | Prov: {prov} | Res: {res_info[:35]}{C_RESET}")
        else:
            with stats_lock:
                sin_datos += 1
            with db_lock:
                marcar_no_ssn(mat, obs)
            with print_lock:
                print(f"  {C_DIM}- Sin datos detallados en SSN para matrícula {mat}.{C_RESET}")

    except Exception as err:
        with stats_lock:
            errores += 1
        with print_lock:
            print(f"  {C_RED}❌ Error en búsqueda SSN para {mat}: {err}{C_RESET}")

    # Respetar pausa aleatoria anti-ban por worker
    wait = random.uniform(delay_min, delay_max)
    time.sleep(wait)

def ejecutar_enriquecimiento_mendoza(delay_min: float = 2.5, delay_max: float = 4.0, max_items: int = 0, ramo_tipo: str = "VIDA", workers: int = 2):
    global STOP_ENRICHMENT, sitekey_cache, completados, sin_datos, errores
    STOP_ENRICHMENT = False
    completados = 0
    sin_datos = 0
    errores = 0
    
    pendientes = obtener_mendoza_incompletos(ramo_tipo=ramo_tipo)
    total_incompletos = len(pendientes)
    
    if max_items > 0:
        pendientes = pendientes[:max_items]

    print(f"\n{C_CYAN}{C_BOLD}🍇 INICIANDO ENRIQUECIMIENTO PARALELO ({workers} WORKERS) DE PRODUCTORES DE MENDOZA ({ramo_tipo}) VIA SSN{C_RESET}")
    print(f"{C_CYAN}  Total de productores de Mendoza ({ramo_tipo}) incompletos encontrados: {total_incompletos}{C_RESET}")
    print(f"{C_CYAN}  Se procesarán: {len(pendientes)} registros con {workers} hilos paralelos y delays de {delay_min}s a {delay_max}s...{C_RESET}\n")

    if not pendientes:
        print(f"{C_GREEN}{C_BOLD}🎉 ¡Todos los productores de Mendoza ({ramo_tipo}) ya tienen teléfono y email o ya fueron procesados!{C_RESET}")
        return 0

    try:
        print(f"{C_MAGENTA}🔑 Obteniendo Sitekey de la SSN...{C_RESET}")
        sitekey_cache = obtener_sitekey()
        print(f"{C_GREEN}✓ Sitekey obtenido: {sitekey_cache}{C_RESET}\n")
    except Exception as e:
        print(f"{C_YELLOW}⚠️ No se pudo auto-detectar sitekey ({e}), usando fallback por defecto.{C_RESET}")
        sitekey_cache = "6Ld-lCUaAAAAAN6S246U1h2f3g8u4h7"

    total_len = len(pendientes)
    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = [
            executor.submit(procesar_un_productor, prod, idx, total_len, delay_min, delay_max)
            for idx, prod in enumerate(pendientes, start=1)
        ]
        for future in as_completed(futures):
            if STOP_ENRICHMENT:
                break

    print(f"\n{C_MAGENTA}{C_BOLD}======================================================{C_RESET}")
    print(f"{C_GREEN}{C_BOLD}📊 RESUMEN DE ENRIQUECIMIENTO MENDOZA ({ramo_tipo}) - MULTIWORKER ({workers}):{C_RESET}")
    print(f"  ✓ Productores enriquecidos exitosamente : {completados}")
    print(f"  - Sin datos en registro en vivo         : {sin_datos}")
    print(f"  ❌ Errores de conexión/captcha          : {errores}")
    print(f"{C_MAGENTA}{C_BOLD}======================================================{C_RESET}")
    return completados

def detener():
    global STOP_ENRICHMENT
    STOP_ENRICHMENT = True

if __name__ == "__main__":
    delay_min = float(sys.argv[1]) if len(sys.argv) > 1 else 2.5
    delay_max = float(sys.argv[2]) if len(sys.argv) > 2 else 4.0
    limit = int(sys.argv[3]) if len(sys.argv) > 3 else 0
    ramo = sys.argv[4] if len(sys.argv) > 4 else "VIDA"
    workers = int(sys.argv[5]) if len(sys.argv) > 5 else 2
    
    ejecutar_enriquecimiento_mendoza(delay_min=delay_min, delay_max=delay_max, max_items=limit, ramo_tipo=ramo, workers=workers)

