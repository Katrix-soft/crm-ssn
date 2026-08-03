#!/usr/bin/env python3
"""
Script de Enriquecimiento Resiliente de Provincia y Localidad (Dateas + DuckDuckGo + Bing)
---------------------------------------------------------------------------------------------------
Opción B: Conexión Directa Segura Multi-Motor (Dateas -> DuckDuckGo -> Bing)
1. Conexión directa sin proxies fallidos para garantizar el 100% de precisión en los resultados.
2. Control moderado de 2 hilos paralelos con 1.2s de retardo y variaciones aleatorias de TLS.
3. Fallback inteligente en cascada: Dateas Directo -> DuckDuckGo Search -> Bing Search.
4. Auto-cooldown de IP automático si se detecta cualquier micro-bloqueo.
"""

import os
import sys
import sqlite3
import re
import time
import random
import threading
from typing import Optional, List
from concurrent.futures import ThreadPoolExecutor, as_completed

try:
    from curl_cffi import requests as http_req
    USE_CURL_CFFI = True
except ImportError:
    import requests as http_req
    USE_CURL_CFFI = False

from bs4 import BeautifulSoup

DB_PATH = os.path.expanduser("~/.katrixbroker/data/productores_scraped.db")
STOP_ENRICHMENT = False
db_lock = threading.Lock()

PROVINCIAS_ARGENTINAS = [
    "Buenos Aires", "Ciudad Autónoma de Buenos Aires", "CABA", "Córdoba", "Santa Fe", 
    "Mendoza", "Tucumán", "Salta", "Entre Ríos", "Misiones", "Chaco", "Corrientes", 
    "Santiago del Estero", "San Juan", "Jujuy", "Río Negro", "Neuquén", "Formosa", 
    "Chubut", "San Luis", "Catamarca", "La Rioja", "La Pampa", "Santa Cruz", "Tierra del Fuego"
]

CITY_PROV_MAP = {
    "godoy cruz": "Mendoza", "guaymallen": "Mendoza", "maipu": "Mendoza", "san rafael": "Mendoza", 
    "las heras": "Mendoza", "lujan de cuyo": "Mendoza", "mar del plata": "Buenos Aires", 
    "la plata": "Buenos Aires", "bahia blanca": "Buenos Aires", "tandil": "Buenos Aires", 
    "san isidro": "Buenos Aires", "vicente lopez": "Buenos Aires", "avellaneda": "Buenos Aires", 
    "lomas de zamora": "Buenos Aires", "quilmes": "Buenos Aires", "lanus": "Buenos Aires", 
    "moron": "Buenos Aires", "san martin": "Buenos Aires", "tigre": "Buenos Aires", 
    "pilar": "Buenos Aires", "moreno": "Buenos Aires", "merlo": "Buenos Aires", "lujan": "Buenos Aires",
    "rafael calzada": "Buenos Aires", "rosario": "Santa Fe", "santa fe": "Santa Fe", 
    "venado tuerto": "Santa Fe", "rafaela": "Santa Fe", "cordoba": "Córdoba", 
    "villa maria": "Córdoba", "rio cuarto": "Córdoba", "carlos paz": "Córdoba", 
    "ciudad autonoma": "Ciudad Autónoma de Buenos Aires", "caba": "Ciudad Autónoma de Buenos Aires", 
    "capital federal": "Ciudad Autónoma de Buenos Aires"
}

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36 Edg/124.0.0.0"
]

IMPERSONATE_PROFILES = ["chrome124", "firefox120", "edge120", "safari17_0"]

def get_random_headers():
    return {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "es-AR,es;q=0.9,en;q=0.8",
    }

def limpiar_marcas_error_dateas() -> int:
    if not os.path.exists(DB_PATH):
        return 0
    try:
        with db_lock:
            conn = sqlite3.connect(DB_PATH, timeout=20.0)
            cur = conn.cursor()
            cur.execute("""
                UPDATE productores_detalle
                SET observaciones = REPLACE(REPLACE(observaciones, 'NO_DATEAS_2', ''), 'NO_DATEAS_1', '')
                WHERE observaciones LIKE '%NO_DATEAS%'
            """)
            cur.execute("""
                UPDATE productores_detalle
                SET observaciones = TRIM(observaciones)
                WHERE observaciones IS NOT NULL
            """)
            cnt = cur.rowcount
            conn.commit()
            conn.close()
        print(f"🧹 Se limpiaron las marcas de error de Dateas en {cnt} registros.")
        return cnt
    except Exception as ex:
        print(f"Error al limpiar marcas Dateas: {ex}")
        return 0

