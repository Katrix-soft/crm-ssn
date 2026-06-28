"""
api_client.py
Cliente de comunicación HTTP/HTTPS para interactuar con la API REST de Katrix ERP,
incluyendo gestión de sesión (JWT) y validación de licencia por huella de hardware.
"""
import os
import sys
import json
import hashlib
import socket
import uuid
import platform
import requests
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

# Configuración por defecto
CONFIG_FILENAME = "licencia_config.json"


def obtener_url_api() -> str:
    """
    Obtiene la URL de la API del archivo local config_api.json o de variables de entorno.
    """
    # Intentar leer desde config_api.json en el directorio de la app
    try:
        if getattr(sys, "frozen", False):
            base = os.path.dirname(sys.executable)
        else:
            base = os.path.dirname(os.path.abspath(__file__))
        config_file = os.path.join(base, "config_api.json")
        if os.path.exists(config_file):
            with open(config_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                url = data.get("api_url")
                if url:
                    return url.rstrip("/")
    except Exception:
        pass
    
    # Fallback a variable de entorno o localhost
    return os.environ.get("KATRIX_API_URL", "http://localhost:8000").rstrip("/")


DEFAULT_API_URL = obtener_url_api()


def _get_config_dir() -> str:
    """Devuelve la carpeta de datos del usuario según el entorno."""
    if platform.system() == "Windows":
        data_dir = os.path.join(os.getenv("APPDATA", os.path.expanduser("~")), "KatrixBroker", "data")
    else:
        data_dir = os.path.join(os.path.expanduser("~"), ".katrixbroker", "data")
    os.makedirs(data_dir, exist_ok=True)
    return data_dir


def _get_config_path() -> str:
    return os.path.join(_get_config_dir(), CONFIG_FILENAME)


def obtener_fingerprint() -> str:
    """
    Genera un identificador único y estable de hardware para el equipo actual.
    Combina SO, nombre del host, procesador y dirección MAC física.
    """
    try:
        sys_info = f"{platform.system()}-{platform.machine()}-{platform.processor()}-{socket.gethostname()}-{uuid.getnode()}"
        return hashlib.sha256(sys_info.encode("utf-8")).hexdigest()[:16].upper()
    except Exception:
        # Fallback si falla la recolección
        return "FALLBACK-HW-FING"


def _get_encryption_key() -> bytes:
    """Deriva una llave criptográfica AES usando la huella del hardware local."""
    fingerprint = obtener_fingerprint()
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=b"katrix-secure-salt-2026",
        iterations=100000,
    )
    return base64.urlsafe_b64encode(kdf.derive(fingerprint.encode("utf-8")))


