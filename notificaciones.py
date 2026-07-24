"""
notificaciones.py
Módulo de notificaciones de reuniones y alertas multi-plataforma (Windows, Linux, macOS).
"""
import os
import platform
import subprocess
import shutil
from datetime import datetime
from typing import List, Dict, Any, Tuple

def enviar_notificacion_sistema(titulo: str, mensaje: str) -> bool:
    """
    Envía una notificación nativa del sistema operativo (Windows, Linux, macOS).
    Retorna True si la notificación pudo enviarse exitosamente.
    """
    system_name = platform.system()
    
    # --- LINUX ---
    if system_name == "Linux":
        try:
            if shutil.which("notify-send"):
                subprocess.run(["notify-send", "-i", "appointment-soon", titulo, mensaje], check=False)
                return True
            elif shutil.which("zenity"):
                subprocess.run(["zenity", "--notification", f"--text={titulo}: {mensaje}"], check=False)
                return True
            elif shutil.which("kdialog"):
                subprocess.run(["kdialog", "--passivepopup", f"{titulo}\n{mensaje}", "5"], check=False)
                return True
        except Exception as ex:
            print(f"[NOTIF LINUX ERROR] {ex}")

    # --- WINDOWS ---
    elif system_name == "Windows":
        try:
            # Script PowerShell seguro para notificación en globo / Toast nativo de Windows
            titulo_clean = titulo.replace('"', "'")
            mensaje_clean = mensaje.replace('"', "'")
            ps_script = f'''
            [void] [System.Reflection.Assembly]::LoadWithPartialName("System.Windows.Forms")
            $objNotifyIcon = New-Object System.Windows.Forms.NotifyIcon
            $objNotifyIcon.Icon = [System.Drawing.SystemIcons]::Information
            $objNotifyIcon.BalloonTipIcon = "Info"
            $objNotifyIcon.BalloonTipTitle = "{titulo_clean}"
            $objNotifyIcon.BalloonTipText = "{mensaje_clean}"
            $objNotifyIcon.Visible = $True
            $objNotifyIcon.ShowBalloonTip(6000)
            '''
            creation_flags = getattr(subprocess, 'CREATE_NO_WINDOW', 0)
            subprocess.run(["powershell", "-Command", ps_script], check=False, creationflags=creation_flags)
            return True
        except Exception as ex:
            print(f"[NOTIF WINDOWS ERROR] {ex}")

    # --- MACOS ---
    elif system_name == "Darwin":
        try:
            titulo_clean = titulo.replace('"', "'")
            mensaje_clean = mensaje.replace('"', "'")
            apple_script = f'display notification "{mensaje_clean}" with title "{titulo_clean}"'
            subprocess.run(["osascript", "-e", apple_script], check=False)
            return True
        except Exception as ex:
            print(f"[NOTIF MACOS ERROR] {ex}")

    return False


def obtener_resumen_reuniones() -> Dict[str, Any]:
    """
    Consulta las reuniones y visitas desde la base de datos SQLite
    y clasifica las pendientes para hoy, próximas y vencidas.
    """
    try:
        import ssn_test
        mes_actual = datetime.now().strftime("%Y-%m")
        hoy_str = datetime.now().strftime("%Y-%m-%d")
        
        visitas = ssn_test.obtener_visitas(mes_actual)
        
        reuniones_hoy = []
        reuniones_pendientes = []
        
        for v in visitas:
            if v.get("estado", "").lower() == "pendiente":
                reuniones_pendientes.append(v)
                v_fecha = str(v.get("fecha") or "")
                
                # Si coincide con la fecha de hoy o la visita está agendada para hoy
                if v_fecha.startswith(hoy_str) or not v_fecha or v_fecha == "—":
                    reuniones_hoy.append(v)
                    
        return {
            "total_pendientes": len(reuniones_pendientes),
            "total_hoy": len(reuniones_hoy),
            "reuniones_hoy": reuniones_hoy,
            "reuniones_pendientes": reuniones_pendientes,
        }
    except Exception as ex:
        print(f"[ERROR obtener_resumen_reuniones] {ex}")
        return {
            "total_pendientes": 0,
            "total_hoy": 0,
            "reuniones_hoy": [],
            "reuniones_pendientes": [],
        }