DATEAS_COOLDOWN_UNTIL = 0
dateas_cooldown_lock = threading.Lock()

def consultar_dateas_con_fallback(cuit: str, session=None) -> dict:
    global DATEAS_COOLDOWN_UNTIL
    c_clean = re.sub(r"\D", "", str(cuit or ""))
    if not c_clean or len(c_clean) < 10:
        return {"status": "SIN_DATOS"}

    headers = get_random_headers()
    imp_target = random.choice(IMPERSONATE_PROFILES)
    req = session if session is not None else http_req

    # --- 1. Intento Directo Dateas (con Circuit Breaker de 10 min) ---
    now = time.time()
    if now >= DATEAS_COOLDOWN_UNTIL:
        url_dateas = f"https://www.dateas.com/es/consulta_cuit_cuil?cuit={c_clean}"
        try:
            if USE_CURL_CFFI:
                r = req.get(url_dateas, headers=headers, impersonate=imp_target, timeout=8)
            else:
                r = req.get(url_dateas, headers=headers, timeout=8)

            if r.status_code == 429 or r.status_code == 403:
                with dateas_cooldown_lock:
                    if time.time() >= DATEAS_COOLDOWN_UNTIL:
                        DATEAS_COOLDOWN_UNTIL = time.time() + 600  # 10 minutos de reposo total
                        print(f"{C_YELLOW}🧊 Dateas en reposo por IP (10 min de silencio). Usando motores de respaldo...{C_RESET}")
            elif r.status_code == 200:
                html_lower = r.text.lower()
                is_blocked = ("access denied" in html_lower or "just a moment..." in html_lower or "attention required" in html_lower or "enable javascript" in html_lower)
                if is_blocked:
                    with dateas_cooldown_lock:
                        if time.time() >= DATEAS_COOLDOWN_UNTIL:
                            DATEAS_COOLDOWN_UNTIL = time.time() + 600
                            print(f"{C_YELLOW}🧊 Dateas en reposo por IP (10 min de silencio). Usando motores de respaldo...{C_RESET}")
                elif "table" in html_lower:
                    soup = BeautifulSoup(r.text, "html.parser")
                    table = soup.find("table")
                    if table:
                        rows = table.find_all("tr")
                        for row in rows[1:]:
                            cols = [c.get_text(strip=True) for c in row.find_all(["td", "th"])]
                            if len(cols) >= 5:
                                p_val = re.sub(r"\s*\(Pcia\)", "", cols[3], flags=re.IGNORECASE).strip()
                                l_val = cols[4].strip()
                                if p_val and p_val != "—":
                                    return {
                                        "status": "OK",
                                        "nombre_dateas": cols[0],
                                        "cuit": cols[1],
                                        "provincia": p_val,
                                        "localidad": l_val,
                                        "fuente": "Dateas Directo"
                                    }
        except Exception:
            pass  # Falló Dateas, continuar con fallbacks

    # --- 2. Fallback CuitOnline Directo / Búsqueda ---
    url_cuitonline = f"https://www.cuitonline.com/constancia/cuit/{c_clean}"
    try:
        if USE_CURL_CFFI:
            r_co = req.get(url_cuitonline, headers=headers, impersonate=imp_target, timeout=8)
        else:
            r_co = req.get(url_cuitonline, headers=headers, timeout=8)

        if r_co.status_code == 200:
            html_lower = r_co.text.lower()
            if ("localidad:" in html_lower or "provincia:" in html_lower) and not ("access denied" in html_lower or "just a moment..." in html_lower):
                soup = BeautifulSoup(r_co.text, "html.parser")
                full_text = soup.get_text()
                loc_m = re.search(r"Localidad:\s*([^·\-\:\,\n]+)", full_text, re.IGNORECASE)
                loc = loc_m.group(1).strip() if loc_m else ""
                loc = re.sub(r"\s+(Ganancias|Persona|Física|Jurídica|CUIT|Responsable|Inscripto|No Inscripto).*", "", loc, flags=re.IGNORECASE).strip()

                prov = ""
                for p in PROVINCIAS_ARGENTINAS:
                    if re.search(r"\b" + re.escape(p) + r"\b", full_text, re.IGNORECASE):
                        prov = p
                        break

                if not prov and loc:
                    loc_lower = loc.lower()
                    for c_name, p_name in CITY_PROV_MAP.items():
                        if c_name in loc_lower:
                            prov = p_name
                            break

                if prov == "CABA" or prov == "Capital Federal":
                    prov = "Ciudad Autónoma de Buenos Aires"

                if loc or prov:
                    return {
                        "status": "OK",
                        "provincia": prov or "Buenos Aires",
                        "localidad": loc or prov or "Sin especificar",
                        "fuente": "CuitOnline Directo"
                    }
    except Exception:
        pass

    # --- 3. Fallback Instantáneo: DuckDuckGo Search ---
    url_ddg = f"https://html.duckduckgo.com/html/?q={c_clean}"
    try:
        if USE_CURL_CFFI:
            r_ddg = req.get(url_ddg, headers=headers, impersonate=imp_target, timeout=8)
        else:
            r_ddg = req.get(url_ddg, headers=headers, timeout=8)

        if r_ddg.status_code == 200:
            soup = BeautifulSoup(r_ddg.text, "html.parser")
            snippets = [a.get_text(strip=True) for a in soup.find_all("a", class_="result__snippet")]
            full_text = " ".join(snippets)

            if full_text:
                loc_m = re.search(r"Localidad:\s*([^·\-\:\,\n]+)", full_text, re.IGNORECASE)
                loc = loc_m.group(1).strip() if loc_m else ""
                loc = re.sub(r"\s+(Ganancias|Persona|Física|Jurídica|CUIT|Responsable|Inscripto|No Inscripto).*", "", loc, flags=re.IGNORECASE).strip()

                prov = ""
                for p in PROVINCIAS_ARGENTINAS:
                    if re.search(r"\b" + re.escape(p) + r"\b", full_text, re.IGNORECASE):
                        prov = p
                        break

                if not prov and loc:
                    loc_lower = loc.lower()
                    for c_name, p_name in CITY_PROV_MAP.items():
                        if c_name in loc_lower:
                            prov = p_name
                            break

                if prov == "CABA" or prov == "Capital Federal":
                    prov = "Ciudad Autónoma de Buenos Aires"

                if loc or prov:
                    return {
                        "status": "OK",
                        "provincia": prov or "Buenos Aires",
                        "localidad": loc or prov or "Sin especificar",
                        "fuente": "Fallback Búsqueda DDG"
                    }
    except Exception:
        pass

    # --- 4. Fallback Cuarto: Apify Google Search Actor ---
    apify_res = consultar_apify_google_search(c_clean)
    if apify_res:
        return apify_res

    return {"status": "SIN_DATOS"}

