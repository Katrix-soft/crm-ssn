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

def obtener_mendoza_incompletos(ramo_tipo: str = "TODOS") -> list[dict]:
    if not os.path.exists(DB_PATH):
        print(f"{C_RED}❌ No se encontró la base de datos en {DB_PATH}{C_RESET}")
        return []
    
    conn = sqlite3.connect(DB_PATH)
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
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("UPDATE productores_detalle SET observaciones = ? WHERE matricula = ?", (nueva_obs, matricula))
        conn.commit()
        conn.close()
    except Exception as ex:
        print(f"Error marcando NO_SSN_LIVE para {matricula}: {ex}")

def ejecutar_enriquecimiento_mendoza(delay_min: float = 2.5, delay_max: float = 4.0, max_items: int = 0, ramo_tipo: str = "VIDA"):
    global STOP_ENRICHMENT
    STOP_ENRICHMENT = False
    
    pendientes = obtener_mendoza_incompletos(ramo_tipo=ramo_tipo)
    total_incompletos = len(pendientes)
    
    if max_items > 0:
        pendientes = pendientes[:max_items]

    print(f"\n{C_CYAN}{C_BOLD}🍇 INICIANDO ENRIQUECIMIENTO DE PRODUCTORES DE MENDOZA ({ramo_tipo}) VIA SSN (CapSolver){C_RESET}")
    print(f"{C_CYAN}  Total de productores de Mendoza ({ramo_tipo}) incompletos encontrados: {total_incompletos}{C_RESET}")
    print(f"{C_CYAN}  Se procesarán: {len(pendientes)} registros con delays de {delay_min}s a {delay_max}s...{C_RESET}\n")

    if not pendientes:
        print(f"{C_GREEN}{C_BOLD}🎉 ¡Todos los productores de Mendoza ({ramo_tipo}) ya tienen teléfono y email o ya fueron procesados!{C_RESET}")
        return 0

    # Cache de sitekey para no consultar el formulario HTML en cada paso si no cambia
    sitekey_cache = None
    try:
        print(f"{C_MAGENTA}🔑 Obteniendo Sitekey de la SSN...{C_RESET}")
        sitekey_cache = obtener_sitekey()
        print(f"{C_GREEN}✓ Sitekey obtenido: {sitekey_cache}{C_RESET}\n")
    except Exception as e:
        print(f"{C_YELLOW}⚠️ No se pudo auto-detectar sitekey ({e}), usando fallback por defecto.{C_RESET}")
        sitekey_cache = "6Ld-lCUaAAAAAN6S246U1h2f3g8u4h7"

    completados = 0
    sin_datos = 0
    errores = 0

    for idx, prod in enumerate(pendientes, start=1):
        if STOP_ENRICHMENT:
            print(f"\n{C_YELLOW}⏹️ Proceso detenido por el usuario.{C_RESET}")
            break

        mat = prod["matricula"]
        nombre = prod["nombre"] or "Desconocido"
        obs = prod.get("observaciones") or ""

        print(f"{C_BOLD}[{idx}/{len(pendientes)}]{C_RESET} Consultando Matrícula {C_CYAN}{mat}{C_RESET} ({nombre})...")

        token = None
        # Intento con CapSolver
        try:
            token = resolver_captcha(sitekey_cache)
        except Exception as ex:
            print(f"  {C_RED}❌ Error al resolver Captcha en CapSolver: {ex}{C_RESET}")
            # Si el sitekey expiró, re-intentar obtener sitekey
            try:
                sitekey_cache = obtener_sitekey()
                token = resolver_captcha(sitekey_cache)
            except Exception:
                errores += 1
                time.sleep(5)
                continue

        # Consulta HTTP a SSN
        try:
            html = buscar_en_ssn(mat, "MATRICULA", token)
            
            # Chequear bloqueo HTTP
            if "access denied" in html.lower() or "too many requests" in html.lower() or "429" in html:
                print(f"{C_YELLOW}⚠️ Detectado posible Rate Limit de IP. Pausando 5 minutos (cooldown)...{C_RESET}")
                for _ in range(300):
                    if STOP_ENRICHMENT:
                        break
                    time.sleep(1)
                continue

            datos = parsear_resultado(html)

            if datos and (datos.get("telefono") or datos.get("email") or datos.get("cuit") or datos.get("resolucion")):
                datos["matricula"] = mat
                guardar_en_db(datos)
                completados += 1
                tel = datos.get("telefono") or "Sin Tel"
                email = datos.get("email") or "Sin Email"
                prov = datos.get("provincia") or "Mendoza"
                res_info = datos.get("resolucion") or ""
                print(f"  {C_GREEN}{C_BOLD}✓ ¡REEMPLAZADO EN DB! Tel: {tel} | Email: {email} | Prov: {prov} | Res: {res_info[:35]}{C_RESET}")
            else:
                sin_datos += 1
                marcar_no_ssn(mat, obs)
                print(f"  {C_DIM}- Sin datos detallados en SSN para matrícula {mat}.{C_RESET}")

        except Exception as err:
            errores += 1
            print(f"  {C_RED}❌ Error en búsqueda SSN para {mat}: {err}{C_RESET}")

        # Respetar pausa aleatoria anti-ban
        wait = random.uniform(delay_min, delay_max)
        time.sleep(wait)

    print(f"\n{C_MAGENTA}{C_BOLD}======================================================{C_RESET}")
    print(f"{C_GREEN}{C_BOLD}📊 RESUMEN DE ENRIQUECIMIENTO MENDOZA ({ramo_tipo}):{C_RESET}")
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
    
    ejecutar_enriquecimiento_mendoza(delay_min=delay_min, delay_max=delay_max, max_items=limit, ramo_tipo=ramo)