class APIClient:
    def __init__(self, base_url: str = DEFAULT_API_URL):
        self.base_url = base_url.rstrip("/")
        self.token: Optional[str] = None
        self.username: Optional[str] = None
        self.role: Optional[str] = None
        self.user_id: Optional[int] = None
        self.license_key: Optional[str] = None
        
        # Intentar cargar licencia guardada localmente
        self._load_local_license()

    def _get_headers(self) -> Dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers

    # ─────────────────────────────────────────────────────────────────────────
    # Gestión de Licencia (Validación de Software)
    # ─────────────────────────────────────────────────────────────────────────

    def _load_local_license(self):
        """Carga y desencripta los datos de licencia de la configuración local."""
        path = _get_config_path()
        if os.path.exists(path):
            try:
                with open(path, "rb") as f:
                    encrypted_data = f.read()
                f_cipher = Fernet(_get_encryption_key())
                decrypted_data = f_cipher.decrypt(encrypted_data)
                data = json.loads(decrypted_data.decode("utf-8"))
                self.license_key = data.get("license_key")
            except Exception:
                self.license_key = None

    def save_local_license(self, license_key: str):
        """Guarda la licencia localmente encriptada usando la huella del equipo."""
        path = _get_config_path()
        self.license_key = license_key.strip().upper()
        try:
            data_bytes = json.dumps({"license_key": self.license_key}).encode("utf-8")
            f_cipher = Fernet(_get_encryption_key())
            encrypted_data = f_cipher.encrypt(data_bytes)
            with open(path, "wb") as f:
                f.write(encrypted_data)
        except Exception as e:
            print(f"Error al guardar configuración de licencia cifrada: {e}")

    def remove_local_license(self):
        """Elimina el registro de licencia local (desactivación)."""
        path = _get_config_path()
        if os.path.exists(path):
            try:
                os.remove(path)
            except Exception:
                pass
        self.license_key = None

    def validar_licencia_online(self, license_key: str, email_cliente: str = "") -> Tuple[bool, str]:
        """
        Valida la licencia contra el servidor usando la huella digital local.
        """
        fingerprint = obtener_fingerprint()
        
        # Obtener información súper detallada del sistema operativo y hardware
        import getpass
        import json
        hostname = socket.gethostname()
        
        try:
            usuario_so = getpass.getuser()
        except Exception:
            usuario_so = "desconocido"
            
        os_name = platform.system()
        os_release = platform.release()
        os_version = platform.version()
        machine = platform.machine()
        processor = platform.processor() or "N/A"
        
        if os_name == "Darwin":
            os_name = "macOS"
            
        detalle_dispositivo = {
            "usuario": usuario_so,
            "hostname": hostname,
            "sistema_operativo": f"{os_name} {os_release}",
            "so_version": os_version,
            "arquitectura": machine,
            "procesador": processor
        }
        
        dispositivo_nombre = json.dumps(detalle_dispositivo, ensure_ascii=False)
        
        url = f"{self.base_url}/licencias/validar"
        payload = {
            "clave": license_key.strip().upper(),
            "dispositivo_id": fingerprint,
            "dispositivo_nombre": dispositivo_nombre,
            "email_cliente": email_cliente.strip()
        }
        try:
            response = requests.post(url, json=payload, timeout=10)
            if response.status_code == 200:
                res_data = response.json()
                if res_data.get("valid"):
                    self.save_local_license(license_key)
                    return True, f"Licencia válida para: {res_data.get('cliente')}"
                else:
                    return False, res_data.get("message", "Licencia inválida")
            else:
                return False, f"Error del servidor de licencias (HTTP {response.status_code})"
        except requests.RequestException as e:
            # Si el servidor no está disponible y ya hay una licencia guardada, permitir "modo offline" temporal
            if self.license_key == license_key.strip().upper():
                return True, "Licencia validada localmente (Modo Offline)"
            return False, f"No se pudo conectar al servidor de licencias: {e}"

    # ─────────────────────────────────────────────────────────────────────────
    # Autenticación de Usuario (Login y JWT)
    # ─────────────────────────────────────────────────────────────────────────

    def login(self, username_or_email: str, password: str) -> Tuple[bool, str]:
        """Inicia sesión y almacena el token JWT."""
        url = f"{self.base_url}/auth/login"
        payload = {
            "username": username_or_email,
            "password": password
        }
        try:
            response = requests.post(url, data=payload, timeout=10)
            if response.status_code == 200:
                data = response.json()
                self.token = data.get("access_token")
                # Obtener detalles del perfil
                return self.obtener_perfil()
            elif response.status_code == 401:
                return False, "Usuario o contraseña incorrectos"
            elif response.status_code == 403:
                return False, response.json().get("detail", "Cuenta bloqueada o inactiva")
            else:
                return False, f"Error de autenticación (HTTP {response.status_code})"
        except requests.RequestException as e:
            return False, f"Error de conexión con el servidor: {e}"

    def obtener_perfil(self) -> Tuple[bool, str]:
        """Obtiene datos del usuario logueado usando el token actual."""
        if not self.token:
            return False, "No hay sesión activa"
        url = f"{self.base_url}/auth/me"
        try:
            response = requests.get(url, headers=self._get_headers(), timeout=10)
            if response.status_code == 200:
                data = response.json()
                self.username = data.get("usuario")
                self.role = data.get("rol")
                self.user_id = data.get("id")
                return True, f"Sesión activa: {self.username} ({self.role})"
            else:
                self.token = None
                return False, "Sesión expirada o inválida"
        except requests.RequestException as e:
            return False, f"Error al verificar perfil: {e}"

    # ─────────────────────────────────────────────────────────────────────────
    # CRUD PAS y Sincronización Remota (Opcional si usa el backend centralizado)
    # ─────────────────────────────────────────────────────────────────────────

    def obtener_todos_remoto(self) -> List[Dict[str, Any]]:
        """Descarga todos los productores accesibles según el rol del usuario."""
        url = f"{self.base_url}/pas/"
        try:
            response = requests.get(url, headers=self._get_headers(), timeout=15)
            if response.status_code == 200:
                return response.json()
            return []
        except Exception:
            return []

    def actualizar_companias_remoto(self, matricula: str, companias: str) -> bool:
        """Actualiza las compañías del PAS en el servidor remoto."""
        url = f"{self.base_url}/pas/{matricula}/companias"
        try:
            response = requests.put(
                url, 
                json={"companias": companias}, 
                headers=self._get_headers(), 
                timeout=10
            )
            return response.status_code == 200
        except Exception:
            return False