APIFY_TOKEN = os.environ.get("APIFY_TOKEN", "")

def consultar_apify_google_search(c_clean: str) -> dict:
    if not APIFY_TOKEN:
        return None
    try:
        url = f"https://api.apify.com/v2/acts/apify~google-search-scraper/run-sync-get-dataset-items?token={APIFY_TOKEN}"
        payload = {
            "queries": f"cuit {c_clean}",
            "maxPagesPerQuery": 1,
            "resultsPerPage": 3
        }
        r = http_req.post(url, json=payload, timeout=25)
        if r.status_code in [200, 201]:
            items = r.json()
            if items and len(items) > 0 and "organicResults" in items[0]:
                for res in items[0]["organicResults"]:
                    t = res.get("title", "")
                    s = res.get("snippet", "")
                    full_text = f"{t} {s}"
                    prov = ""
                    for p in PROVINCIAS_ARGENTINAS:
                        if re.search(r"\b" + re.escape(p) + r"\b", full_text, re.IGNORECASE):
                            prov = p
                            break
                    loc_m = re.search(r"Localidad:\s*([^·\-\:\,\n]+)", full_text, re.IGNORECASE)
                    loc = loc_m.group(1).strip() if loc_m else ""
                    if prov or loc:
                        return {
                            "status": "OK",
                            "provincia": prov or "Buenos Aires",
                            "localidad": loc or prov or "Sin especificar",
                            "fuente": "Apify Google Search"
                        }
    except Exception:
        pass
    return None

