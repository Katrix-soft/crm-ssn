import asyncio
import sqlite3
import re
from typing import List, Dict, Set
from mercantil_andina import MercantilAndinaClient
import ssn_test  # Para importar DB_PATH y toggle_en_organizacion

def clean_name(name: str) -> str:
    """Limpia sufijos comunes y normaliza a mayúsculas."""
    name = name.upper()
    name = re.sub(r'[,.\-]', ' ', name)
    # Quitar sufijos conocidos
    name = name.replace(" VIDA", "").replace(" CTA 1", "").replace(" CTA 2", "")
    name = name.replace(" Y ASOCIADOS S A", "").replace(" Y ASOCIADOS 1", "").replace(" Y ASOCIADOS 2", "").replace(" Y ASOCIADOS", "")
    return name.strip()

def normalize_name_tokens(name: str) -> Set[str]:
    """Convierte el nombre en un set de palabras clave."""
    if not name:
        return set()
    cleaned = clean_name(name)
    words = set(w for w in cleaned.split() if len(w) > 2)
    return words

def match_producers(mercantil_name: str, local_producers: List[Dict]) -> str:
    """Busca coincidencia difusa (fuzzy) o por prefijo entre las palabras del nombre."""
    m_tokens = normalize_name_tokens(mercantil_name)
    if not m_tokens:
        return None
    
    best_match_matricula = None
    best_match_score = 0
    
    for lp in local_producers:
        lp_tokens = lp["tokens"]
        if not lp_tokens:
            continue
        
        # Algoritmo de prefijo (ej: ELIS matchea con ELISA)
        common_count = 0
        for m in m_tokens:
            for l in lp_tokens:
                if m == l or m.startswith(l) or l.startswith(m):
                    common_count += 1
                    break # Matcheó esta palabra de Mercantil con alguna local
                    
        # Calcular score sobre el total de palabras importantes
        score = common_count / max(len(m_tokens), len(lp_tokens))
        
        # Score más tolerante (0.65 permite fallar 1 palabra si hay 3)
        if score >= 0.65:
            if score > best_match_score:
                best_match_score = score
                best_match_matricula = lp["matricula"]
                
                if score == 1.0:
                    break
                    
    return best_match_matricula

def scrape_and_save(nombre: str) -> bool:
    """Ejecuta el scraper de SSN por nombre y guarda el resultado si lo encuentra."""
    print(f"      [SSN SCRAPER] Buscando '{nombre}' en la SSN...")
    try:
        html = ssn_test.buscar_en_ssn(nombre, "NOMBRE")
        if html:
            resultado = ssn_test.parsear_resultado(html)
            if resultado and resultado.get("matricula"):
                print(f"      [SSN SCRAPER] ¡Encontrado! Matrícula asignada: {resultado['matricula']}")
                ssn_test.guardar_en_db(resultado)
                return True
            else:
                print("      [SSN SCRAPER] No se pudo parsear ningún resultado válido o hay múltiples coincidencias.")
        else:
            print("      [SSN SCRAPER] SSN no devolvió resultados.")
    except Exception as e:
        print(f"      [SSN SCRAPER] Error durante la consulta: {e}")
    return False

def get_local_producers() -> List[Dict]:
    conn = sqlite3.connect(ssn_test.DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT matricula, nombre, companias FROM productores_detalle")
    rows = cursor.fetchall()
    conn.close()
    
    return [
        {
            "matricula": str(r[0]),
            "nombre": r[1],
            "companias": r[2] or "",
            "tokens": normalize_name_tokens(r[1])
        }
        for r in rows if r[1]
    ]

async def run_sync():
    print("Iniciando sincronización inteligente de productores con Mercantil Andina...")
    client = MercantilAndinaClient()
    
    # 1. Obtener productores de Mercantil Andina
    print("1. Obteniendo productores de Mercantil Andina...")
    try:
        response = await client._request("GET", "/productores/v1/")
        if isinstance(response, dict) and "datos" in response:
            productores_mercantil = response["datos"]
            print(f"   ✓ {len(productores_mercantil)} productores obtenidos de la API.")
        else:
            print("   ✗ Error: Estructura de respuesta inesperada.")
            return
    except Exception as e:
        print(f"   ✗ Error al conectar con Mercantil: {e}")
        return

    # 2. Cargar productores locales
    print("2. Cargando base de datos local (Buscador_SSN.db)...")
    local_producers = get_local_producers()
    print(f"   ✓ {len(local_producers)} productores locales cargados.")

    # 3. Matcheo y Actualización
    print("3. Matcheando productores y actualizando estado 'En Organización'...")
    matches_count = 0
    not_found_count = 0
    scraped_count = 0
    attempted_scrapes = set()
    
    for prod_m in productores_mercantil:
        nombre_m = prod_m.get("nombre", "")
        cuenta_m = prod_m.get("cuenta")
        
        matricula_match = match_producers(nombre_m, local_producers)
        
        if not matricula_match:
            nombre_limpio = clean_name(nombre_m).replace(" Y ASOCIADOS", "").strip()
            # Tomamos solo las 2 o 3 primeras palabras para asegurar que SSN lo encuentre (Apellido Nombre)
            nombre_corto = " ".join(nombre_limpio.split()[:3])
            
            if nombre_corto not in attempted_scrapes:
                print(f"   [SIN MATCH] '{nombre_m}'. Intentando auto-scrape en SSN para '{nombre_corto}'...")
                attempted_scrapes.add(nombre_corto)
                exito_scrape = scrape_and_save(nombre_corto)
                if exito_scrape:
                    scraped_count += 1
                    # Recargamos la BD local para poder matchearlo
                    local_producers = get_local_producers()
                    matricula_match = match_producers(nombre_m, local_producers)
            else:
                print(f"   [OMITIDO] Ya intentamos scrapear '{nombre_corto}' en esta sesión. Saltando...")
        
        if matricula_match:
            # Encontrado o Scrapeado con éxito
            try:
                ssn_test.toggle_en_organizacion(matricula_match, True, "sync_mercantil")
                
                # Actualizar las compañías con el número de cuenta
                prod_local = next((p for p in local_producers if p["matricula"] == matricula_match), None)
                if prod_local:
                    companias_actuales = prod_local.get("companias") or ""
                    nueva_compania = f"Mercantil Andina (Cta: {cuenta_m})"
                    
                    if nueva_compania not in companias_actuales:
                        if companias_actuales:
                            comp_final = f"{companias_actuales} | {nueva_compania}"
                        else:
                            comp_final = nueva_compania
                        ssn_test.actualizar_companias(matricula_match, comp_final, "sync_mercantil")

                print(f"   [MATCH] {nombre_m} -> Matrícula: {matricula_match} | Compañía: Mercantil (Cta: {cuenta_m})")
                matches_count += 1
            except Exception as e:
                print(f"   [ERROR BD] Falló actualización para {nombre_m}: {e}")
        else:
            print(f"   [FALLO DEFINITIVO] No se encontró ni pudo scrapear a: {nombre_m} (Cuenta: {cuenta_m})")
            not_found_count += 1

    print("\n=========================================")
    print("        RESUMEN DE SINCRONIZACIÓN        ")
    print("=========================================")
    print(f"Total Mercantil:       {len(productores_mercantil)}")
    print(f"Matcheados exitosos:   {matches_count} (ahora marcados como 'En Organización')")
    print(f"Nuevos scrapeados SSN: {scraped_count}")
    print(f"No encontrados:        {not_found_count}")
    print("=========================================\n")
    print("Ya podés abrir el CRM y verificar el buscador. Los matcheados aparecerán en la organización.")

if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    asyncio.run(run_sync())
