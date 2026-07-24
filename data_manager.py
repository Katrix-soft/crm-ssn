"""
data_manager.py
Maneja la carga del CSV local (cache) y la descarga en background del CSV remoto.
"""
import csv
import os
import sys
import threading
import time
import urllib.request
import urllib.error
from datetime import datetime
from typing import Callable, Dict, List, Any, Optional

from utils import COL_MATRICULA, COL_TIPO_ID, COL_ID, COL_NOMBRE, COL_RAMO

# ---------------------------------------------------------------------------
# Configuración
# ---------------------------------------------------------------------------
CSV_URL = (
    "https://datosabiertos.ssn.gob.ar/dataset/"
    "be4927ba-6b6d-4cee-b33e-5319b33b15b8/resource/"
    "07de24f8-4191-497e-a0da-da83cf5eb5d9/download/productores-asesores.csv"
)
CSV_FILENAME = "productores-asesores.csv"

# Columnas mínimas requeridas para considerar el CSV válido
REQUIRED_COLUMNS = {COL_MATRICULA, COL_ID, COL_NOMBRE, COL_RAMO}

# Timeout de descarga (segundos)
DOWNLOAD_TIMEOUT = 30


def _get_data_dir() -> str:
    """
    Devuelve el directorio donde se guarda el cache CSV.
    - Si corre como .exe de PyInstaller: junto al ejecutable
    - Si corre en dev: carpeta ./data/ relativa al script
    """
    if getattr(sys, "frozen", False):
        # Ejecutable PyInstaller: guardar junto al .exe
        base = os.path.dirname(sys.executable)
    else:
        base = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(base, "data")
    os.makedirs(data_dir, exist_ok=True)
    return data_dir


def _get_cache_path() -> str:
    return os.path.join(_get_data_dir(), CSV_FILENAME)


def _parse_csv(filepath: str) -> List[Dict[str, Any]]:
    """
    Lee y parsea el CSV. Devuelve lista de dicts.
    Lanza ValueError si las columnas requeridas no están presentes.
    """
    records = []
    with open(filepath, encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        if reader.fieldnames is None:
            raise ValueError("El CSV no tiene encabezados.")
        
        actual_cols = set(reader.fieldnames)
        missing = REQUIRED_COLUMNS - actual_cols
        if missing:
            raise ValueError(
                f"El CSV remoto cambió su estructura. "
                f"Columnas faltantes: {', '.join(missing)}"
            )
        
        for row in reader:
            # Limpiar espacios extra en los valores
            clean = {k: (v.strip() if v else "") for k, v in row.items()}
            records.append(clean)
    
    return records


def get_cache_date() -> Optional[str]:
    """Retorna la fecha de modificación del CSV cacheado, o None si no existe."""
    path = _get_cache_path()
    if not os.path.exists(path):
        return None
    mtime = os.path.getmtime(path)
    return datetime.fromtimestamp(mtime).strftime("%d/%m/%Y %H:%M")


def has_cache() -> bool:
    """True si existe un CSV cacheado."""
    return os.path.exists(_get_cache_path())


def load_local() -> List[Dict[str, Any]]:
    """
    Carga el CSV local (cache). Devuelve lista de registros.
    Lanza FileNotFoundError si no existe, ValueError si estructura inválida.
    """
    path = _get_cache_path()
    if not os.path.exists(path):
        raise FileNotFoundError(f"No existe cache en: {path}")
    return _parse_csv(path)


def _download_to_temp(url: str, dest_path: str) -> str:
    """
    Descarga la URL a un archivo temporal en el mismo directorio que dest_path.
    Retorna el path del archivo temporal.
    """
    tmp_path = dest_path + ".tmp"
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": (
                "Mozilla/5.0 (BuscadorSSN/1.0; "
                "+https://github.com/ssn-buscador)"
            )
        },
    )
    with urllib.request.urlopen(req, timeout=DOWNLOAD_TIMEOUT) as resp:
        with open(tmp_path, "wb") as f:
            while True:
                chunk = resp.read(65536)
                if not chunk:
                    break
                f.write(chunk)
    return tmp_path