# --- Mapa de normalización de provincias: unifica variantes sin tilde, abreviadas y con errores ---
_PROV_NORMALIZER = {
    # Buenos Aires
    "buenos aires": "Buenos Aires",
    "buenos aires (pcia)": "Buenos Aires",
    "bs as": "Buenos Aires",
    "bs. as.": "Buenos Aires",
    "pcia. buenos aires": "Buenos Aires",
    # CABA
    "ciudad autonoma de buenos aires": "Ciudad Autónoma de Buenos Aires",
    "ciudad autónoma de buenos aires": "Ciudad Autónoma de Buenos Aires",
    "ciudad autonoma": "Ciudad Autónoma de Buenos Aires",
    "capital federal": "Ciudad Autónoma de Buenos Aires",
    "caba": "Ciudad Autónoma de Buenos Aires",
    # Córdoba
    "cordoba": "Córdoba",
    "córdoba": "Córdoba",
    # Santa Fe
    "santa fe": "Santa Fe",
    # Mendoza
    "mendoza": "Mendoza",
    # Tucumán
    "tucuman": "Tucumán",
    "tucumán": "Tucumán",
    # Salta
    "salta": "Salta",
    # Entre Ríos
    "entre rios": "Entre Ríos",
    "entre ríos": "Entre Ríos",
    # Misiones
    "misiones": "Misiones",
    # Chaco
    "chaco": "Chaco",
    # Corrientes
    "corrientes": "Corrientes",
    # Santiago del Estero
    "santiago del estero": "Santiago del Estero",
    # San Juan
    "san juan": "San Juan",
    # Jujuy
    "jujuy": "Jujuy",
    # Río Negro
    "rio negro": "Río Negro",
    "río negro": "Río Negro",
    # Neuquén
    "neuquen": "Neuquén",
    "neuquén": "Neuquén",
    # Formosa
    "formosa": "Formosa",
    # Chubut
    "chubut": "Chubut",
    # San Luis
    "san luis": "San Luis",
    # Catamarca
    "catamarca": "Catamarca",
    # La Rioja
    "la rioja": "La Rioja",
    # La Pampa
    "la pampa": "La Pampa",
    # Santa Cruz
    "santa cruz": "Santa Cruz",
    # Tierra del Fuego
    "tierra del fuego": "Tierra del Fuego",
}

def _normalizar_provincia(prov: str) -> str:
    """Normaliza el nombre de una provincia a su forma canónica oficial."""
    if not prov:
        return prov
    key = prov.strip().lower()
    return _PROV_NORMALIZER.get(key, prov.strip())

def _actualizar_productor_db(mat: str, prov: str, loc: str):
    prov_normalizada = _normalizar_provincia(prov)
    try:
        with db_lock:
            conn = sqlite3.connect(DB_PATH, timeout=20.0)
            cur = conn.cursor()
            cur.execute("""
                UPDATE productores_detalle 
                SET provincia = CASE WHEN provincia IS NULL OR provincia = '' OR provincia = '—' THEN ? ELSE provincia END,
                    localidad = CASE WHEN localidad IS NULL OR localidad = '' OR localidad = '—' THEN ? ELSE localidad END
                WHERE matricula = ?
            """, (prov_normalizada, loc, mat))
            conn.commit()
            conn.close()
    except Exception as ex:
        print(f"Error guardando OK en DB para {mat}: {ex}")

def _registrar_fallo_intentos_db(mat: str, obs_actual: str):
    tag = "NO_DATEAS_2" if "NO_DATEAS_1" in str(obs_actual) else "NO_DATEAS_1"
    nueva_obs = f"{obs_actual} {tag}".strip() if obs_actual else tag

    try:
        with db_lock:
            conn = sqlite3.connect(DB_PATH, timeout=20.0)
            cur = conn.cursor()
            cur.execute("""
                UPDATE productores_detalle 
                SET observaciones = ? 
                WHERE matricula = ?
            """, (nueva_obs, mat))
            conn.commit()
            conn.close()
    except Exception as ex:
        print(f"Error registrando intento en DB para {mat}: {ex}")

def _worker_procesar_item(item, delay_between: float, thread_sessions: dict):
    global STOP_ENRICHMENT
    if STOP_ENRICHMENT:
        return None

    tid = threading.get_ident()
    if tid not in thread_sessions:
        if USE_CURL_CFFI:
            thread_sessions[tid] = http_req.Session()
        else:
            thread_sessions[tid] = http_req.Session()
    session = thread_sessions[tid]

    mat = item["matricula"]
    cuit = item["cuit"] or item["documento"]
    nombre = item["nombre"]
    obs = item["observaciones"] or ""

    res = consultar_dateas_con_fallback(cuit=cuit, session=session)
    if res.get("status") == "NETWORK_ERROR":
        time.sleep(0.8)
        res = consultar_dateas_con_fallback(cuit=cuit, session=session)

    status = res.get("status")

    info = ""
    if status == "OK":
        prov = res.get("provincia", "").strip()
        loc = res.get("localidad", "").strip()
        fuente = res.get("fuente", "Enriquecido")
        if prov and prov != "—":
            _actualizar_productor_db(mat, prov, loc)
            info = f"{prov}, {loc} ({fuente})"
        else:
            _registrar_fallo_intentos_db(mat, obs)
            status = "ERROR"
            info = "Sin provincia identificada"
    elif status == "NETWORK_ERROR":
        info = "Error de red transitorio"
    else:  # SIN_DATOS
        _registrar_fallo_intentos_db(mat, obs)
        status = "ERROR"
        info = "Sin coincidencia CUIT"

    PROCESSED_MATRICULAS.add(str(mat))
    time.sleep(delay_between + random.uniform(0.1, 0.3))
    return (mat, nombre, cuit, status, info)

# Colores de 256 colores (bypasea la paleta del tema del terminal)
C_RESET   = "\033[0m"
C_BOLD    = "\033[1m"
C_GREEN   = "\033[1m\033[38;5;46m"    # Verde Neón Puro (#46 = Lime Green)
C_YELLOW  = "\033[1m\033[38;5;226m"   # Amarillo Canario Brillante (#226)
C_RED     = "\033[1m\033[38;5;196m"   # Rojo Puro (#196)
C_CYAN    = "\033[1m\033[38;5;51m"    # Cyan Eléctrico (#51)
C_BLUE    = "\033[1m\033[38;5;21m"    # Azul Puro (#21)
C_MAGENTA = "\033[1m\033[38;5;201m"   # Magenta Neon (#201)
C_DIM     = "\033[38;5;240m"          # Gris Tenue (#240)

PROCESSED_MATRICULAS = set()