def _files_differ(path_a: str, path_b: str, compare_bytes: int = 4096) -> bool:
    """Compara los primeros N bytes de dos archivos para detectar cambios rápido."""
    if not os.path.exists(path_a) or not os.path.exists(path_b):
        return True
    size_a = os.path.getsize(path_a)
    size_b = os.path.getsize(path_b)
    if size_a != size_b:
        return True
    # Comparar primeros bytes
    with open(path_a, "rb") as fa, open(path_b, "rb") as fb:
        return fa.read(compare_bytes) != fb.read(compare_bytes)


class DataManager:
    """
    Gestiona el ciclo de vida de los datos:
    - Carga local rápida al arrancar
    - Descarga en background
    - Notificaciones vía callbacks
    """

    def __init__(self):
        self.records: List[Dict[str, Any]] = []
        self.cache_date: Optional[str] = None
        self._bg_thread: Optional[threading.Thread] = None

        # Callbacks (llamados desde el hilo background → usar page.update())
        self.on_load_success: Optional[Callable[[List[Dict[str, Any]]], None]] = None
        self.on_load_error: Optional[Callable[[str], None]] = None
        self.on_update_available: Optional[Callable[[str], None]] = None
        self.on_update_error: Optional[Callable[[str], None]] = None

    def initialize(self, user_id: int = None, role: str = None, regional_only: bool = False, api_client: Any = None):
        """
        Punto de entrada principal:
        Carga registros de la base de datos SQLite con soporte para roles.
        Si la DB local está vacía y se dispone de conexión a la API, sincroniza los registros automáticamente.
        """
        try:
            from ssn_test import obtener_todos_db, guardar_pas_masivos
            db_records = obtener_todos_db(user_id=user_id, role=role, regional_only=regional_only)
            
            # Sincronizar desde la API remota si la DB local está vacía
            if not db_records and api_client:
                remotos = api_client.obtener_todos_remoto()
                if remotos:
                    guardar_pas_masivos(remotos)
                    db_records = obtener_todos_db(user_id=user_id, role=role, regional_only=regional_only)

            self.records = []

            for db_rec in db_records:
                mat = db_rec.get("matricula", "").strip()
                if mat:
                    cuit = db_rec.get("cuit") or db_rec.get("documento") or ""
                    cuit_clean = cuit.replace("-", "").strip()
                    tipo_id = "CUIT" if len(cuit_clean) == 11 else "DNI"
                    
                    rec = {
                        COL_MATRICULA: mat,
                        COL_NOMBRE: db_rec.get("nombre", ""),
                        COL_ID: cuit,
                        COL_TIPO_ID: tipo_id,
                        COL_RAMO: db_rec.get("ramo", "Patrimoniales y Vida"),
                        "provincia": db_rec.get("provincia", "—"),
                        "telefono": db_rec.get("telefono", "—"),
                        "email": db_rec.get("email", "—"),
                        "resolucion": db_rec.get("resolucion", "—"),
                        "fecha_resolucion": db_rec.get("fecha_resolucion", "—"),
                        "domicilio": db_rec.get("domicilio", "—"),
                        "localidad": db_rec.get("localidad", "—"),
                        "cod_postal": db_rec.get("cod_postal", "—"),
                        "estado_contacto": db_rec.get("estado_contacto") or "Sin contactar",
                        "companias": db_rec.get("companias", ""),
                        "sociedades": db_rec.get("sociedades", ""),
                    }
                    self.records.append(rec)
            
            self.cache_date = "Datos de Broker (Excel)"
            if self.on_load_success:
                self.on_load_success(self.records)
        except Exception as e:
            if self.on_load_error:
                self.on_load_error(str(e))