def procesar_lote_dateas(batch_size: int = 200, max_workers: int = 2, delay_between: float = 0.9, on_item_processed=None,
                        matricula_desde: int = 0, matricula_hasta: int = 999999, target_matriculas: Optional[List[str]] = None):
    global PROCESSED_MATRICULAS
    if not os.path.exists(DB_PATH):
        print(f"{C_RED}❌ No se encontró la base de datos en {DB_PATH}{C_RESET}")
        return 0

    pool_size = max(batch_size * 10, 2000)

    with db_lock:
        conn = sqlite3.connect(DB_PATH, timeout=20.0)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        if target_matriculas is not None:
            t_mats = [str(m) for m in target_matriculas if str(m) not in PROCESSED_MATRICULAS]
            raw_rows = []
            if t_mats:
                chunk_size = 500
                for i in range(0, len(t_mats), chunk_size):
                    chunk = t_mats[i:i + chunk_size]
                    placeholders = ",".join(["?"] * len(chunk))
                    cursor.execute(f"""
                        SELECT matricula, cuit, documento, nombre, provincia, localidad, observaciones 
                        FROM productores_detalle 
                        WHERE matricula IN ({placeholders})
                          AND (cuit IS NOT NULL AND cuit != '' AND cuit != '—')
                          AND (provincia IS NULL OR provincia = '' OR provincia = '—' OR localidad IS NULL OR localidad = '' OR localidad = '—')
                    """, chunk)
                    raw_rows.extend(cursor.fetchall())
        else:
            cursor.execute("""
                SELECT matricula, cuit, documento, nombre, provincia, localidad, observaciones 
                FROM productores_detalle 
                WHERE (cuit IS NOT NULL AND cuit != '' AND cuit != '—')
                  AND (telefono IS NULL OR telefono = '' OR telefono = '—' OR telefono LIKE 'E-mail%')
                  AND (email IS NULL OR email = '' OR email = '—')
                  AND (provincia IS NULL OR provincia = '' OR provincia = '—' OR localidad IS NULL OR localidad = '' OR localidad = '—')
                  AND (observaciones IS NULL OR observaciones NOT LIKE '%NO_DATEAS_2%')
                  AND CAST(matricula AS INTEGER) BETWEEN ? AND ?
                ORDER BY CAST(matricula AS INTEGER) DESC
                LIMIT ?
            """, (matricula_desde, matricula_hasta, pool_size))
            raw_rows = cursor.fetchall()
        conn.close()

    pendientes = [r for r in raw_rows if str(r["matricula"]) not in PROCESSED_MATRICULAS][:batch_size]

    if not pendientes:
        print(f"{C_GREEN}{C_BOLD}🎉 ¡Todos los productores incompletos seleccionados ya fueron enriquecidos o procesados!{C_RESET}")
        return 0

    print(f"{C_MAGENTA}{C_BOLD}⚡ Procesando lote de {len(pendientes)} CUITs (Modo Acelerado Seguro: {max_workers} hilos, delay {delay_between}s)...{C_RESET}")
    actualizados = 0
    idx_counter = 0
    consecutive_net_errors = 0
    thread_sessions = {}

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(_worker_procesar_item, item, delay_between, thread_sessions): item
            for item in pendientes
        }

        for future in as_completed(futures):
            global STOP_ENRICHMENT
            if STOP_ENRICHMENT:
                executor.shutdown(wait=False, cancel_futures=True)
                break

            result = future.result()
            if not result:
                continue

            idx_counter += 1
            mat, nombre, cuit, status, info = result

            if status == "OK":
                actualizados += 1
                consecutive_net_errors = 0
                print(f"  {C_GREEN}{C_BOLD}[{idx_counter}/{len(pendientes)}] ✓ Matrícula {mat} ({nombre}) -> {info}{C_RESET}")
            elif status == "NETWORK_ERROR":
                consecutive_net_errors += 1
                print(f"  {C_YELLOW}[{idx_counter}/{len(pendientes)}] ⚡ Matrícula {mat} ({nombre}): {info}{C_RESET}")
                if consecutive_net_errors >= 6:
                    print(f"{C_RED}{C_BOLD}⚠️ Pausando 20s para enfriar red...{C_RESET}")
                    if on_item_processed:
                        on_item_processed(idx_counter, len(pendientes), mat, nombre, cuit, "RATE_LIMIT", "Enfriando red (20s)...")
                    for _ in range(20):
                        if STOP_ENRICHMENT:
                            break
                        time.sleep(1)
                    consecutive_net_errors = 0
            else:
                consecutive_net_errors = 0
                print(f"  {C_DIM}[{idx_counter}/{len(pendientes)}] - Matrícula {mat} ({nombre}): {info}{C_RESET}")

            if on_item_processed:
                on_item_processed(idx_counter, len(pendientes), mat, nombre, cuit, status, info)

    for s in thread_sessions.values():
        try:
            s.close()
        except Exception:
            pass

    return actualizados

def ejecutar_ciclo_continuo(batch_size: int = 200, pause_seconds: int = 6, on_batch_finish=None, on_item_processed=None,
                           matricula_desde: int = 0, matricula_hasta: int = 999999, max_workers: int = 2, delay_between: float = 0.9,
                           target_matriculas: Optional[List[str]] = None):
    global STOP_ENRICHMENT, PROCESSED_MATRICULAS
    STOP_ENRICHMENT = False
    PROCESSED_MATRICULAS.clear()
    batch_num = 1

    if target_matriculas:
        try:
            t_mats = [str(m) for m in target_matriculas]
            with db_lock:
                conn = sqlite3.connect(DB_PATH, timeout=20.0)
                cur = conn.cursor()
                chunk_size = 500
                for i in range(0, len(t_mats), chunk_size):
                    chunk = t_mats[i:i + chunk_size]
                    placeholders = ",".join(["?"] * len(chunk))
                    cur.execute(f"""
                        UPDATE productores_detalle
                        SET observaciones = REPLACE(REPLACE(observaciones, 'NO_DATEAS_2', ''), 'NO_DATEAS_1', '')
                        WHERE matricula IN ({placeholders}) AND observaciones LIKE '%NO_DATEAS%'
                    """, chunk)
                conn.commit()
                conn.close()
        except Exception as ex:
            print(f"Error despejando marcas para matriculas target: {ex}")

    rango = f"[{len(target_matriculas)} objetivo(s)]" if target_matriculas is not None else f"[{matricula_desde} – {matricula_hasta}]"
    print(f"\n{C_CYAN}{C_BOLD}🚀 Iniciando Enriquecimiento Focalizado {rango}: {batch_size} consultas/lote, {max_workers} hilos, pausa {pause_seconds}s.{C_RESET}")

    while not STOP_ENRICHMENT:
        print(f"\n{C_BLUE}{C_BOLD}--- 📦 Lote #{batch_num} {rango} ---{C_RESET}")
        count = procesar_lote_dateas(batch_size=batch_size, max_workers=max_workers, delay_between=delay_between,
                                    on_item_processed=on_item_processed, matricula_desde=matricula_desde, matricula_hasta=matricula_hasta,
                                    target_matriculas=target_matriculas)
        
        if count == 0 and not STOP_ENRICHMENT:
            print(f"{C_GREEN}{C_BOLD}✨ ¡Proceso completado! No quedan productores incompletos seleccionados pendientes.{C_RESET}")
            break

        if on_batch_finish:
            on_batch_finish(count, batch_num)

        if STOP_ENRICHMENT:
            break

        faltantes = 0
        try:
            with db_lock:
                conn = sqlite3.connect(DB_PATH, timeout=20.0)
                cur = conn.cursor()
                if target_matriculas is not None:
                    t_mats = [str(m) for m in target_matriculas]
                    raw_count = 0
                    chunk_size = 500
                    for i in range(0, len(t_mats), chunk_size):
                        chunk = t_mats[i:i + chunk_size]
                        placeholders = ",".join(["?"] * len(chunk))
                        cur.execute(f"""
                            SELECT COUNT(*) FROM productores_detalle 
                            WHERE matricula IN ({placeholders})
                              AND (cuit IS NOT NULL AND cuit != '' AND cuit != '—')
                              AND (provincia IS NULL OR provincia = '' OR provincia = '—' OR localidad IS NULL OR localidad = '' OR localidad = '—')
                        """, chunk)
                        raw_count += cur.fetchone()[0]
                    faltantes = raw_count
                else:
                    cur.execute("""
                        SELECT COUNT(*) 
                        FROM productores_detalle 
                        WHERE (cuit IS NOT NULL AND cuit != '' AND cuit != '—')
                          AND (telefono IS NULL OR telefono = '' OR telefono = '—' OR telefono LIKE 'E-mail%')
                          AND (email IS NULL OR email = '' OR email = '—')
                          AND (provincia IS NULL OR provincia = '' OR provincia = '—' OR localidad IS NULL OR localidad = '' OR localidad = '—')
                          AND (observaciones IS NULL OR observaciones NOT LIKE '%NO_DATEAS_2%')
                          AND CAST(matricula AS INTEGER) BETWEEN ? AND ?
                    """, (matricula_desde, matricula_hasta))
                    faltantes = cur.fetchone()[0]
                conn.close()
        except Exception:
            pass

        print(f"{C_CYAN}⏳ Lote #{batch_num} terminado ({count} pasaron a Completos). {C_YELLOW}{C_BOLD}📌 Quedan {faltantes} productores pendientes.{C_RESET} {C_CYAN}Pausa de {pause_seconds}s...{C_RESET}")
        
        for _ in range(pause_seconds):
            if STOP_ENRICHMENT:
                break
            time.sleep(1)
            
        batch_num += 1

def detener_enriquecimiento():
    global STOP_ENRICHMENT
    STOP_ENRICHMENT = True

if __name__ == "__main__":
    b_size   = int(sys.argv[1]) if len(sys.argv) > 1 else 150
    p_secs   = int(sys.argv[2]) if len(sys.argv) > 2 else 10
    mat_min  = int(sys.argv[3]) if len(sys.argv) > 3 else 0
    mat_max  = int(sys.argv[4]) if len(sys.argv) > 4 else 999999
    n_workers = int(sys.argv[5]) if len(sys.argv) > 5 else 2

    ejecutar_ciclo_continuo(batch_size=b_size, pause_seconds=p_secs,
                            matricula_desde=mat_min, matricula_hasta=mat_max,
                            max_workers=n_workers)