"""
main.py
Entry point de la aplicación Buscador de Productores Asesores de Seguros (SSN).
"""
import threading
import time
import os
import sys
from typing import Any
import flet as ft

from data_manager import DataManager
from ui_components import (
    COLORS,
    build_header,
    build_search_bar,
    build_results_badge,
    build_results_table,
    build_pagination,
    build_detail_dialog,
    build_detail_view,
    build_dashboard_metrics_view,
    build_cartera_view,
    build_loading_state,
    build_welcome_loading_view,
    build_error_state,
    build_footer,
    build_login_view,
    build_licensing_view,
)
from ssn_test import (
    DB_PATH,
    obtener_de_db,
    guardar_en_db,
    obtener_sitekey,
    resolver_captcha,
    buscar_en_ssn,
    parsear_resultado,
    inicializar_db,
    verificar_login,
    verificar_login_status,
    actualizar_password,
    actualizar_estado_contacto,
    actualizar_observaciones,
    actualizar_companias,
    actualizar_sociedades,
    obtener_todas_sociedades,
    generar_password_provisorio,
    enviar_mail_recuperacion,
    registrar_log,
    parsear_e_importar_archivo,
)
from utils import (
    build_index,
    fuzzy_filter,
    count_matches,
    record_to_clipboard,
    MAX_RESULTS,
    PAGE_SIZE,
)

def safe_upper(val):
    return str(val).strip().upper() if val is not None else ''

current_user_context = {"user_id": None, "role": None}

_orig_obtener_de_db = obtener_de_db
def obtener_de_db(identificador: str, user_id: Any = None, role: Any = None) -> Any:
    if user_id is None:
        user_id = current_user_context["user_id"]
    if role is None:
        role = current_user_context["role"]
    return _orig_obtener_de_db(identificador, user_id=user_id, role=role)

_orig_guardar_en_db = guardar_en_db
def guardar_en_db(datos: dict, user_id: Any = None) -> Any:
    if user_id is None:
        user_id = current_user_context["user_id"]
    return _orig_guardar_en_db(datos, user_id=user_id)

APP_NAME           = "CRM Productores de Seguros"
APP_VERSION        = "1.0.0"
WIN_DEFAULT_WIDTH  = 1280
WIN_DEFAULT_HEIGHT = 760
WIN_MIN_WIDTH      = 800
WIN_MIN_HEIGHT     = 560
def get_incomplete_fields_count(r: dict) -> int:
    check_fields = ["telefono", "email", "domicilio", "localidad", "cod_postal", "resolucion", "fecha_resolucion"]
    missing = 0
    for field in check_fields:
        val = r.get(field)
        if val is None or str(val).strip() in ("", "—", "None", "null"):
            missing += 1
    return missing


def get_asset_path(filename: str) -> str:
    if getattr(sys, "frozen", False):
        base = sys._MEIPASS  # type: ignore[attr-defined]
    else:
        base = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base, filename)


def ejecutar_autoupdate(page: ft.Page, download_url: str, version: str):
    import sys
    import os
    import subprocess
    import requests
    import threading

    prog_bar = ft.ProgressBar(width=400, value=0.0)
    prog_text = ft.Text("Descargando actualización (0%)...", size=13, color=COLORS["text_primary"])
    
    cancel_download = False
    
    def on_cancel(e):
        nonlocal cancel_download
        cancel_download = True
        dlg.open = False
        page.update()
        
    dlg = ft.AlertDialog(
        modal=True,
        title=ft.Text(f"Descargando v{version}", size=16, weight=ft.FontWeight.W_700),
        content=ft.Column(
            [
                prog_text,
                prog_bar,
            ],
            tight=True,
            spacing=15,
        ),
        actions=[
            ft.TextButton("Cancelar", on_click=on_cancel)
        ],
    )
    
    if dlg not in page.overlay:
        page.overlay.append(dlg)
    dlg.open = True
    page.update()
    
    def download_thread():
        nonlocal cancel_download
        import time
        
        def log_trace(msg):
            try:
                import tempfile
                log_path = os.path.join(tempfile.gettempdir(), "update_debug.txt")
                with open(log_path, "a", encoding="utf-8") as lf:
                    lf.write(f"[{time.strftime('%H:%M:%S')}] TRACE: {msg}\n")
            except Exception:
                pass
                
        try:
            log_trace("Started download_thread")
            is_frozen = getattr(sys, "frozen", False)
            if is_frozen:
                current_exe = sys.executable
                current_dir = os.path.dirname(current_exe)
                temp_exe = os.path.join(current_dir, "KatrixBroker_new.exe")
            else:
                import tempfile
                current_dir = os.path.dirname(os.path.abspath(__file__))
                temp_exe = os.path.join(tempfile.gettempdir(), "KatrixBroker_latest.exe")
                
            log_trace(f"temp_exe path resolved: {temp_exe}")
            log_trace(f"Calling requests.get for: {download_url}")
            response = requests.get(download_url, stream=True, timeout=30)
            log_trace(f"requests.get status code: {response.status_code}")
            total_size = int(response.headers.get('content-length', 0))
            log_trace(f"total_size parsed: {total_size}")
            
            downloaded = 0
            last_update_time = 0.0
            
            log_trace("Opening temp_exe for writing...")
            with open(temp_exe, "wb") as f:
                log_trace("File opened. Entering iter_content loop...")
                chunk_count = 0
                for chunk in response.iter_content(chunk_size=1024*64):
                    chunk_count += 1
                    if chunk_count % 10 == 1 or chunk_count < 5:
                        log_trace(f"Chunk #{chunk_count} read from stream (len={len(chunk) if chunk else 0})")
                    if cancel_download:
                        log_trace("Download cancelled by user")
                        f.close()
                        try:
                            os.remove(temp_exe)
                        except Exception:
                            pass
                        return
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        
                        current_time = time.time()
                        if current_time - last_update_time >= 0.25:
                            last_update_time = current_time
                            if total_size > 0:
                                pct = downloaded / total_size
                                prog_bar.value = pct
                                prog_text.value = f"Descargando actualización ({int(pct * 100)}%)..."
                            else:
                                prog_bar.value = None
                                prog_text.value = f"Descargando actualización ({downloaded // (1024 * 1024)} MB)..."
                            page.update()
            
            if total_size > 0:
                prog_bar.value = 1.0
                prog_text.value = "Descargando actualización (100%)..."
                page.update()
            
            if is_frozen:
                prog_text.value = "Instalando actualización..."
                page.update()
                
                if sys.platform.startswith("win"):
                    bat_path = os.path.join(current_dir, "update.bat")
                    with open(bat_path, "w", encoding="utf-8") as bf:
                        bf.write(f'''@echo off
timeout /t 2 /nobreak > nul
del "{current_exe}"
rename "{temp_exe}" "{os.path.basename(current_exe)}"
start "" "{current_exe}"
del "%~f0"
''')
                    subprocess.Popen([bat_path], shell=True, creationflags=subprocess.CREATE_NEW_CONSOLE if hasattr(subprocess, "CREATE_NEW_CONSOLE") else 0)
                else:
                    sh_path = os.path.join(current_dir, "update.sh")
                    with open(sh_path, "w", encoding="utf-8") as sf:
                        sf.write(f'''#!/bin/bash
sleep 2
rm -f "{current_exe}"
mv "{temp_exe}" "{current_exe}"
chmod +x "{current_exe}"
"{current_exe}" &
rm -f "$0"
''')
                    os.chmod(sh_path, 0o755)
                    subprocess.Popen(["/bin/bash", sh_path], start_new_session=True)
                
                page.window.close()
            else:
                dlg.open = False
                page.update()
                
                def close_dev_dlg(e):
                    dev_dlg.open = False
                    page.update()
                    
                dev_dlg = ft.AlertDialog(
                    title=ft.Text("Modo Desarrollo", size=16, weight=ft.FontWeight.W_700),
                    content=ft.Text(f"Descarga finalizada. El archivo se guardó como 'KatrixBroker_latest.exe' en {os.path.dirname(temp_exe)}.\nNo se reemplazó tu entorno de ejecución Python.", size=13),
                    actions=[ft.TextButton("Entendido", on_click=close_dev_dlg)]
                )
                if dev_dlg not in page.overlay:
                    page.overlay.append(dev_dlg)
                dev_dlg.open = True
                page.update()
                log_trace("Finished download_thread successfully (non-frozen mode)")
                
        except Exception as err:
            import traceback
            try:
                import tempfile
                log_path = os.path.join(tempfile.gettempdir(), "update_debug.txt")
                with open(log_path, "a", encoding="utf-8") as lf:
                    lf.write(f"Exception in download_thread: {str(err)}\n")
                    lf.write(traceback.format_exc() + "\n")
            except Exception:
                pass
            dlg.open = False
            page.update()
            
            def close_err_dlg(e):
                err_dlg.open = False
                page.update()
                
            err_dlg = ft.AlertDialog(
                title=ft.Text("Error al actualizar", size=16, weight=ft.FontWeight.W_700),
                content=ft.Text(f"No se pudo descargar la actualización:\n{str(err)}", size=13),
                actions=[ft.TextButton("Cerrar", on_click=close_err_dlg)]
            )
            if err_dlg not in page.overlay:
                page.overlay.append(err_dlg)
            err_dlg.open = True
            page.update()

    page.run_thread(download_thread)


def iniciar_check_actualizacion(page: ft.Page, client):
    import sys
    if not getattr(sys, "frozen", False):
        return
        
    def worker():
        try:
            update_info = client.check_update()
            if not update_info:
                return
                
            latest_version = update_info.get("latest_version")
            download_url = update_info.get("download_url")
            
            if not latest_version or not download_url:
                return
                
            try:
                curr_parts = [int(x) for x in APP_VERSION.split(".")]
                latest_parts = [int(x) for x in latest_version.split(".")]
            except Exception:
                if APP_VERSION != latest_version:
                    curr_parts = [0]
                    latest_parts = [1]
                else:
                    return
            
            if latest_parts > curr_parts:
                print(f"⚡ Nueva versión v{latest_version} disponible. Iniciando auto-actualización silenciosa...")
                ejecutar_autoupdate(page, download_url, latest_version)
        except Exception as e:
            print(f"Error silencioso en check de actualización: {e}")

    threading.Thread(target=worker, daemon=True).start()



def main(page: ft.Page):
    page.title             = APP_NAME
    page.window.width      = WIN_DEFAULT_WIDTH
    page.window.height     = WIN_DEFAULT_HEIGHT
    page.window.min_width  = WIN_MIN_WIDTH
    page.window.min_height = WIN_MIN_HEIGHT
    page.window.maximized  = True
    page.bgcolor           = COLORS["background"]
    page.padding           = 0
    page.spacing           = 0
    page.theme             = ft.Theme(color_scheme_seed=COLORS["primary"])
    page.theme_mode        = ft.ThemeMode.LIGHT
    page.locale_configuration = ft.LocaleConfiguration(
        supported_locales=[ft.Locale("es", "ES")],
        current_locale=ft.Locale("es", "ES")
    )

    icon_path = get_asset_path(os.path.join("assets", "icon.png"))
    if os.path.exists(icon_path):
        page.window.icon = icon_path

    def safe_update(control):
        try:
            if control is not None and control.page is not None:
                control.update()
                return True
        except Exception:
            pass
        return False

    state = {
        "records":      [],
        "all_filtered": [],
        "query":        "",
        "ramo":         None,
        "provincia":    None,
        "localidad":    None,
        "provincia2":   None,
        "localidad2":   None,
        "estado_contacto": None,
        "custom_filters": [],
        "page":         0,
        "loading":      True,
        "error":        None,
        "cache_date":   None,
        "debounce_timer": None,
        "dialog":       None,
        "logged_in":    False,
        "license_valid": False,
        "error_license": None,
        "username":     None,
        "role":         None,
        "user_id":      None,
        "permisos":     {"comercial", "buscador", "cartera"},
        "calendar_url": "",
        "error_login":  None,
        "viewing_detail": False,
        "viewing_admin": False,
        "viewing_dashboard": False,
        "viewing_profile": False,
        "viewing_cartera": False,
        "admin_tab_index": 0,
        "mostly_complete": False,
        "sort_column": "matricula",
        "sort_descending": True,
        "regional_only": False,
    }

    from api_client import APIClient
    client = APIClient()

    search_ref       = ft.Ref[ft.TextField]()
    settings_btn_ref = ft.Ref[ft.IconButton]()
    header_ref       = ft.Ref[ft.Container]()
    stats_ref        = ft.Ref[ft.Container]()
    content_area     = ft.Ref[ft.Column]()
    footer_container = ft.Ref[ft.Container]()

    def trigger_import_picker(e):
        try:
            # Usar zenity nativo en Linux para evitar dependencias fallidas (como libmpv) del cliente "full" de Flet
            import subprocess
            import sys
            
            file_path = None
            if sys.platform.startswith("linux"):
                try:
                    res = subprocess.run(
                        ["zenity", "--file-selection", "--title=Seleccionar archivo de Productores", "--file-filter=Excel/CSV | *.xlsx *.xlsm *.csv"],
                        capture_output=True, text=True
                    )
                    if res.returncode == 0 and res.stdout.strip():
                        file_path = res.stdout.strip()
                except FileNotFoundError:
                    show_alert_dialog("Error", "Zenity no está instalado en este sistema.")
                    return
            else:
                # Fallback nativo para Windows (tkinter)
                import tkinter as tk
                from tkinter import filedialog
                root = tk.Tk()
                root.withdraw()
                root.attributes('-topmost', True)
                file_path = filedialog.askopenfilename(
                    title="Seleccionar archivo de Productores",
                    filetypes=[("Excel y CSV", "*.xlsx *.xlsm *.csv")]
                )
                root.destroy()
                
            if not file_path:
                return
                
            loading_import_dlg = ft.AlertDialog(
                modal=True,
                title=ft.Row(
                    controls=[
                        ft.Icon(ft.Icons.UPLOAD_FILE_ROUNDED, color=COLORS["accent"], size=22),
                        ft.Text("Importando Datos", size=16, weight=ft.FontWeight.BOLD, color=COLORS["text_primary"]),
                    ],
                    spacing=8,
                ),
                content=ft.Container(
                    content=ft.Column(
                        controls=[
                            ft.Row(
                                controls=[
                                    ft.ProgressRing(color=COLORS["accent"], width=24, height=24, stroke_width=3),
                                    ft.Text("Procesando y guardando...", size=13, weight=ft.FontWeight.W_500, color=COLORS["text_primary"]),
                                ],
                                spacing=12,
                            ),
                            ft.Text("Esto puede demorar unos segundos dependiendo del tamaño del archivo.", size=12, color=COLORS["text_secondary"]),
                        ],
                        spacing=12,
                        tight=True,
                    ),
                    width=300,
                    padding=10,
                ),
            )
            page.overlay.append(loading_import_dlg)
            loading_import_dlg.open = True
            page.update()
            
            def run_import():
                try:
                    count, incompletos = parsear_e_importar_archivo(file_path)
                    
                    # Reinicializar DataManager para recargar los registros de la DB
                    dm.initialize(user_id=state["user_id"], role=state["role"], regional_only=state.get("regional_only", False))
                    
                    # Cerrar modal
                    loading_import_dlg.open = False
                    page.update()
                    
                    leyenda_incompletos = ""
                    if incompletos > 0:
                        leyenda_incompletos = f"\n\n⚠️ Atención: En la base de datos hay {incompletos} registros con datos incompletos (sin teléfono o email). Podés usar el botón 'Extraer' en la vista de detalle para completarlos."
                        
                    from ssn_test import obtener_total_cached
                    total_db = obtener_total_cached()
                    visibility_str = "Regionales (Cuyo)" if state.get("regional_only", False) else "Nacionales (Todo el país)"
                    
                    show_alert_dialog(
                        "Importación Exitosa", 
                        f"Se han procesado {count} productores del archivo de forma exitosa.\n\n"
                        f"📊 Total de productores en Base de Datos: {total_db}\n"
                        f"👁️ Vista Activa: {visibility_str} ({len(dm.records)} productores visibles en pantalla).\n"
                        f"Se conservaron todos los datos previamente enriquecidos.{leyenda_incompletos}"
                    )
                    if state["username"]:
                        registrar_log(state["username"], "IMPORT_FILE", f"Importados exitosamente {count} registros desde {os.path.basename(file_path)}")
                    
                    # Re-renderizar la lista
                    render_content()
                except Exception as ex:
                    try:
                        loading_import_dlg.open = False
                        page.update()
                    except Exception:
                        pass
                    show_alert_dialog(
                        "Error de Importación", 
                        f"No se pudo procesar el archivo:\n{str(ex)[:200]}"
                    )
            
            threading.Thread(target=run_import, daemon=True).start()
        except Exception as ex:
            show_alert_dialog(
                "Error de Importación", 
                f"No se pudo iniciar el selector de archivos:\n{str(ex)[:200]}"
            )

    def on_vaciar_db_click(e):
        def _confirm_delete(ev):
            from ssn_test import vaciar_base_de_datos
            
            def bg_delete():
                count = vaciar_base_de_datos()
                dm.initialize(user_id=state["user_id"], role=state["role"], regional_only=state.get("regional_only", False))
                dlg.open = False
                page.update()
                if state["username"]:
                    registrar_log(state["username"], "EMPTY_DB", f"Vaciada la base de datos ({count} registros borrados).")
                show_alert_dialog("Base de Datos Vaciada", f"Se han eliminado {count} registros permanentemente.")
                render_content()
                
            page.run_thread(bg_delete)
            
        dlg = ft.AlertDialog(
            title=ft.Row([ft.Icon(ft.Icons.WARNING_ROUNDED, color=ft.Colors.RED_500), ft.Text("Atención: Vaciar Base de Datos")]),
            content=ft.Text("¿Estás 100% seguro de que querés borrar TODOS los registros de la base de datos? Se perderán todas las notas, teléfonos y estados guardados. Esta acción no se puede deshacer.", size=13),
            actions=[
                ft.TextButton("Cancelar", on_click=lambda _: setattr(dlg, "open", False) or page.update()),
                ft.ElevatedButton("Sí, Vaciar Base", on_click=_confirm_delete, style=ft.ButtonStyle(bgcolor=ft.Colors.RED_600, color=ft.Colors.WHITE)),
            ]
        )
        page.overlay.append(dlg)
        dlg.open = True
        page.update()


    # Dropdowns de filtros avanzados
    provincia_dropdown = ft.Dropdown(
        options=[ft.dropdown.Option("Todas las provincias")],
        value="Todas las provincias",
        hint_text="Todas las provincias",
        width=180,
        border_color=COLORS["border"],
        border_radius=10,
        text_size=13,
        content_padding=ft.Padding(left=12, right=12, top=10, bottom=10),
        on_select=lambda e: on_provincia_change(None if e.control.value == "Todas las provincias" else e.control.value),
        color=COLORS["text_primary"],
        bgcolor=COLORS["surface"],
    )

    localidad_dropdown = ft.Dropdown(
        options=[ft.dropdown.Option("Todas las localidades")],
        value="Todas las localidades",
        hint_text="Todas las localidades",
        width=180,
        border_color=COLORS["border"],
        border_radius=10,
        text_size=13,
        content_padding=ft.Padding(left=12, right=12, top=10, bottom=10),
        on_select=lambda e: on_localidad_change(None if e.control.value == "Todas las localidades" else e.control.value),
        color=COLORS["text_primary"],
        bgcolor=COLORS["surface"],
        disabled=True,
    )

    provincia_dropdown2 = ft.Dropdown(
        options=[ft.dropdown.Option("Todas las provincias")],
        value="Todas las provincias",
        hint_text="Todas las provincias",
        width=180,
        border_color=COLORS["border"],
        border_radius=10,
        text_size=13,
        content_padding=ft.Padding(left=12, right=12, top=10, bottom=10),
        on_select=lambda e: on_provincia2_change(None if e.control.value == "Todas las provincias" else e.control.value),
        color=COLORS["text_primary"],
        bgcolor=COLORS["surface"],
    )

    localidad_dropdown2 = ft.Dropdown(
        options=[ft.dropdown.Option("Todas las localidades")],
        value="Todas las localidades",
        hint_text="Todas las localidades",
        width=180,
        border_color=COLORS["border"],
        border_radius=10,
        text_size=13,
        content_padding=ft.Padding(left=12, right=12, top=10, bottom=10),
        on_select=lambda e: on_localidad2_change(None if e.control.value == "Todas las localidades" else e.control.value),
        color=COLORS["text_primary"],
        bgcolor=COLORS["surface"],
        disabled=True,
    )

    estado_dropdown = ft.Dropdown(
        options=[
            ft.dropdown.Option("Todos los estados"),
            ft.dropdown.Option("Sin contactar"),
            ft.dropdown.Option("Contactado"),
            ft.dropdown.Option("No responde"),
            ft.dropdown.Option("Interesado"),
        ],
        value="Todos los estados",
        hint_text="Todos los estados",
        width=180,
        border_color=COLORS["border"],
        border_radius=10,
        text_size=13,
        content_padding=ft.Padding(left=12, right=12, top=10, bottom=10),
        on_select=lambda e: on_estado_change(None if e.control.value == "Todos los estados" else e.control.value),
        color=COLORS["text_primary"],
        bgcolor=COLORS["surface"],
    )

    def show_snackbar(message: str, color: str = COLORS["success"]):
        page.snack_bar = ft.SnackBar(
            content=ft.Row(
                controls=[
                    ft.Icon(ft.Icons.CHECK_CIRCLE_OUTLINE, color="#FFFFFF", size=18),
                    ft.Text(message, color="#FFFFFF", size=13),
                ],
                spacing=10,
            ),
            bgcolor=color,
            duration=4000,
        )
        page.snack_bar.open = True
        page.update()

    def show_alert_dialog(title: str, text: str):
        dlg = ft.AlertDialog(
            title=ft.Row(
                controls=[
                    ft.Icon(ft.Icons.INFO_OUTLINED, color=COLORS["primary"], size=22),
                    ft.Text(title, size=16, weight=ft.FontWeight.BOLD, color=COLORS["text_primary"]),
                ],
                spacing=8,
            ),
            content=ft.Text(text, size=13, color=COLORS["text_secondary"]),
            actions=[
                ft.TextButton("Aceptar", on_click=lambda _: setattr(dlg, "open", False) or page.update()),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        page.overlay.append(dlg)
        dlg.open = True
        page.update()

    def render_content():
        if content_area.current is None:
            return

        def go_to_authorized():
            if "comercial" in state.get("permisos", set()):
                sidebar_selected["index"] = 0
                state["viewing_dashboard"] = True
                state["viewing_cartera"] = False
                state["viewing_admin"] = False
                state["viewing_profile"] = False
            elif "buscador" in state.get("permisos", set()):
                sidebar_selected["index"] = 1
                state["viewing_dashboard"] = False
                state["viewing_cartera"] = False
                state["viewing_admin"] = False
                state["viewing_profile"] = False
            elif "cartera" in state.get("permisos", set()):
                sidebar_selected["index"] = 2
                state["viewing_cartera"] = True
                state["viewing_dashboard"] = False
                state["viewing_admin"] = False
                state["viewing_profile"] = False
            else:
                on_logout(None)
                return
            update_page_layout()
            render_content()

        # Enforce permission checks
        if state.get("viewing_dashboard") and "comercial" not in state.get("permisos", set()):
            from ui_components import build_access_denied_view
            content_area.current.controls = [build_access_denied_view("Gestión Comercial", on_go_back=go_to_authorized)]
            safe_update(content_area.current)
            return

        if state.get("viewing_cartera") and "cartera" not in state.get("permisos", set()):
            from ui_components import build_access_denied_view
            content_area.current.controls = [build_access_denied_view("Cartera & Operaciones", on_go_back=go_to_authorized)]
            safe_update(content_area.current)
            return

        if (not state.get("viewing_admin") and 
            not state.get("viewing_profile") and 
            not state.get("viewing_dashboard") and 
            not state.get("viewing_cartera") and 
            "buscador" not in state.get("permisos", set())):
            from ui_components import build_access_denied_view
            content_area.current.controls = [build_access_denied_view("Red de PAS (Buscador)", on_go_back=go_to_authorized)]
            safe_update(content_area.current)
            return

        if state.get("viewing_admin"):
            render_admin_dashboard()
            return

        if state.get("viewing_dashboard"):
            render_dashboard_metrics()
            return

        if state.get("viewing_profile"):
            render_profile_view()
            return

        if state.get("viewing_cartera"):
            render_cartera_view()
            return

        if state.get("viewing_detail"):
            return

        if state["loading"]:
            content_area.current.controls = [build_loading_state()]
        elif state["error"]:
            content_area.current.controls = [
                build_error_state(state["error"], on_retry=None)
            ]
        else:
            records      = state["records"]
            query        = state["query"]
            ramo         = state["ramo"]
            current_page = state["page"]

            all_filtered  = fuzzy_filter(records, query, ramo)
            
            # Filtro por provincia y localidad (Set 1 y Set 2)
            prov1 = state.get("provincia")
            loc1 = state.get("localidad")
            prov2 = state.get("provincia2")
            loc2 = state.get("localidad2")
            
            # Si la consulta es numérica (matrícula o DNI/cuit de búsqueda específica), 
            # no filtramos por provincia, estado o completitud para permitir localizarlo de inmediato.
            is_specific_search = bool(query and query.strip().isdigit())

            if (prov1 or prov2) and not is_specific_search:
                def matches_prov_loc(r):
                    match1 = True
                    if prov1:
                        match1 = safe_upper(r.get("provincia")) == prov1.upper()
                        if match1 and loc1:
                            match1 = safe_upper(r.get("localidad")) == loc1.upper()
                    else:
                        match1 = False
                        
                    match2 = True
                    if prov2:
                        match2 = safe_upper(r.get("provincia")) == prov2.upper()
                        if match2 and loc2:
                            match2 = safe_upper(r.get("localidad")) == loc2.upper()
                    else:
                        match2 = False
                        
                    if prov1 and prov2:
                        return match1 or match2
                    elif prov1:
                        return match1
                    return match2
                all_filtered = [r for r in all_filtered if matches_prov_loc(r)]
                
            # Filtro por estado_contacto
            if state["estado_contacto"] and not is_specific_search:
                all_filtered = [r for r in all_filtered if r.get("estado_contacto", "Sin contactar").strip().lower() == state["estado_contacto"].lower()]

            # Filtro de registros mayormente completos (máx 3 incompletos)
            if state.get("mostly_complete") and not is_specific_search:
                all_filtered = [r for r in all_filtered if get_incomplete_fields_count(r) <= 3]

            # Filtros personalizados
            if not is_specific_search:
                for f in state.get("custom_filters", []):
                    field = f["field"]
                    op = f["operator"]
                    val = f["value"].strip().lower()
                    if not val:
                        continue
                    if op == "contiene":
                        all_filtered = [r for r in all_filtered if val in str(r.get(field, "")).strip().lower()]
                    elif op == "es igual a":
                        all_filtered = [r for r in all_filtered if val == str(r.get(field, "")).strip().lower()]
                    elif op == "comienza con":
                        all_filtered = [r for r in all_filtered if str(r.get(field, "")).strip().lower().startswith(val)]
                    elif op == "termina con":
                        all_filtered = [r for r in all_filtered if str(r.get(field, "")).strip().lower().endswith(val)]
                    elif op == "no contiene":
                        all_filtered = [r for r in all_filtered if val not in str(r.get(field, "")).strip().lower()]

            # Ordenamiento
            sort_col = state.get("sort_column")
            if sort_col:
                is_desc = state.get("sort_descending", True)
                if sort_col == "matricula":
                    def get_mat_num(r):
                        try:
                            val = r.get("productor_matricula") or r.get("matricula") or 0
                            return int(val)
                        except (ValueError, TypeError):
                            return 0
                    all_filtered.sort(key=get_mat_num, reverse=is_desc)
                elif sort_col == "nombre":
                    all_filtered.sort(key=lambda r: (r.get("productor_apellido_nombre") or r.get("nombre") or "").strip().lower(), reverse=is_desc)
                elif sort_col == "cuit":
                    all_filtered.sort(key=lambda r: (r.get("productor_id") or r.get("cuit") or r.get("documento") or "").strip().lower(), reverse=is_desc)
                elif sort_col == "ramo":
                    all_filtered.sort(key=lambda r: (r.get("ramo") or "").strip().lower(), reverse=is_desc)
                elif sort_col == "estado":
                    all_filtered.sort(key=lambda r: (r.get("estado_contacto") or "").strip().lower(), reverse=is_desc)

            total_matches = len(all_filtered)
            state["all_filtered"] = all_filtered
            update_stats(all_filtered)

            total_pages  = max(1, (total_matches + PAGE_SIZE - 1) // PAGE_SIZE)
            if current_page >= total_pages:
                current_page = 0
                state["page"] = 0

            start        = current_page * PAGE_SIZE
            page_records = all_filtered[start:start + PAGE_SIZE]

            badge      = build_results_badge(total_matches, len(records), query, current_page, total_pages)
            table      = build_results_table(
                page_records,
                on_row_click=open_detail,
                on_live_search=on_live_search,
                query=query,
                db_is_empty=(len(records) == 0),
                on_import_click=trigger_import_picker,
                sort_column=state.get("sort_column"),
                sort_descending=state.get("sort_descending", False),
                on_sort_change=on_sort_change,
            )
            pagination = build_pagination(current_page, total_pages, on_page_change=go_to_page)

            content_area.current.controls = [badge, table, pagination]

        page.update()

    def open_admin_panel(e=None):
        state["viewing_admin"] = True
        state["viewing_detail"] = False
        update_page_layout()
        render_content()

    def exit_admin_panel():
        state["viewing_admin"] = False
        update_page_layout()
        render_content()

    def render_admin_dashboard():
        if content_area.current is not None:
            from ui_components import build_admin_dashboard
            
            def on_crear_usuario(username, email, password, rol="agente", requiere_cambio=1, matricula=None, permisos="comercial,buscador,cartera"):
                from ssn_test import crear_usuario
                return crear_usuario(username, email, password, rol=rol, requiere_cambio=requiere_cambio, matricula=matricula, permisos=permisos)
                
            def on_eliminar_usuario(user_id):
                from ssn_test import eliminar_usuario
                return eliminar_usuario(user_id)
                
            def on_cambiar_password(user_id, new_password):
                from ssn_test import cambiar_password_admin
                return cambiar_password_admin(user_id, new_password)
                
            admin_view = build_admin_dashboard(
                state,
                on_back=exit_admin_panel,
                on_crear_usuario=on_crear_usuario,
                on_eliminar_usuario=on_eliminar_usuario,
                on_cambiar_password=on_cambiar_password,
                on_vaciar_db=on_vaciar_db_click,
                on_import_click=trigger_import_picker,
                page=page,
            )
            content_area.current.controls = [admin_view]
            safe_update(content_area.current)

    def open_dashboard_panel(e=None):
        state["viewing_dashboard"] = True
        state["viewing_detail"] = False
        state["viewing_admin"] = False
        update_page_layout()
        render_content()

    def exit_dashboard_panel():
        state["viewing_dashboard"] = False
        update_page_layout()
        render_content()

    def apply_dashboard_filter(filter_type: str, filter_value: Any):
        if filter_type == "navigate":
            if filter_value == "cartera":
                sidebar_selected["index"] = 2
                state["viewing_cartera"] = True
                state["viewing_dashboard"] = False
                state["viewing_detail"] = False
                state["viewing_admin"] = False
                state["viewing_profile"] = False
                update_page_layout()
                render_content()
            elif filter_value == "red_pas":
                sidebar_selected["index"] = 1
                state["viewing_cartera"] = False
                state["viewing_dashboard"] = False
                state["viewing_detail"] = False
                state["viewing_admin"] = False
                state["viewing_profile"] = False
                update_page_layout()
                render_content()
            return

        state["page"] = 0
        state["query"] = ""
        if search_ref.current:
            search_ref.current.value = ""
            
        if filter_type == "status":
            state["estado_contacto"] = filter_value
            if estado_dropdown:
                if filter_value is None:
                    estado_dropdown.value = "Todos los estados"
                else:
                    val_map = {
                        "sin contactar": "Sin contactar",
                        "contactado": "Contactado",
                        "interesado": "Interesado",
                        "no responde": "No responde"
                    }
                    estado_dropdown.value = val_map.get(filter_value.lower(), "Todos los estados")
                
        elif filter_type == "ramo":
            state["ramo"] = filter_value
            
        elif filter_type == "provincia":
            state["provincia"] = filter_value
            state["localidad"] = None
            if filter_value:
                localidades = sorted(list(set(
                    safe_upper(r.get("localidad")) 
                    for r in state["records"] 
                    if safe_upper(r.get("provincia")) == filter_value.upper() and r.get("localidad")
                )))
                localidad_dropdown.options = [ft.dropdown.Option("Todas las localidades")] + [ft.dropdown.Option(l) for l in localidades]
                localidad_dropdown.value = "Todas las localidades"
                localidad_dropdown.disabled = False
            else:
                localidad_dropdown.options = [ft.dropdown.Option("Todas las localidades")]
                localidad_dropdown.value = "Todas las localidades"
                localidad_dropdown.disabled = True
            
            provincia_dropdown.value = filter_value or "Todas las provincias"
            
        elif filter_type == "compania":
            state["custom_filters"] = [{"field": "companias", "operator": "contiene", "value": filter_value}]
            update_settings_btn()
            
        elif filter_type == "contacto_completo":
            state["mostly_complete"] = True
            
        elif filter_type == "total":
            state["estado_contacto"] = None
            state["ramo"] = None
            state["provincia"] = None
            state["localidad"] = None
            state["custom_filters"] = []
            
            estado_dropdown.value = "Todos los estados"
            provincia_dropdown.value = "Todas las provincias"
            localidad_dropdown.value = "Todas las localidades"
            localidad_dropdown.disabled = True
            update_settings_btn()

        recreate_dropdowns_and_search()
        exit_dashboard_panel()

    def render_dashboard_metrics():
        if content_area.current is not None:
            dash_view = build_dashboard_metrics_view(
                state["records"],
                on_back=exit_dashboard_panel,
                on_filter_click=apply_dashboard_filter,
                page=page,
                state=state,
            )
            content_area.current.controls = [dash_view]
            safe_update(content_area.current)

    def go_to_page(new_page: int):
        state["page"] = new_page
        render_content()

    def on_sort_change(col_id: str):
        if state.get("sort_column") == col_id:
            state["sort_descending"] = not state.get("sort_descending", True)
        else:
            state["sort_column"] = col_id
            state["sort_descending"] = True if col_id == "matricula" else False
        state["page"] = 0
        recreate_dropdowns_and_search()
        render_content()

    def toggle_theme(e):
        current_mode = state.get("theme_mode", "dark")
        new_mode = "light" if current_mode == "dark" else "dark"
        state["theme_mode"] = new_mode
        
        from ui_components import set_theme_mode
        set_theme_mode(new_mode)
        
        page.theme_mode = ft.ThemeMode.DARK if new_mode == "dark" else ft.ThemeMode.LIGHT
        page.bgcolor = COLORS["background"]
        page.theme = ft.Theme(color_scheme_seed=COLORS["primary"])
        
        # Actualizar dropdowns y search bar
        recreate_dropdowns_and_search()
        
        # Actualizar header y footer
        update_header()
        
        # Actualizar footer container
        if footer_container.current is not None:
            new_f = build_footer(state["cache_date"])
            footer_container.current.content = new_f.content
            footer_container.current.bgcolor = new_f.bgcolor
            footer_container.current.border = new_f.border
            safe_update(footer_container.current)
            
        # Re-renderizar la tabla y el resto del contenido
        update_page_layout()
        if state.get("viewing_admin"):
            render_admin_dashboard()
        elif state.get("viewing_detail") and state.get("selected_record"):
            open_detail(state["selected_record"])
        else:
            render_content()

    def recreate_dropdowns_and_search():
        # Guardar valores actuales
        prov_val = provincia_dropdown.value
        loc_val = localidad_dropdown.value
        prov_val2 = provincia_dropdown2.value
        loc_val2 = localidad_dropdown2.value
        est_val = estado_dropdown.value
        search_val = search_ref.current.value if search_ref.current else ""
        
        # Volver a construir dropdowns con los nuevos COLORS
        provincia_dropdown.border_color = COLORS["border"]
        provincia_dropdown.color = COLORS["text_primary"]
        provincia_dropdown.bgcolor = COLORS["surface"]
        
        localidad_dropdown.border_color = COLORS["border"]
        localidad_dropdown.color = COLORS["text_primary"]
        localidad_dropdown.bgcolor = COLORS["surface"]

        provincia_dropdown2.border_color = COLORS["border"]
        provincia_dropdown2.color = COLORS["text_primary"]
        provincia_dropdown2.bgcolor = COLORS["surface"]
        
        localidad_dropdown2.border_color = COLORS["border"]
        localidad_dropdown2.color = COLORS["text_primary"]
        localidad_dropdown2.bgcolor = COLORS["surface"]
        
        estado_dropdown.border_color = COLORS["border"]
        estado_dropdown.color = COLORS["text_primary"]
        estado_dropdown.bgcolor = COLORS["surface"]
        
        from ssn_test import obtener_ultima_actualizacion
        new_search = build_search_bar(
            on_change=on_search_change,
            on_ramo_change=on_ramo_change,
            on_provincia_change=on_provincia_change,
            on_localidad_change=on_localidad_change,
            on_estado_change=on_estado_change,
            on_settings_click=open_custom_filters_dialog,
            search_ref=search_ref,
            settings_btn_ref=settings_btn_ref,
            provincia_dropdown=provincia_dropdown,
            localidad_dropdown=localidad_dropdown,
            estado_dropdown=estado_dropdown,
            provincia_dropdown2=provincia_dropdown2,
            localidad_dropdown2=localidad_dropdown2,
            on_provincia2_change=on_provincia2_change,
            on_localidad2_change=on_localidad2_change,
            on_export_click=export_to_csv,
            on_import_click=trigger_import_picker,
            on_submit=on_search_submit,
            is_admin=(state.get("role") == "admin"),
            ultima_actualizacion=obtener_ultima_actualizacion(),
            on_vaciar_db_click=on_vaciar_db_click,
            on_admin_click=open_admin_panel,
            mostly_complete_value=state.get("mostly_complete", False),
            on_mostly_complete_change=on_mostly_complete_change,
            sort_descending_value=state.get("sort_descending", False),
            on_sort_direction_change=on_sort_direction_change,
            selected_ramo=state.get("ramo"),
            regional_only_value=state.get("regional_only", False),
            on_regional_only_change=on_regional_only_change,
        )
        initial_search.content = new_search.content
        initial_search.bgcolor = new_search.bgcolor
        
        if search_ref.current:
            search_ref.current.value = search_val

    def update_header():
        if header_ref.current is not None:
            if state["logged_in"]:
                # Determinar título según la vista activa
                if state.get("viewing_cartera"):
                    header_title = "Cartera de Productores"
                    header_subtitle = "Gestión y análisis de tu cartera de productores PAS"
                    try:
                        from ssn_test import obtener_cartera_db
                        _count = len(obtener_cartera_db(user_id=state.get("user_id"), role=state.get("role"), regional_only=state.get("regional_only", False)))
                        header_stat = f"{_count} productores en tu organización"
                    except:
                        header_stat = "0 productores en tu organización"
                elif state.get("viewing_dashboard"):
                    header_title = "Gestión Comercial"
                    header_subtitle = "Panel de seguimiento y actividad comercial"
                    header_stat = None
                elif state.get("viewing_admin"):
                    header_title = "Administración"
                    header_subtitle = "Gestión de usuarios, licencias y configuración"
                    header_stat = None
                elif state.get("viewing_profile"):
                    header_title = "Perfil de Usuario"
                    header_subtitle = "Configuración y datos de tu cuenta"
                    header_stat = None
                elif state.get("viewing_detail"):
                    record = state.get("selected_record") or {}
                    nombre = record.get("productor_apellido_nombre") or record.get("nombre") or "Productor"
                    header_title = f"Detalle — {nombre}"
                    header_subtitle = "Ficha completa del Productor Asesor de Seguros"
                    header_stat = None
                else:
                    header_title = "Buscador de Productores"
                    header_subtitle = "Asesores de Seguros · SSN Argentina"
                    header_stat = None

                from notificaciones import obtener_resumen_reuniones
                from ui_components import open_reuniones_notif_dialog
                
                resumen_notif = obtener_resumen_reuniones()
                pending_count = resumen_notif.get("total_pendientes", 0)

                def open_notif_dialog_cb(e=None):
                    open_reuniones_notif_dialog(page, on_refresh_header=update_header)

                new_h = build_header(
                    len(state["records"]),
                    on_logout_click=on_logout,
                    on_logs_click=open_audit_logs_dialog,
                    on_theme_click=toggle_theme,
                    on_dashboard_click=open_dashboard_panel,
                    on_profile_click=open_profile_panel,
                    on_notif_click=open_notif_dialog_cb,
                    pending_notif_count=pending_count,
                    title=header_title,
                    subtitle=header_subtitle,
                    stat_label=header_stat,
                )
            else:
                new_h = build_header(0, on_theme_click=toggle_theme)
            header_ref.current.content = new_h.content
            header_ref.current.bgcolor = new_h.bgcolor
            safe_update(header_ref.current)

    def open_profile_panel(e=None):
        state["viewing_profile"] = True
        state["viewing_admin"] = False
        state["viewing_dashboard"] = False
        state["viewing_detail"] = False
        update_page_layout()
        render_content()

    def exit_profile_panel():
        state["viewing_profile"] = False
        update_page_layout()
        render_content()

    def render_profile_view():
        if content_area.current is not None:
            from ui_components import build_profile_view
            from ssn_test import actualizar_usuario, crear_usuario, eliminar_usuario, cambiar_password_admin
            
            def on_update_profile(new_uname, new_email, new_pwd, new_calendar_url=""):
                success, msg = actualizar_usuario(
                    state["user_id"],
                    new_uname,
                    new_email,
                    password_txt=new_pwd,
                    is_self_update=True,
                    calendar_url=new_calendar_url
                )
                if success:
                    registrar_log(state.get("username", "admin"), "PROFILE_UPDATED", f"Usuario actualizó su propio perfil. Nuevo usuario: '{new_uname}' ({new_email}) - Calendar URL: {new_calendar_url}")
                    state["username"] = new_uname
                    state["calendar_url"] = new_calendar_url
                    update_header()
                return success, msg
                
            def on_crear_usuario_cb(uname, email, pwd, rol, requiere_cambio=1, matricula=None, permisos="comercial,buscador,cartera"):
                return crear_usuario(uname, email, pwd, rol=rol, requiere_cambio=requiere_cambio, matricula=matricula, permisos=permisos)
                
            def on_eliminar_usuario_cb(uid):
                return eliminar_usuario(uid)
                
            def on_cambiar_password_cb(uid, pwd):
                return cambiar_password_admin(uid, pwd)

            profile_view = build_profile_view(
                state,
                on_back=exit_profile_panel,
                on_update_profile=on_update_profile,
                on_crear_usuario=on_crear_usuario_cb,
                on_eliminar_usuario=on_eliminar_usuario_cb,
                on_cambiar_password=on_cambiar_password_cb,
                page=page,
            )
            content_area.current.controls = [profile_view]
            safe_update(content_area.current)

    def exit_cartera_panel():
        state["viewing_cartera"] = False
        update_page_layout()
        render_content()

    def render_cartera_view():
        if content_area.current is None:
            return

        cartera_container = build_cartera_view(
            page=page,
            on_back=exit_cartera_panel,
            user_id=state.get("user_id"),
            role=state.get("role"),
            state=state,
        )
        content_area.current.controls = [cartera_container]
        safe_update(content_area.current)

    def open_audit_logs_dialog(e):
        import sqlite3
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT fecha, usuario, accion, detalles FROM logs_auditoria ORDER BY fecha DESC LIMIT 50")
        rows = cursor.fetchall()
        conn.close()
        
        log_rows = []
        for r in rows:
            fecha_val, user, action, detalles_val = r
            log_rows.append(
                ft.DataRow(
                    cells=[
                        ft.DataCell(ft.Text(fecha_val, size=11, color=COLORS["text_secondary"])),
                        ft.DataCell(ft.Text(user, size=11, color=COLORS["text_primary"], weight=ft.FontWeight.BOLD)),
                        ft.DataCell(ft.Container(
                            content=ft.Text(action, size=10, color=COLORS["text_on_primary"], weight=ft.FontWeight.BOLD),
                            bgcolor=COLORS["primary"] if "SUCCESS" in action or "SAVE" in action or "LOGIN" in action else (COLORS["accent"] if "CHANGED" in action or "UPDATE" in action else "#C62828"),
                            padding=ft.Padding(6, 3, 6, 3),
                            border_radius=4,
                        )),
                        ft.DataCell(ft.Text(detalles_val, size=11, color=COLORS["text_primary"])),
                    ]
                )
            )
            
        logs_table = ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("Fecha/Hora", size=12, weight=ft.FontWeight.BOLD)),
                ft.DataColumn(ft.Text("Usuario", size=12, weight=ft.FontWeight.BOLD)),
                ft.DataColumn(ft.Text("Acción", size=12, weight=ft.FontWeight.BOLD)),
                ft.DataColumn(ft.Text("Descripción", size=12, weight=ft.FontWeight.BOLD)),
            ],
            rows=log_rows,
            column_spacing=18,
            heading_row_height=40,
        )
        
        dlg = ft.AlertDialog(
            title=ft.Row(
                controls=[
                    ft.Icon(ft.Icons.RECEIPT_LONG_ROUNDED, color=COLORS["primary"], size=22),
                    ft.Text("Registro de Auditoría (Últimos 50 eventos)", size=16, weight=ft.FontWeight.BOLD, color=COLORS["text_primary"]),
                ],
                spacing=8,
            ),
            content=ft.Container(
                content=ft.Column(
                    controls=[logs_table],
                    scroll=ft.ScrollMode.AUTO,
                ),
                width=800,
                height=450,
            ),
            actions=[
                ft.TextButton("Cerrar", on_click=lambda _: setattr(dlg, "open", False) or page.update()),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        
        page.overlay.append(dlg)
        dlg.open = True
        page.update()

    def export_to_csv(e):
        import csv
        import urllib.parse
        
        query = search_ref.current.value.strip() if search_ref.current else ""
        ramo = state["selected_ramo"]
        provincia = state["selected_provincia"]
        localidad = state["selected_localidad"]
        estado = state["selected_estado"]
        
        records_to_export = []
        for rec in state["records"]:
            if ramo and rec.get("productor_ramo") != ramo:
                continue
            if provincia:
                cached = obtener_de_db(rec.get("productor_matricula", "")) or (obtener_de_db(rec.get("productor_id", "")) if rec.get("productor_id") else None)
                prov_val = cached.get("provincia") if cached else None
                if not prov_val or prov_val.lower() != provincia.lower():
                    continue
            if localidad:
                cached = obtener_de_db(rec.get("productor_matricula", "")) or (obtener_de_db(rec.get("productor_id", "")) if rec.get("productor_id") else None)
                loc_val = cached.get("localidad") if cached else None
                if not loc_val or loc_val.lower() != localidad.lower():
                    continue
            if estado:
                cached = obtener_de_db(rec.get("productor_matricula", "")) or (obtener_de_db(rec.get("productor_id", "")) if rec.get("productor_id") else None)
                est_val = cached.get("estado_contacto", "Sin contactar") if cached else "Sin contactar"
                if est_val != estado:
                    continue
            if state["custom_filters"]:
                cached = obtener_de_db(rec.get("productor_matricula", "")) or (obtener_de_db(rec.get("productor_id", "")) if rec.get("productor_id") else None)
                c_dict = dict(cached) if cached else {}
                c_dict["nombre"] = rec.get("nombre", "")
                c_dict["matricula"] = rec.get("productor_matricula", "")
                c_dict["cuit"] = rec.get("productor_id", "")
                c_dict["ramo"] = rec.get("productor_ramo", "")
                
                match = True
                for rule in state["custom_filters"]:
                    field = rule["field"]
                    op = rule["op"]
                    val = rule["value"].lower()
                    rec_val = str(c_dict.get(field) or "").lower()
                    if op == "Contiene" and val not in rec_val:
                        match = False
                        break
                    elif op == "Es igual a" and rec_val != val:
                        match = False
                        break
                    elif op == "Comienza con" and not rec_val.startswith(val):
                        match = False
                        break
                    elif op == "Termina con" and not rec_val.endswith(val):
                        match = False
                        break
                if not match:
                    continue
            if query:
                name_val = rec.get("nombre", "")
                mat_val = rec.get("productor_matricula", "")
                id_val = rec.get("productor_id", "")
                if not (fuzzy_filter(query, name_val) or query in mat_val or query in id_val):
                    continue
            records_to_export.append(rec)
            
        if not records_to_export:
            show_alert_dialog("Exportar a CSV", "No hay registros que coincidan con los filtros actuales para exportar.")
            return
            
        export_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "exportaciones")
        os.makedirs(export_dir, exist_ok=True)
        filename = f"productores_exportados_{int(time.time())}.csv"
        filepath = os.path.join(export_dir, filename)
        
        try:
            with open(filepath, mode="w", newline="", encoding="utf-8-sig") as f:
                writer = csv.writer(f, delimiter=";")
                writer.writerow(["Matricula", "Nombre", "CUIT/DNI", "Ramo", "Provincia", "Localidad", "Telefono", "Email", "Domicilio", "Estado Contacto", "Observaciones"])
                for rec in records_to_export:
                    mat = rec.get("productor_matricula", "")
                    cuit = rec.get("productor_id", "")
                    cached = obtener_de_db(mat) or (obtener_de_db(cuit) if cuit else None)
                    prov = cached.get("provincia", "—") if cached else "—"
                    loc = cached.get("localidad", "—") if cached else "—"
                    tel = cached.get("telefono", "—") if cached else "—"
                    email = cached.get("email", "—") if cached else "—"
                    dom = cached.get("domicilio", "—") if cached else "—"
                    est = cached.get("estado_contacto", "Sin contactar") if cached else "Sin contactar"
                    obs = cached.get("observaciones", "") if cached else ""
                    writer.writerow([mat, rec.get("nombre", ""), cuit, rec.get("productor_ramo", ""), prov, loc, tel, email, dom, est, obs])
            
            # Registrar acción en log de auditoría
            if state["username"]:
                registrar_log(state["username"], "EXPORT_CSV", f"Exportación de {len(records_to_export)} productores a CSV")
                
            show_alert_dialog("Exportación Exitosa", f"Se exportaron {len(records_to_export)} productores con éxito.\nGuardado en: {filepath}")
        except Exception as ex:
            show_alert_dialog("Error de Exportación", f"No se pudo guardar el archivo: {str(ex)}")

    def update_footer():
        if footer_container.current is not None:
            new_footer = build_footer(state["cache_date"])
            footer_container.current.content = new_footer.content
            safe_update(footer_container.current)

    def build_stats_cards_ui(target_records=None):
        records = target_records if target_records is not None else state.get("all_filtered", state["records"])
        total = len(records)
        
        sin_contactar = 0
        contactados = 0
        interesados = 0
        no_responde = 0
        
        for r in records:
            status = r.get("estado_contacto", "Sin contactar").strip().lower()
            if status == "sin contactar" or not status:
                sin_contactar += 1
            elif status == "contactado":
                contactados += 1
            elif status == "interesado":
                interesados += 1
            elif status == "no responde":
                no_responde += 1
        
        def filter_by_status(status_val):
            state["estado_contacto"] = status_val
            state["page"] = 0
            if status_val is None:
                estado_dropdown.value = "Todos los estados"
            else:
                val_map = {
                    "sin contactar": "Sin contactar",
                    "contactado": "Contactado",
                    "interesado": "Interesado",
                    "no responde": "No responde"
                }
                estado_dropdown.value = val_map.get(status_val.lower(), "Todos los estados")
            
            safe_update(estado_dropdown)
            render_content()

        def make_card(title, value, icon, color, status_filter):
            return ft.Container(
                content=ft.Row(
                    controls=[
                        ft.Container(
                            content=ft.Icon(icon, color=color, size=24),
                            bgcolor=ft.Colors.with_opacity(0.12, color),
                            border_radius=12,
                            padding=10,
                        ),
                        ft.Column(
                            controls=[
                                ft.Text(str(value), size=18, weight=ft.FontWeight.BOLD, color=COLORS["text_primary"]),
                                ft.Text(title, size=11, color=COLORS["text_secondary"], weight=ft.FontWeight.W_500),
                            ],
                            spacing=1,
                            tight=True,
                        )
                    ],
                    spacing=12,
                ),
                bgcolor=COLORS["surface"],
                border_radius=12,
                padding=14,
                width=190,
                shadow=ft.BoxShadow(spread_radius=1, blur_radius=6, color=ft.Colors.with_opacity(0.06, "#000000")),
                on_click=lambda e: filter_by_status(status_filter),
            )
            
        return ft.Container(
            content=ft.Row(
                controls=[
                    make_card("Total Productores", total, ft.Icons.PEOPLE_ROUNDED, COLORS["primary"], None),
                    make_card("Sin Contactar", sin_contactar, ft.Icons.HOURGLASS_EMPTY_ROUNDED, COLORS["text_secondary"], "sin contactar"),
                    make_card("Contactados", contactados, ft.Icons.PHONE_CALLBACK_ROUNDED, COLORS["success"], "contactado"),
                    make_card("Interesados", interesados, ft.Icons.STAR_ROUNDED, COLORS["warning"], "interesado"),
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                spacing=16,
            ),
            margin=ft.Margin(left=24, right=24, top=16, bottom=8),
        )

    def update_settings_btn():
        if settings_btn_ref.current:
            active = len(state["custom_filters"]) > 0
            settings_btn_ref.current.icon = ft.Icons.SETTINGS_SUGGEST_ROUNDED if active else ft.Icons.SETTINGS_OUTLINED
            settings_btn_ref.current.icon_color = COLORS["accent"] if active else COLORS["primary"]
            settings_btn_ref.current.tooltip = "Filtros personalizados activos" if active else "Configurar filtros personalizados"
            settings_btn_ref.current.update()

    def open_custom_filters_dialog(e):
        temp_filters = [dict(f) for f in state["custom_filters"]]
        rules_column = ft.Column(spacing=10, height=250, scroll=ft.ScrollMode.AUTO)
        
        def update_rule(idx, key, val):
            temp_filters[idx][key] = val
            
        def remove_rule(idx):
            temp_filters.pop(idx)
            refresh_dialog_content()
            
        def add_rule(e):
            temp_filters.append({"field": "nombre", "operator": "contiene", "value": ""})
            refresh_dialog_content()
            
        def build_rule_row(index, rule_data):
            fields = [
                ("nombre", "Nombre"),
                ("matricula", "Matrícula"),
                ("cuit", "CUIT/ID"),
                ("ramo", "Ramo"),
                ("provincia", "Provincia"),
                ("localidad", "Localidad"),
                ("estado_contacto", "Estado"),
                ("domicilio", "Domicilio"),
                ("email", "Email"),
                ("telefono", "Teléfono"),
                ("resolucion", "Resolución"),
            ]
            
            operators = [
                ("contiene", "Contiene"),
                ("es igual a", "Es igual a"),
                ("comienza con", "Comienza con"),
                ("termina con", "Termina con"),
                ("no contiene", "No contiene"),
            ]
            
            field_dd = ft.Dropdown(
                options=[ft.dropdown.Option(k, v) for k, v in fields],
                value=rule_data["field"],
                label="Campo",
                width=140,
                text_size=13,
                content_padding=ft.Padding(10, 8, 10, 8),
                border_radius=6,
                filled=True,
                border_color=COLORS.get("border", "transparent"),
                on_select=lambda e: update_rule(index, "field", e.control.value),
            )
            
            op_dd = ft.Dropdown(
                options=[ft.dropdown.Option(k, v) for k, v in operators],
                value=rule_data["operator"],
                label="Condición",
                width=130,
                text_size=13,
                content_padding=ft.Padding(10, 8, 10, 8),
                border_radius=6,
                filled=True,
                border_color=COLORS.get("border", "transparent"),
                on_select=lambda e: update_rule(index, "operator", e.control.value),
            )
            
            val_tf = ft.TextField(
                value=rule_data["value"],
                label="Valor buscado",
                hint_text="Ej: Mendoza",
                width=170,
                text_size=13,
                content_padding=ft.Padding(10, 8, 10, 8),
                border_radius=6,
                filled=True,
                border_color=COLORS["primary"] if not rule_data["value"] else COLORS.get("border", "transparent"),
                on_change=lambda e: update_rule(index, "value", e.control.value),
                on_submit=apply_filters,
                autofocus=True,
            )
            
            del_btn = ft.IconButton(
                icon=ft.Icons.DELETE_ROUNDED,
                icon_color=ft.Colors.RED_400,
                icon_size=20,
                tooltip="Eliminar regla",
                on_click=lambda e: remove_rule(index),
            )
            
            return ft.Container(
                content=ft.Row(
                    controls=[field_dd, op_dd, val_tf, del_btn],
                    spacing=12,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                padding=12,
                border_radius=8,
                bgcolor="#1E293B",
                border=ft.Border.all(1, COLORS["divider"]),
                margin=ft.Margin.only(bottom=8)
            )

        def build_add_button():
            return ft.Container(
                content=ft.Row(
                    controls=[
                        ft.Icon(ft.Icons.ADD_CIRCLE_OUTLINE_ROUNDED, color=COLORS["primary"], size=20),
                        ft.Text("Agregar nueva condición de búsqueda", color=COLORS["primary"], weight=ft.FontWeight.W_500)
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                ),
                padding=12,
                border_radius=8,
                border=ft.Border.all(1, COLORS["primary"]),
                ink=True,
                on_click=add_rule,
                margin=ft.Margin.only(top=8)
            )

        def refresh_dialog_content():
            rules_column.controls = []
            if not temp_filters:
                rules_column.controls = [
                    ft.Container(
                        content=ft.Column(
                            controls=[
                                ft.Icon(ft.Icons.FILTER_ALT_OFF_ROUNDED, color=COLORS["text_secondary"], size=40),
                                ft.Text("No hay filtros activos.\nAgregá una condición para empezar.", size=13, color=COLORS["text_secondary"], text_align=ft.TextAlign.CENTER),
                            ],
                            alignment=ft.MainAxisAlignment.CENTER,
                            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        ),
                        padding=30,
                        alignment=ft.Alignment(0, 0),
                    )
                ]
            else:
                for idx, rule in enumerate(temp_filters):
                    rules_column.controls.append(build_rule_row(idx, rule))
            
            # Agregar el botón de añadir siempre al final
            rules_column.controls.append(build_add_button())
            
            try:
                rules_column.update()
            except Exception:
                pass

        def apply_filters(e):
            state["custom_filters"] = [dict(f) for f in temp_filters if f["value"].strip()]
            dlg.open = False
            page.update()
            update_settings_btn()
            state["page"] = 0
            render_content()
            
        def clear_filters(e):
            temp_filters.clear()
            refresh_dialog_content()

        refresh_dialog_content()
        
        dlg = ft.AlertDialog(
            title=ft.Row(
                controls=[
                    ft.Icon(ft.Icons.FILTER_ALT_ROUNDED, color=COLORS["primary"], size=24),
                    ft.Text("Filtros Avanzados", size=18, weight=ft.FontWeight.BOLD, color=COLORS["text_primary"]),
                ],
                spacing=10,
            ),
            content=ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Text("Definí reglas condicionales precisas. Si la regla está vacía, se ignora automáticamente.", size=13, color=COLORS["text_secondary"]),
                        ft.Divider(height=16, color=COLORS["divider"]),
                        ft.Container(content=rules_column, width=540),
                    ],
                    tight=True,
                    spacing=8,
                ),
                width=540,
            ),
            actions=[
                ft.TextButton("Limpiar Todo", icon=ft.Icons.DELETE_SWEEP_ROUNDED, on_click=clear_filters, style=ft.ButtonStyle(color=ft.Colors.RED_400)),
                ft.TextButton("Cancelar", on_click=lambda _: setattr(dlg, "open", False) or page.update()),
                ft.ElevatedButton("Aplicar Filtros", icon=ft.Icons.CHECK_ROUNDED, on_click=apply_filters, style=ft.ButtonStyle(bgcolor=COLORS["primary"], color=COLORS["text_on_primary"])),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
            actions_padding=ft.Padding(20, 10, 20, 20),
            title_padding=ft.Padding(20, 20, 20, 0),
            content_padding=ft.Padding(20, 16, 20, 0),
            shape=ft.RoundedRectangleBorder(radius=12),
        )
        
        page.overlay.append(dlg)
        dlg.open = True
        page.update()

    def update_stats(records_override=None):
        if stats_ref.current is not None:
            stats_ref.current.content = build_stats_cards_ui(records_override)
            safe_update(stats_ref.current)

    def on_search_change(query: str):
        state["query"] = query
        state["page"]  = 0
        if state["debounce_timer"] is not None:
            state["debounce_timer"].cancel()
        def do_filter():
            page.run_thread(render_content)
        timer = threading.Timer(0.15, do_filter)
        state["debounce_timer"] = timer
        timer.start()


    def on_search_submit(e):
        query = search_ref.current.value.strip() if search_ref.current else ""
        if not query:
            return
            
        # Calcular los resultados locales de forma síncrona para evitar demoras del debounce
        local_results = fuzzy_filter(state["records"], query, state["ramo"])
        
        # Filtrar por provincia y localidad (Set 1 y Set 2)
        prov1 = state.get("provincia")
        loc1 = state.get("localidad")
        prov2 = state.get("provincia2")
        loc2 = state.get("localidad2")
        
        if prov1 or prov2:
            def matches_prov_loc(r):
                match1 = True
                if prov1:
                    match1 = safe_upper(r.get("provincia")) == prov1.upper()
                    if match1 and loc1:
                        match1 = safe_upper(r.get("localidad")) == loc1.upper()
                else:
                    match1 = False
                    
                match2 = True
                if prov2:
                    match2 = safe_upper(r.get("provincia")) == prov2.upper()
                    if match2 and loc2:
                        match2 = safe_upper(r.get("localidad")) == loc2.upper()
                else:
                    match2 = False
                    
                if prov1 and prov2:
                    return match1 or match2
                elif prov1:
                    return match1
                return match2
            local_results = [r for r in local_results if matches_prov_loc(r)]
            
        # Filtrar por estado_contacto
        if state["estado_contacto"]:
            local_results = [r for r in local_results if r.get("estado_contacto", "Sin contactar").strip().lower() == state["estado_contacto"].lower()]

        # Filtro de registros mayormente completos (máx 3 incompletos)
        if state.get("mostly_complete"):
            local_results = [r for r in local_results if get_incomplete_fields_count(r) <= 3]
            
        # Filtros personalizados
        for f in state.get("custom_filters", []):
            field = f["field"]
            op = f["operator"]
            val = f["value"].strip().lower()
            if not val:
                continue
            if op == "contiene":
                local_results = [r for r in local_results if val in str(r.get(field, "")).strip().lower()]
            elif op == "es igual a":
                local_results = [r for r in local_results if val == str(r.get(field, "")).strip().lower()]
            elif op == "comienza con":
                local_results = [r for r in local_results if str(r.get(field, "")).strip().lower().startswith(val)]
            elif op == "termina con":
                local_results = [r for r in local_results if str(r.get(field, "")).strip().lower().endswith(val)]
            elif op == "no contiene":
                local_results = [r for r in local_results if val not in str(r.get(field, "")).strip().lower()]

        # Si la consulta es numérica, verificamos si existe de manera exacta por matrícula o ID/cuit en los registros.
        # Si no existe de forma exacta (aunque haya coincidencias parciales por caracteres), mostramos el diálogo.
        show_dialog = False
        if query.isdigit():
            is_exact_matricula_present = any(str(r.get("productor_matricula")).strip() == query for r in state["records"])
            is_exact_id_present = any(str(r.get("productor_id")).strip() == query for r in state["records"])
            if not (is_exact_matricula_present or is_exact_id_present):
                show_dialog = True
        elif not local_results:
            show_dialog = True

        # Mostrar el cuadro de diálogo de extracción
        if show_dialog:
            def on_confirm_live_search(e_confirm):
                confirm_dlg.open = False
                page.update()
                on_live_search(query)
                
            confirm_dlg = ft.AlertDialog(
                title=ft.Row(
                    controls=[
                        ft.Icon(ft.Icons.WIFI_FIND_ROUNDED, color=COLORS["accent"], size=22),
                        ft.Text("Extraer Productor desde la SSN", size=16, weight=ft.FontWeight.BOLD, color=COLORS["text_primary"]),
                    ],
                    spacing=8,
                ),
                content=ft.Container(
                    content=ft.Column(
                        controls=[
                            ft.Text(f"No se encontró el productor '{query}' en la base local.", size=13, weight=ft.FontWeight.BOLD, color=COLORS["text_primary"]),
                            ft.Text("¿Desea consultar e importar sus datos en vivo desde la SSN?", size=12, color=COLORS["text_secondary"]),
                        ],
                        spacing=8,
                        tight=True,
                    ),
                    width=320,
                    padding=10,
                ),
                actions=[
                    ft.TextButton("Cancelar", on_click=lambda _: setattr(confirm_dlg, "open", False) or page.update()),
                    ft.ElevatedButton(
                        "Consultar y Extraer",
                        on_click=on_confirm_live_search,
                        style=ft.ButtonStyle(bgcolor=COLORS["accent"], color=COLORS["text_on_primary"]),
                    ),
                ],
                actions_alignment=ft.MainAxisAlignment.END,
            )
            
            page.overlay.append(confirm_dlg)
            confirm_dlg.open = True
            page.update()

    def on_ramo_change(ramo):
        state["ramo"] = ramo
        state["page"] = 0
        render_content()

    def on_provincia_change(prov):
        state["provincia"] = prov
        state["localidad"] = None
        state["page"]      = 0
        
        if prov:
            localidades = sorted(list(set(
                safe_upper(r.get("localidad")) 
                for r in state["records"] 
                if safe_upper(r.get("provincia")) == prov.upper() and r.get("localidad")
            )))
            localidad_dropdown.options = [ft.dropdown.Option("Todas las localidades")] + [ft.dropdown.Option(l) for l in localidades]
            localidad_dropdown.value = "Todas las localidades"
            localidad_dropdown.disabled = False
        else:
            localidad_dropdown.options = [ft.dropdown.Option("Todas las localidades")]
            localidad_dropdown.value = "Todas las localidades"
            localidad_dropdown.disabled = True
            
        safe_update(localidad_dropdown)
        render_content()

    def on_localidad_change(loc):
        state["localidad"] = loc
        state["page"]      = 0
        render_content()

    def on_provincia2_change(prov):
        state["provincia2"] = prov
        state["localidad2"] = None
        state["page"]      = 0
        
        if prov:
            localidades = sorted(list(set(
                safe_upper(r.get("localidad")) 
                for r in state["records"] 
                if safe_upper(r.get("provincia")) == prov.upper() and r.get("localidad")
            )))
            localidad_dropdown2.options = [ft.dropdown.Option("Todas las localidades")] + [ft.dropdown.Option(l) for l in localidades]
            localidad_dropdown2.value = "Todas las localidades"
            localidad_dropdown2.disabled = False
        else:
            localidad_dropdown2.options = [ft.dropdown.Option("Todas las localidades")]
            localidad_dropdown2.value = "Todas las localidades"
            localidad_dropdown2.disabled = True
            
        safe_update(localidad_dropdown2)
        render_content()

    def on_localidad2_change(loc):
        state["localidad2"] = loc
        state["page"]      = 0
        render_content()

    def on_estado_change(est):
        state["estado_contacto"] = est
        state["page"]            = 0
        render_content()

    def on_mostly_complete_change(val):
        state["mostly_complete"] = val
        state["page"]            = 0
        recreate_dropdowns_and_search()
        render_content()
        if val:
            show_snackbar("Filtro Activo: Se ocultan productores con datos de contacto incompletos.", COLORS["success"])
        else:
            show_snackbar("Filtro Desactivado: Se muestran todos los productores.", COLORS["primary"])

    def on_sort_direction_change(val):
        state["sort_descending"] = val
        state["page"]            = 0
        recreate_dropdowns_and_search()
        render_content()
        show_snackbar(f"Orden establecido: {'Descendente' if val else 'Ascendente'}", COLORS["accent"])

    def on_regional_only_change(val):
        state["regional_only"] = val
        state["page"]          = 0
        
        # Mostrar snackbar indicando el inicio del recargo
        if val:
            show_snackbar("Cargando productores regionales (Cuyo)...", COLORS["primary"])
        else:
            show_snackbar("Cargando productores nacionales (todo el país)...", COLORS["primary"])
            
        def bg_reload():
            try:
                # Cargar datos de la base de datos
                dm.initialize(user_id=state["user_id"], role=state["role"], regional_only=val)
                # Re-crear dropdowns y filtros
                recreate_dropdowns_and_search()
                render_content()
                if val:
                    show_snackbar("Vista: Se muestran solo productores de Cuyo (Mendoza, San Juan, San Luis).", COLORS["success"])
                else:
                    show_snackbar("Vista: Se muestran productores de todo el país (Nacional).", COLORS["success"])
            except Exception as ex:
                show_snackbar(f"Error al recargar base de datos: {ex}", COLORS["warning"])
                
        threading.Thread(target=bg_reload, daemon=True).start()

    def on_live_search(query_str: str, search_type: str = "AUTO"):
        if query_str == "MANUAL_EXTRACT" or not query_str.isdigit():
            search_type_dd = ft.Dropdown(
                options=[
                    ft.dropdown.Option("MATRICULA", "Nro. de Matrícula"),
                    ft.dropdown.Option("DNI", "Nro. de Documento (DNI/CUIT)"),
                ],
                value="MATRICULA",
                width=280,
                text_size=13,
                border_radius=8,
            )
            
            number_tf = ft.TextField(
                label="Número a consultar",
                hint_text="Ej: 88295 o 27318551435",
                width=280,
                text_size=13,
                border_radius=8,
            )
            
            def on_confirm_extract(e):
                val = number_tf.value.strip()
                if not val or not val.isdigit():
                    show_alert_dialog("Dato Inválido", "Por favor, ingresá un número válido para consultar.")
                    return
                # Cerrar modal
                dlg.open = False
                page.update()
                # Ejecutar raspado real
                on_live_search(val, search_type_dd.value)
                
            dlg = ft.AlertDialog(
                title=ft.Row(
                    controls=[
                        ft.Icon(ft.Icons.ADD_LINK_ROUNDED, color=COLORS["accent"], size=22),
                        ft.Text("Extraer Productor desde la SSN", size=16, weight=ft.FontWeight.BOLD, color=COLORS["text_primary"]),
                    ],
                    spacing=8,
                ),
                content=ft.Container(
                    content=ft.Column(
                        controls=[
                            ft.Text("Ingresá la matrícula o CUIT para consultar en vivo y guardar en el CRM.", size=12, color=COLORS["text_secondary"]),
                            ft.Container(height=8),
                            search_type_dd,
                            ft.Container(height=4),
                            number_tf,
                        ],
                        spacing=8,
                        tight=True,
                    ),
                    width=300,
                    padding=10,
                ),
                actions=[
                    ft.TextButton("Cancelar", on_click=lambda _: setattr(dlg, "open", False) or page.update()),
                    ft.ElevatedButton("Consultar y Extraer", on_click=on_confirm_extract, style=ft.ButtonStyle(bgcolor=COLORS["accent"], color=COLORS["text_on_primary"])),
                ],
                actions_alignment=ft.MainAxisAlignment.END,
            )
            page.overlay.append(dlg)
            dlg.open = True
            page.update()
            return
            
        actual_type = search_type
        if actual_type == "AUTO":
            actual_type = "MATRICULA" if len(query_str) <= 6 else "DNI"
            
        # Crear y mostrar un diálogo de carga modal persistente
        loading_dlg = ft.AlertDialog(
            modal=True,
            title=ft.Row(
                controls=[
                    ft.Icon(ft.Icons.CLOUD_DOWNLOAD_ROUNDED, color=COLORS["accent"], size=22),
                    ft.Text("Extrayendo de la SSN", size=16, weight=ft.FontWeight.BOLD, color=COLORS["text_primary"]),
                ],
                spacing=8,
            ),
            content=ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Row(
                            controls=[
                                ft.ProgressRing(color=COLORS["accent"], width=24, height=24, stroke_width=3),
                                ft.Text("Consultando base de datos...", size=13, weight=ft.FontWeight.W_500, color=COLORS["text_primary"]),
                            ],
                            spacing=12,
                        ),
                        ft.Text("Resolviendo CAPTCHA y extrayendo datos. Esto puede demorar unos 15 segundos.", size=12, color=COLORS["text_secondary"]),
                    ],
                    spacing=12,
                    tight=True,
                ),
                width=300,
                padding=10,
            ),
        )
        
        page.overlay.append(loading_dlg)
        loading_dlg.open = True
        page.update()
            
        def run_live_search():
            try:
                sitekey = obtener_sitekey()
                token = resolver_captcha(sitekey)
                
                html = buscar_en_ssn(query_str, actual_type, token)
                datos = parsear_resultado(html)
                
                def handle_result():
                    loading_dlg.open = False
                    page.update()
                    
                    if datos:
                        guardar_en_db(datos)
                        cuit = datos.get("cuit") or datos.get("documento") or ""
                        new_rec = {
                            "productor_matricula": datos.get("matricula", ""),
                            "productor_apellido_nombre": datos.get("nombre", "Productor nuevo"),
                            "productor_id": cuit,
                            "productor_tipo_id": "CUIT" if len(cuit) == 11 else "DNI",
                            "ramo": datos.get("ramo", "Patrimoniales y Vida"),
                            "provincia": datos.get("provincia", "—"),
                            "telefono": datos.get("telefono", "—"),
                            "email": datos.get("email", "—"),
                            "resolucion": datos.get("resolucion", "—"),
                            "fecha_resolucion": datos.get("fecha_resolucion", "—"),
                            "domicilio": datos.get("domicilio", "—"),
                            "localidad": datos.get("localidad", "—"),
                            "cod_postal": datos.get("cod_postal", "—"),
                            "estado_contacto": "Sin contactar",
                            "companias": datos.get("companias", ""),
                            "sociedades": datos.get("sociedades", ""),
                            "observaciones": datos.get("observaciones", ""),
                            "usuario_id": state.get("user_id"),
                        }
                        
                        state["records"].insert(0, new_rec)
                        build_index(state["records"])
                        
                        # Registrar log
                        if state["username"]:
                            registrar_log(state["username"], "SCRAPE_LIVE", f"Extraído exitosamente {actual_type}: {query_str} ({new_rec['productor_apellido_nombre']})")
                        
                        render_content()
                        open_detail(new_rec)
                        show_alert_dialog("Productor Extraído", f"Se ha extraído y guardado a {new_rec['productor_apellido_nombre']} con éxito.")
                    else:
                        show_alert_dialog("Sin Resultados", f"No se encontró ningún productor activo con {actual_type.lower()} {query_str} en la base de la SSN.")
                        render_content()
                
                page.run_thread(handle_result)
                
            except Exception as ex:
                print(f"Error en búsqueda en vivo: {ex}")
                def handle_error():
                    loading_dlg.open = False
                    page.update()
                    show_alert_dialog("Error de Extracción", f"Hubo un error al conectar con la SSN o resolver el Captcha:\n{str(ex)[:150]}")
                    render_content()
                page.run_thread(handle_error)
        
        threading.Thread(target=run_live_search, daemon=True).start()

    def open_detail(record: dict):
        # ── Normalizar claves: los registros de Cartera usan "matricula"/"cuit"/"nombre"
        # mientras que los del Buscador usan "productor_matricula"/"productor_id"/etc.
        # Hacemos que ambos formatos funcionen de forma transparente.
        if not record.get("productor_matricula") and record.get("matricula"):
            record["productor_matricula"] = record["matricula"]
        if not record.get("productor_id") and record.get("cuit"):
            record["productor_id"] = record["cuit"]
        if not record.get("productor_apellido_nombre") and record.get("nombre"):
            record["productor_apellido_nombre"] = record["nombre"]
        if not record.get("productor_ramo") and record.get("ramo"):
            record["productor_ramo"] = record["ramo"]

        state["selected_record"] = record
        def on_back():
            if state.get("detail_back_to_cartera"):
                state["viewing_detail"] = False
                state["selected_record"] = None
                state["viewing_cartera"] = True
                state["viewing_dashboard"] = False
                sidebar_selected["index"] = 2
                state["detail_back_to_cartera"] = False
            elif state.get("detail_back_to_dashboard"):
                state["viewing_detail"] = False
                state["selected_record"] = None
                state["viewing_dashboard"] = True
                sidebar_selected["index"] = 0
                state["detail_back_to_dashboard"] = False
            else:
                state["viewing_detail"] = False
                state["selected_record"] = None
            update_page_layout()
            render_content()

        def copy_to_clipboard(rec: dict):
            text = record_to_clipboard(rec)
            page.set_clipboard(text)
            show_snackbar("Datos copiados al portapapeles ✓")

        def on_register_visit_click(rec: dict):
            state["viewing_dashboard"] = True
            state["viewing_detail"]    = False
            state["viewing_cartera"]   = False
            state["viewing_admin"]     = False
            state["viewing_profile"]   = False
            sidebar_selected["index"] = 0
            state["active_dashboard_tab"] = "Plan de Visitas"
            
            domicilio = rec.get("domicilio", "") or ""
            localidad = rec.get("localidad", "") or ""
            provincia = rec.get("provincia", "") or ""
            lugar_parts = [p.strip() for p in [domicilio, localidad, provincia] if p.strip() and p.strip() != "—"]
            lugar_str = ", ".join(lugar_parts)

            state["prefill_new_visit"] = {
                "nombre": rec.get("productor_apellido_nombre") or rec.get("nombre") or "",
                "matricula": rec.get("productor_matricula") or rec.get("matricula") or "",
                "compania": (rec.get("companias") or "").split(",")[0].strip(),
                "lugar": lugar_str
            }
            update_page_layout()
            render_content()
            
            import time
            def trigger_dialog():
                time.sleep(0.4)
                if "open_add_pas_dialog" in state:
                    state["open_add_pas_dialog"](None)
            page.run_thread(trigger_dialog)

        def on_status_change(nuevo_estado: str):
            matricula = record.get("productor_matricula")
            if matricula:
                current_user = state.get("username") or "broker"
                old_status = record.get("estado_contacto", "Sin contactar")
                if old_status != nuevo_estado:
                    if actualizar_estado_contacto(matricula, nuevo_estado, usuario=current_user):
                        record["estado_contacto"] = nuevo_estado
                        for r in state["records"]:
                            if r.get("productor_matricula") == matricula:
                                r["estado_contacto"] = nuevo_estado
                                break
                        
                        # Generate dynamic log entry in bitácora
                        from datetime import datetime
                        timestamp = datetime.now().strftime("%d/%m/%Y %H:%M")
                        log_entry = f"[{timestamp} - {current_user}]: Cambió el estado de contacto a: {nuevo_estado}"
                        
                        old_obs = record.get("observaciones", "") or ""
                        if old_obs.strip():
                            updated_obs = old_obs.rstrip("\n") + "\n" + log_entry
                        else:
                            updated_obs = log_entry
                            
                        if actualizar_observaciones(matricula, updated_obs, usuario=current_user):
                            record["observaciones"] = updated_obs
                            for r in state["records"]:
                                if r.get("productor_matricula") == matricula:
                                    r["observaciones"] = updated_obs
                                    break
                        
                        # Auto-log a "Llamado" activity in the commercial module
                        try:
                            from ssn_test import guardar_actividad_comercial
                            mes_actual = datetime.now().strftime("%Y-%m")
                            fecha_actividad = datetime.now().strftime("%Y-%m-%d")
                            nombre_pas = record.get("nombre") or record.get("productor_apellido_nombre") or f"Matrícula {matricula}"
                            companias_val = record.get("companias", "") or ""
                            compania_principal = companias_val.split(",")[0].strip() if companias_val else "Sin Compañía"
                            
                            guardar_actividad_comercial(
                                mes=mes_actual,
                                fecha_actividad=fecha_actividad,
                                matricula=str(matricula),
                                nombre=nombre_pas,
                                tipo="Llamado",
                                compania=compania_principal,
                                observaciones=f"Contacto: {nuevo_estado}"
                            )
                        except Exception as e:
                            print(f"Error logging activity commercial: {e}")
                                    
                        show_snackbar(f"Se actualizó el estado a: {nuevo_estado}", COLORS["success"])
                        open_detail(record)
                        update_stats()

                        if state.get("refresh_dashboard"):
                            try:
                                state["refresh_dashboard"]()
                            except Exception as ex:
                                print(f"Error calling refresh_dashboard from status change: {ex}")
                    else:
                        show_snackbar("No se pudo actualizar el estado de contacto.", COLORS["warning"])

        matricula = record.get("productor_matricula", "")
        cuit = record.get("productor_id", "")
        
        cached = obtener_de_db(matricula) or (obtener_de_db(cuit) if cuit else None)
        if cached:
            record["provincia"] = cached.get("provincia") or "—"
            record["telefono"] = cached.get("telefono") or "—"
            record["email"] = cached.get("email") or "—"
            record["resolucion"] = cached.get("resolucion") or "—"
            record["fecha_resolucion"] = cached.get("fecha_resolucion") or "—"
            record["domicilio"] = cached.get("domicilio") or "—"
            record["localidad"] = cached.get("localidad") or "—"
            record["cod_postal"] = cached.get("cod_postal") or "—"
            record["estado_contacto"] = cached.get("estado_contacto") or "Sin contactar"
            record["observaciones"] = cached.get("observaciones") or ""
            record["companias"] = cached.get("companias") or ""
            record["sociedades"] = cached.get("sociedades") or ""
        else:
            record["observaciones"] = ""
            record["companias"] = ""
            record["sociedades"] = ""

        def on_save_notes(obs_text: str, show_alert: bool = True):
            mat = record.get("productor_matricula")
            if mat:
                current_user = state.get("username") or "broker"
                if actualizar_observaciones(mat, obs_text, usuario=current_user):
                    record["observaciones"] = obs_text
                    for r in state["records"]:
                        if r.get("productor_matricula") == mat:
                            r["observaciones"] = obs_text
                            break
                    if show_alert:
                        show_alert_dialog("Observaciones Guardadas", "Las notas se guardaron correctamente en la base de datos.")
                else:
                    show_alert_dialog("Error", "No se pudieron guardar las notas.")

        def on_save_companias(companias_text: str):
            mat = record.get("productor_matricula")
            if mat:
                current_user = state.get("username") or "broker"
                if actualizar_companias(mat, companias_text, usuario=current_user):
                    record["companias"] = companias_text
                    for r in state["records"]:
                        if r.get("productor_matricula") == mat:
                            r["companias"] = companias_text
                            break
                    show_snackbar("Compañías actualizadas ✓")
                    open_detail(record)
                    update_stats()
                else:
                    show_alert_dialog("Error", "No se pudieron guardar las compañías.")

        def on_save_sociedades(sociedades_text: str):
            mat = record.get("productor_matricula")
            if mat:
                current_user = state.get("username") or "broker"
                if actualizar_sociedades(mat, sociedades_text, usuario=current_user):
                    record["sociedades"] = sociedades_text
                    for r in state["records"]:
                        if r.get("productor_matricula") == mat:
                            r["sociedades"] = sociedades_text
                            break
                    show_snackbar("Sociedades vinculadas actualizadas ✓")
                    open_detail(record)
                    update_stats()
                else:
                    show_alert_dialog("Error", "No se pudieron guardar las sociedades vinculadas.")

        def on_scrape_click(rec: dict, ev):
            def run_scrape():
                current_user = state.get("username") or "broker"
                try:
                    # Notify start
                    page.run_thread(lambda: show_snackbar(f"Actualizando datos de {rec.get('productor_apellido_nombre')} desde la SSN...", color=COLORS["accent"]))
                    
                    # Log start in DB
                    registrar_log(
                        current_user,
                        "UPDATE_SSN_START",
                        f"Iniciando consulta live SSN para {rec.get('productor_apellido_nombre')} (Matrícula: {rec.get('productor_matricula')})"
                    )

                    sitekey = obtener_sitekey()
                    page.run_thread(lambda: show_snackbar("Resolviendo reCAPTCHA con Capsolver... (demora ~15s)", color=COLORS["accent"]))
                    token = resolver_captcha(sitekey)
                    
                    identificador = rec.get("productor_id") or rec.get("productor_matricula")
                    if not identificador:
                        raise ValueError("No se encontró matrícula ni documento para consultar.")
                    
                    actual_type = "MATRICULA" if len(str(identificador).strip()) <= 6 else "DNI"
                    html = buscar_en_ssn(str(identificador), actual_type, token)
                    datos = parsear_resultado(html)
                    
                    if datos:
                        guardar_en_db(datos)
                        rec["provincia"] = datos.get("provincia", "—")
                        rec["telefono"] = datos.get("telefono", "—")
                        rec["email"] = datos.get("email", "—")
                        rec["resolucion"] = datos.get("resolucion", "—")
                        rec["fecha_resolucion"] = datos.get("fecha_resolucion", "—")
                        rec["estado_contacto"] = datos.get("estado_contacto") or "Sin contactar"
                        rec["companias"] = datos.get("companias", "")
                        
                        # Log success in DB
                        registrar_log(
                            current_user,
                            "UPDATE_SSN_SUCCESS",
                            f"Actualización SSN exitosa para {rec.get('productor_apellido_nombre')} (Matrícula: {rec.get('productor_matricula')})"
                        )
                        
                        def reopen():
                            build_index(state["records"])
                            open_detail(rec)
                            show_alert_dialog("Consulta en Vivo SSN", "Datos de contacto obtenidos y guardados con éxito ✓")
                            update_stats()
                        page.run_thread(reopen)
                    else:
                        # Log empty result in DB
                        registrar_log(
                            current_user,
                            "UPDATE_SSN_EMPTY",
                            f"Consulta SSN sin resultados para {rec.get('productor_apellido_nombre')} (Matrícula: {rec.get('productor_matricula')})"
                        )
                        page.run_thread(lambda: show_snackbar("No se encontraron datos de contacto en la SSN.", color=COLORS["warning"]))
                        page.run_thread(lambda: open_detail(rec))
                except Exception as ex:
                    print(f"Error al raspar en vivo: {ex}")
                    # Log error in DB
                    registrar_log(
                        current_user,
                        "UPDATE_SSN_ERROR",
                        f"Error actualizando {rec.get('productor_apellido_nombre')} (Matrícula: {rec.get('productor_matricula')}): {str(ex)[:200]}"
                    )
                    page.run_thread(lambda: show_snackbar(f"Error al consultar la SSN: {str(ex)[:60]}", color=COLORS["warning"]))
                    page.run_thread(lambda: open_detail(rec))
            
            threading.Thread(target=run_scrape, daemon=True).start()

        state["viewing_detail"] = True
        update_page_layout()

        if content_area.current is not None:
            def _go_to_cartera():
                state["viewing_cartera"]   = True
                state["viewing_dashboard"] = False
                state["viewing_detail"]    = False
                state["viewing_admin"]     = False
                state["viewing_profile"]   = False
                sidebar_selected["index"]  = 2
                update_page_layout()
                render_content()
                update_header()

            detail_view = build_detail_view(
                record,
                on_back,
                copy_to_clipboard,
                on_status_change,
                page,
                on_scrape_click,
                on_save_notes,
                on_save_companias,
                on_save_sociedades,
                calendar_url=state.get("calendar_url", ""),
                usuario=state.get("username", "broker"),
                state=state,
                on_register_visit_click=on_register_visit_click,
                on_go_cartera=_go_to_cartera,
            )
            content_area.current.controls = [detail_view]
            safe_update(content_area.current)

    def open_detail_by_matricula(matricula_val, back_to="dashboard"):
        if not matricula_val:
            return
        try:
            from ssn_test import obtener_de_db
            rec = obtener_de_db(str(matricula_val))
            if rec:
                # Configurar el estado de navegación según el origen
                state["detail_back_to_dashboard"] = (back_to == "dashboard")
                state["detail_back_to_cartera"]   = (back_to == "cartera")
                state["viewing_dashboard"] = False
                state["viewing_detail"] = True
                state["viewing_cartera"] = False
                state["viewing_admin"] = False
                state["viewing_profile"] = False
                sidebar_selected["index"] = 2 if back_to == "cartera" else 1
                open_detail(rec)
            else:
                show_snackbar("No se encontró el productor en la base de datos local.", color=COLORS["warning"])
        except Exception as e:
            print("Error opening detail by matricula:", e)

    state["open_detail_by_matricula"] = open_detail_by_matricula

    def on_load_success(records):
        state["records"] = records
        state["page"]    = 0
        build_index(records)
        state["loading"] = False
        state["error"]   = None
        
        # Populate Provincia dropdown
        provincias = sorted(list(set(
            safe_upper(r.get("provincia")) 
            for r in records 
            if r.get("provincia") and r.get("provincia").strip() not in ["", "—", "-", "_"]
        )))
        provincia_dropdown.options = [ft.dropdown.Option("Todas las provincias")] + [ft.dropdown.Option(p) for p in provincias]
        provincia_dropdown.value = "Todas las provincias"
        provincia_dropdown2.options = [ft.dropdown.Option("Todas las provincias")] + [ft.dropdown.Option(p) for p in provincias]
        provincia_dropdown2.value = "Todas las provincias"
        
        safe_update(provincia_dropdown)
        safe_update(provincia_dropdown2)
        # Call synchronously to prevent concurrent modification of the DOM
        if state.get("logged_in") and not state.get("loading_login", False):
            render_content()
            update_header()
            update_stats()

    def on_load_error(message: str):
        state["loading"] = False
        state["error"]   = message
        page.run_thread(render_content)

    def on_update_available(fecha: str):
        state["cache_date"] = fecha
        state["records"]    = dm.records
        state["page"]       = 0
        build_index(dm.records)
        
        # Repopulate Provincia dropdown
        provincias = sorted(list(set(
            safe_upper(r.get("provincia")) 
            for r in dm.records 
            if r.get("provincia") and r.get("provincia").strip() not in ["", "—", "-", "_"]
        )))
        provincia_dropdown.options = [ft.dropdown.Option("Todas las provincias")] + [ft.dropdown.Option(p) for p in provincias]
        provincia_dropdown.value = "Todas las provincias"
        provincia_dropdown2.options = [ft.dropdown.Option("Todas las provincias")] + [ft.dropdown.Option(p) for p in provincias]
        provincia_dropdown2.value = "Todas las provincias"
        
        page.run_thread(safe_update, provincia_dropdown)
        page.run_thread(safe_update, provincia_dropdown2)
        page.run_thread(update_header)
        page.run_thread(update_footer)
        page.run_thread(render_content)
        page.run_thread(update_stats)
        page.run_thread(lambda: show_snackbar(f"Datos actualizados al {fecha}"))

    def on_update_error(message: str):
        page.run_thread(lambda: show_snackbar(
            f"⚠ No se pudo actualizar: {message[:80]}",
            color=COLORS["warning"],
        ))

    def on_login(email: str, password_txt: str, remember: bool = False):
        success, requiere_cambio, msg_error, rol, user_id = verificar_login_status(email, password_txt)
        if success:
            state["error_login"] = None
            state["username"] = email.strip().lower()
            state["role"] = rol or "agente"
            state["user_id"] = user_id
            
            if remember:
                client.save_credentials(email, password_txt)
            else:
                client.clear_credentials()
            
            from ssn_test import obtener_usuarios
            try:
                users_list = obtener_usuarios()
                curr_user = next((u for u in users_list if u["id"] == user_id), None)
                if curr_user:
                    state["calendar_url"] = curr_user.get("calendar_url") or ""
                    p_str = curr_user.get("permisos") or "comercial,buscador,cartera"
                    state["permisos"] = {p.strip() for p in p_str.split(",") if p.strip()}
                else:
                    state["calendar_url"] = ""
                    state["permisos"] = {"comercial", "buscador", "cartera"}
            except Exception as ex:
                print("Error loading user context on login:", ex)
                state["calendar_url"] = ""
                state["permisos"] = {"comercial", "buscador", "cartera"}

            if requiere_cambio:
                new_pass_field = ft.TextField(
                    label="Nueva contraseña",
                    hint_text="Mínimo 6 caracteres",
                    border_color=COLORS["border"],
                    focused_border_color=COLORS["primary"],
                    border_radius=10,
                    text_size=14,
                    password=True,
                    can_reveal_password=True,
                    width=300,
                )
                
                def do_change(e):
                    if not new_pass_field.value or len(new_pass_field.value) < 6:
                        show_snackbar("La contraseña debe tener al menos 6 caracteres", color=COLORS["warning"])
                        return
                    
                    if actualizar_password(email, new_pass_field.value):
                        show_snackbar("Contraseña actualizada con éxito. ¡Sesión iniciada!")
                        page.dialog.open = False
                        
                        state["loading_login"] = True
                        state["logged_in"] = True
                        current_user_context["user_id"] = state["user_id"]
                        current_user_context["role"] = state["role"]
                        sidebar_selected["index"] = 0
                        state["viewing_dashboard"] = True
                        state["viewing_profile"] = False
                        
                        update_page_layout()
                        page.update()
                        
                        def bg_initialize():
                            import time
                            t_start = time.time()
                            dm.initialize(user_id=state["user_id"], role=state["role"], regional_only=state.get("regional_only", False))
                            elapsed = time.time() - t_start
                            remaining = 0.5 - elapsed
                            if remaining > 0:
                                time.sleep(remaining)
                            state["loading_login"] = False
                            update_page_layout()
                            render_content()
                        
                        page.run_thread(bg_initialize)
                    else:
                        show_snackbar("Error al actualizar la contraseña", color=COLORS["warning"])

                change_btn = ft.FilledButton(
                    "Establecer nueva contraseña",
                    on_click=do_change,
                    style=ft.ButtonStyle(
                        bgcolor=COLORS["primary"],
                        color=COLORS["text_on_primary"],
                        shape=ft.RoundedRectangleBorder(radius=10),
                        padding=ft.Padding(left=20, right=20, top=12, bottom=12),
                    ),
                    width=300,
                )
                
                change_dialog = ft.AlertDialog(
                    modal=True,
                    title=ft.Text("Cambio de Contraseña Obligatorio", size=16, weight=ft.FontWeight.W_700),
                    content=ft.Container(
                        content=ft.Column(
                            controls=[
                                ft.Text("Ingresaste con una contraseña provisoria de un solo uso. Debés cambiarla por seguridad.", size=13, color=COLORS["text_secondary"]),
                                ft.Container(height=8),
                                new_pass_field,
                                ft.Container(height=12),
                                change_btn,
                            ],
                            spacing=4,
                            tight=True,
                            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        ),
                        width=320,
                        padding=10,
                    ),
                )
                page.dialog = change_dialog
                change_dialog.open = True
                page.update()
            else:
                state["loading_login"] = True
                state["logged_in"] = True
                current_user_context["user_id"] = state["user_id"]
                current_user_context["role"] = state["role"]
                sidebar_selected["index"] = 0   # Arrancar en Gestión Comercial
                state["viewing_dashboard"] = True
                state["viewing_profile"] = False
                
                show_snackbar("¡Sesión iniciada con éxito!")
                update_page_layout()
                page.update()
                
                def bg_initialize():
                    import time
                    t_start = time.time()
                    dm.initialize(user_id=state["user_id"], role=state["role"], regional_only=state.get("regional_only", False), api_client=client)
                    elapsed = time.time() - t_start
                    remaining = 0.5 - elapsed
                    if remaining > 0:
                        time.sleep(remaining)
                    state["loading_login"] = False
                    update_page_layout()
                    render_content()

                    
                    try:
                        from notificaciones import obtener_resumen_reuniones, enviar_notificacion_sistema
                        res_notif = obtener_resumen_reuniones()
                        tot_pend = res_notif.get("total_pendientes", 0)
                        tot_hoy = res_notif.get("total_hoy", 0)
                        if tot_pend > 0:
                            msg_notif = f"Tenés {tot_pend} reunión(es) pendiente(s)" + (f" ({tot_hoy} agendada(s) para hoy)." if tot_hoy > 0 else ".")
                            enviar_notificacion_sistema("CRM Seguros - Recordatorio", msg_notif)
                    except Exception as ex:
                        print("[NOTIF LOGIN EXCEPTION]", ex)
                
                page.run_thread(bg_initialize)
        else:
            state["error_login"] = msg_error
            update_page_layout()

    def on_logout(e):
        if state["username"]:
            registrar_log(state["username"], "LOGOUT", "Cierre de sesión manual")
        state["logged_in"] = False
        state["username"] = None
        state["role"] = None
        state["user_id"] = None
        state["error_login"] = None
        if "refresh_dashboard" in state:
            state["refresh_dashboard"] = None
        current_user_context["user_id"] = None
        current_user_context["role"] = None
        
        show_snackbar("Sesión cerrada")
        update_page_layout()
        
        def bg_logout_init():
            dm.initialize(regional_only=state.get("regional_only", False))
        page.run_thread(bg_logout_init)

    def on_forgot_password(username: str):
        if not username:
            show_snackbar("Por favor, ingresá tu usuario", color=COLORS["warning"])
            return
            
        username_clean = username.strip().lower()
        
        # Generar la contraseña provisoria
        res_prov = generar_password_provisorio(username_clean)
        if not res_prov:
            show_snackbar("El usuario ingresado no está registrado en el sistema.", color=COLORS["warning"])
            return
            
        temp_pass, email_dest = res_prov
            
        progress_dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Enviando correo...", size=16, weight=ft.FontWeight.W_600),
            content=ft.Container(
                content=ft.Column(
                    controls=[
                        ft.ProgressRing(color=COLORS["primary"]),
                        ft.Text("Enviando contraseña provisoria...", size=13, color=COLORS["text_secondary"]),
                    ],
                    spacing=12,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    tight=True,
                ),
                padding=20,
                width=180,
            ),
        )
        page.dialog = progress_dialog
        progress_dialog.open = True
        page.update()
        
        def run_send_mail():
            # Intentar enviar por SMTP real
            success = enviar_mail_recuperacion(email_dest, temp_pass)
            
            def on_send_finish():
                page.dialog.open = False
                page.update()
                
                if success:
                    def close_success(e):
                        success_dialog.open = False
                        page.update()
                        
                    success_dialog = ft.AlertDialog(
                        title=ft.Text("Correo Enviado", size=16, weight=ft.FontWeight.W_700),
                        content=ft.Text(
                            f"Se ha enviado un correo con una contraseña provisoria a la dirección registrada para el usuario '{username_clean}' ({email_dest}).\n\n"
                            "Por favor, revisá tu bandeja de entrada o carpeta de spam.",
                            size=13,
                            color=COLORS["text_secondary"]
                        ),
                        actions=[
                            ft.TextButton("Entendido", on_click=close_success)
                        ]
                    )
                    page.dialog = success_dialog
                    success_dialog.open = True
                    page.update()
                else:
                    def close_fallback(e):
                        fallback_dialog.open = False
                        page.update()

                    # Fallback elegante si falla el envío de correo (sin internet o SMTP bloqueado)
                    fallback_dialog = ft.AlertDialog(
                        title=ft.Text("Envío de Correo Fallido", size=16, weight=ft.FontWeight.W_700),
                        content=ft.Container(
                            content=ft.Column(
                                controls=[
                                    ft.Text(
                                        f"No se pudo enviar el correo a {email_dest} mediante el servidor SMTP (verificá tu conexión a internet o la configuración del servidor).", 
                                        size=13, 
                                        color=COLORS["warning"]
                                    ),
                                    ft.Container(height=8),
                                    ft.Text("Para fines de demostración, tu contraseña provisoria de un solo uso es:", size=13, color=COLORS["text_secondary"]),
                                    ft.Container(
                                        content=ft.Text(temp_pass, size=16, weight=ft.FontWeight.W_700, color=COLORS["primary"]),
                                        bgcolor=COLORS["surface_variant"] or "#E5E5E5",
                                        padding=10,
                                        border_radius=8,
                                        alignment=ft.Alignment(0, 0)
                                    )
                                ],
                                tight=True,
                                spacing=4
                            ),
                            width=320
                        ),
                        actions=[
                            ft.TextButton("Entendido", on_click=close_fallback)
                        ]
                    )
                    page.dialog = fallback_dialog
                    fallback_dialog.open = True
                    page.update()
                    
            page.run_thread(on_send_finish)
            
        threading.Thread(target=run_send_mail, daemon=True).start()

    # ── Sidebar state ──────────────────────────────────────
    sidebar_selected = {"index": 0}  # 0=Gestión Comercial, 1=Buscador PAS, 2=Cartera

    def on_sidebar_nav(e):
        idx = e.control.selected_index
        sidebar_selected["index"] = idx
        if idx == 0:
            # Gestión Comercial → Dashboard
            state["viewing_dashboard"] = True
            state["viewing_detail"]    = False
            state["viewing_admin"]     = False
            state["viewing_profile"]   = False
            state["viewing_cartera"]   = False
        elif idx == 2:
            # Cartera
            state["viewing_cartera"]   = True
            state["viewing_dashboard"] = False
            state["viewing_detail"]    = False
            state["viewing_admin"]     = False
            state["viewing_profile"]   = False
        else:
            # Buscador de PAS → tabla principal
            state["viewing_dashboard"] = False
            state["viewing_detail"]    = False
            state["viewing_admin"]     = False
            state["viewing_profile"]   = False
            state["viewing_cartera"]   = False
        update_page_layout()
        render_content()
        update_header()

    def build_sidebar():
        is_dark = COLORS["surface"] == "#1E293B"
        sidebar_bg     = "#111827" if is_dark else "#FFFFFF"
        active_color   = COLORS["primary"]
        inactive_color = "#94A3B8" if is_dark else "#64748B"

        # ── Estado de expansión (persiste entre builds) ──────────────────────
        if "sidebar_expanded" not in sidebar_selected:
            sidebar_selected["sidebar_expanded"] = False   # colapsar por defecto
        expanded = sidebar_selected["sidebar_expanded"]
        W_EXPANDED  = 220
        W_COLLAPSED = 72

        def toggle_expand(e):
            sidebar_selected["sidebar_expanded"] = not sidebar_selected["sidebar_expanded"]
            update_page_layout()

        def nav_item(icon_name, label, index):
            is_active = sidebar_selected["index"] == index

            # Permisos dinámicos
            if state.get("logged_in"):
                perm_map = {0: "comercial", 1: "buscador", 2: "cartera"}
                if perm_map.get(index) not in state.get("permisos", set()):
                    return None

            icon_color = active_color if is_active else inactive_color
            text_color = active_color if is_active else inactive_color
            pill_bg    = ft.Colors.with_opacity(0.12, active_color) if is_active else "transparent"

            def _click(e, i=index):
                on_sidebar_nav(type("E", (), {"control": type("C", (), {"selected_index": i})()})())

            if expanded:
                return ft.Container(
                    content=ft.Row(
                        controls=[
                            ft.Container(
                                content=ft.Icon(icon_name, color=icon_color, size=20),
                                width=36, height=36,
                                border_radius=18,
                                alignment=ft.Alignment(0, 0),
                            ),
                            ft.Text(
                                label, size=13, color=text_color,
                                weight=ft.FontWeight.W_600 if is_active else ft.FontWeight.W_400,
                                no_wrap=True, expand=True,
                            ),
                        ],
                        spacing=12,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                    bgcolor=pill_bg,
                    border_radius=50,
                    padding=ft.Padding(left=14, right=18, top=10, bottom=10),
                    margin=ft.Margin(left=8, right=8, top=2, bottom=2),
                    on_click=_click,
                    ink=True,
                    animate=ft.Animation(180, "easeOut"),
                )
            else:
                return ft.Container(
                    content=ft.Container(
                        content=ft.Icon(icon_name, color=icon_color, size=20),
                        width=44, height=44,
                        border_radius=22,
                        bgcolor=pill_bg,
                        alignment=ft.Alignment(0, 0),
                    ),
                    tooltip=label,
                    alignment=ft.Alignment(0, 0),
                    margin=ft.Margin(left=0, right=0, top=2, bottom=2),
                    on_click=_click,
                    ink=True,
                    animate=ft.Animation(180, "easeOut"),
                )

        # ── Hamburger + Logo header ───────────────────────────────────────────
        hamburger = ft.IconButton(
            icon=ft.Icons.MENU_ROUNDED,
            icon_color=inactive_color,
            icon_size=20,
            tooltip="Expandir / colapsar menú",
            on_click=toggle_expand,
            style=ft.ButtonStyle(
                overlay_color=ft.Colors.with_opacity(0.08, active_color),
                shape=ft.RoundedRectangleBorder(radius=12),
            ),
        )

        _logo_path = "LogoJCOrg.png"   # assets/LogoJCOrg.png — Flet lo resuelve desde assets/

        if expanded:
            header_row = ft.Container(
                content=ft.Row(
                    controls=[
                        hamburger,
                        ft.Image(
                            src=_logo_path,
                            width=120,
                            height=36,
                            tooltip="CRM Seguros",
                        ),
                    ],
                    spacing=4,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                padding=ft.Padding(left=4, right=12, top=12, bottom=10),
            )
        else:
            header_row = ft.Container(
                content=ft.Column(
                    controls=[
                        hamburger,
                        ft.Image(
                            src=_logo_path,
                            width=38,
                            height=38,
                            tooltip="CRM Seguros",
                        ),
                    ],
                    spacing=4,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                padding=ft.Padding(left=0, right=0, top=12, bottom=10),
                alignment=ft.Alignment(0, 0),
            )

        divider = ft.Container(
            content=ft.Divider(height=1, color=ft.Colors.with_opacity(0.08, "#000000")),
            padding=ft.Padding(left=10, right=10, top=0, bottom=0),
        )

        nav_items = [item for item in [
            nav_item(ft.Icons.TRENDING_UP_ROUNDED,  "Gestión Comercial", 0),
            nav_item(ft.Icons.SEARCH_ROUNDED,       "Red de PAS",        1),
            nav_item(ft.Icons.FOLDER_SPECIAL_ROUNDED, "Cartera",         2),
        ] if item is not None]

        def _bottom_btn(icon, tip, cb):
            if expanded:
                return ft.Container(
                    content=ft.Row([
                        ft.Icon(icon, color=inactive_color, size=20),
                        ft.Text(tip, size=13, color=inactive_color),
                    ], spacing=12, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                    padding=ft.Padding(left=14, right=18, top=10, bottom=10),
                    margin=ft.Margin(left=8, right=8, top=1, bottom=1),
                    border_radius=50,
                    on_click=cb, ink=True,
                )
            else:
                return ft.Container(
                    content=ft.Icon(icon, color=inactive_color, size=20),
                    tooltip=tip, padding=10, border_radius=22,
                    alignment=ft.Alignment(0, 0),
                    on_click=cb, ink=True,
                )

        bottom_col = ft.Column(
            controls=[
                _bottom_btn(ft.Icons.PERSON_ROUNDED, "Mi Perfil",
                            lambda e: open_profile_panel()),
                _bottom_btn(ft.Icons.LOGOUT_ROUNDED, "Cerrar sesión", on_logout),
                ft.Container(height=12),
            ],
            spacing=0,
            horizontal_alignment=(
                ft.CrossAxisAlignment.STRETCH if expanded
                else ft.CrossAxisAlignment.CENTER
            ),
        )

        sidebar_content = ft.Column(
            controls=[
                header_row,
                divider,
                ft.Container(height=8),
                *nav_items,
                ft.Container(expand=True),
                bottom_col,
            ],
            spacing=0,
            expand=True,
            horizontal_alignment=(
                ft.CrossAxisAlignment.STRETCH if expanded
                else ft.CrossAxisAlignment.CENTER
            ),
        )

        return ft.Container(
            content=sidebar_content,
            bgcolor=sidebar_bg,
            width=W_EXPANDED if expanded else W_COLLAPSED,
            expand=False,
            border=ft.Border(right=ft.BorderSide(1, ft.Colors.with_opacity(0.08, "#000000"))),
            animate=ft.Animation(200, "easeOut"),
        )

    # ── Áreas de layout ───────────────────────────────────
    content_column = ft.Column(spacing=0, expand=True)
    sidebar_ref    = ft.Ref[ft.Container]()
    main_row       = ft.Row(spacing=0, expand=True, controls=[content_column])

    layout_container = ft.Container(
        content=ft.Column(
            controls=[main_row],
            spacing=0,
            expand=True,
        ),
        expand=True,
        bgcolor=COLORS["background"],
        animate=400,
    )
    page.controls = [layout_container]

    def on_activate(license_key):
        state["error_license"] = "Validando..."
        page.update()
        ok, msg = client.validar_licencia_online(license_key)
        if ok:
            state["license_valid"] = True
            state["error_license"] = None
        else:
            state["license_valid"] = False
            state["error_license"] = msg
        update_page_layout()

    def update_page_layout():
        if state.get("logged_in") and state.get("user_id"):
            try:
                from ssn_test import obtener_usuarios
                users_list = obtener_usuarios()
                curr_user = next((u for u in users_list if u["id"] == state["user_id"]), None)
                if curr_user:
                    state["calendar_url"] = curr_user.get("calendar_url") or ""
                    p_str = curr_user.get("permisos") or "comercial,buscador,cartera"
                    state["permisos"] = {p.strip() for p in p_str.split(",") if p.strip()}
                    state["role"] = curr_user.get("rol") or "agente"
            except Exception as ex:
                print("Error dynamically reloading user permissions:", ex)

        layout_container.bgcolor = COLORS["background"]
        if not state.get("license_valid", False) or not state.get("logged_in", False):
            if state.get("reactivating_license", False):
                from ui_components import build_reactivation_loading_view
                reactivation_view = build_reactivation_loading_view()
                content_column.controls = [
                    ft.Container(
                        content=reactivation_view,
                        alignment=ft.Alignment(0, 0),
                        expand=True,
                    )
                ]
                main_row.controls = [content_column]
            else:
                from api_client import obtener_fingerprint
                license_valid = state.get("license_valid", False)
                initial_tab = "licencia" if not license_valid else "login"
                
                login_card = build_login_view(
                    on_login=on_login,
                    on_forgot_password=on_forgot_password,
                    on_activate=on_activate,
                    license_valid=license_valid,
                    initial_tab=initial_tab,
                    error_text=state.get("error_login"),
                    error_license=state.get("error_license"),
                    current_license_key=client.license_key,
                    fingerprint=obtener_fingerprint(),
                    saved_username=client.saved_username,
                    saved_password=client.saved_password,
                    version=APP_VERSION,
                )
                content_column.controls = [
                    ft.Container(
                        content=login_card,
                        alignment=ft.Alignment(0, 0),
                        expand=True,
                    )
                ]
                main_row.controls = [content_column]
        elif state.get("loading_login", False):
            # Pantalla de bienvenida intermedia
            welcome_view = build_welcome_loading_view(state.get("username", ""))
            content_column.controls = [
                ft.Container(
                    content=welcome_view,
                    alignment=ft.Alignment(0, 0),
                    expand=True,
                )
            ]
            main_row.controls = [content_column]
        else:
            update_header()
            sidebar_widget = build_sidebar()

            if (state.get("viewing_dashboard") or 
                state.get("viewing_cartera") or 
                state.get("viewing_admin") or 
                state.get("viewing_profile") or 
                state.get("viewing_detail")):
                content_column.controls = [
                    header_wrap,
                    main_content,
                    footer_wrap,
                ]
            else:
                content_column.controls = [
                    header_wrap,
                    initial_search,
                    ft.Container(ref=stats_ref),
                    main_content,
                    footer_wrap,
                ]
                update_stats()

            main_row.controls = [sidebar_widget, content_column]
        page.update()

    dm = DataManager()
    dm.on_load_success     = on_load_success
    dm.on_load_error       = on_load_error
    dm.on_update_available = on_update_available
    dm.on_update_error     = on_update_error

    from data_manager import get_cache_date
    state["cache_date"] = get_cache_date()

    initial_header = build_header(0, on_theme_click=toggle_theme)
    header_wrap = ft.Container(
        ref=header_ref,
        content=initial_header.content,
        bgcolor=initial_header.bgcolor,
        padding=initial_header.padding,
        shadow=initial_header.shadow,
    )

    from ssn_test import obtener_ultima_actualizacion
    initial_search = build_search_bar(
        on_change=on_search_change,
        on_ramo_change=on_ramo_change,
        on_provincia_change=on_provincia_change,
        on_localidad_change=on_localidad_change,
        on_estado_change=on_estado_change,
        on_settings_click=open_custom_filters_dialog,
        search_ref=search_ref,
        settings_btn_ref=settings_btn_ref,
        provincia_dropdown=provincia_dropdown,
        localidad_dropdown=localidad_dropdown,
        estado_dropdown=estado_dropdown,
        provincia_dropdown2=provincia_dropdown2,
        localidad_dropdown2=localidad_dropdown2,
        on_provincia2_change=on_provincia2_change,
        on_localidad2_change=on_localidad2_change,
        on_export_click=export_to_csv,
        on_import_click=trigger_import_picker,
        on_submit=on_search_submit,
        is_admin=(state.get("role") == "admin"),
        ultima_actualizacion=obtener_ultima_actualizacion(),
        on_vaciar_db_click=on_vaciar_db_click,
        on_admin_click=open_admin_panel,
        mostly_complete_value=state.get("mostly_complete", False),
        on_mostly_complete_change=on_mostly_complete_change,
        sort_descending_value=state.get("sort_descending", False),
        on_sort_direction_change=on_sort_direction_change,
        selected_ramo=state.get("ramo"),
        regional_only_value=state.get("regional_only", False),
        on_regional_only_change=on_regional_only_change,
    )
    initial_footer = build_footer(state["cache_date"])

    main_content = ft.Column(
        ref=content_area,
        controls=[build_loading_state()],
        spacing=0,
        expand=True,
    )

    footer_wrap = ft.Container(
        ref=footer_container,
        content=initial_footer.content,
        bgcolor=initial_footer.bgcolor,
        padding=initial_footer.padding,
        border=initial_footer.border,
    )

    # Validar licencia guardada automáticamente al arrancar
    if client.license_key:
        state["license_valid"] = True
        state["error_license"] = None
    else:
        state["license_valid"] = False
        state["error_license"] = None

    # Iniciar en la pantalla de login/licencia
    update_page_layout()

    def after_render():
        time.sleep(0.1)
        dm.initialize(regional_only=state.get("regional_only", False), api_client=client)

        
        # Validar la licencia guardada online en background para no bloquear el inicio
        if client.license_key:
            def bg_validate_license():
                ok, msg = client.validar_licencia_online(client.license_key)
                if not ok:
                    state["license_valid"] = False
                    state["error_license"] = msg
                    if state.get("logged_in", False):
                        state["logged_in"] = False
                        state["username"] = None
                        state["role"] = None
                        state["user_id"] = None
                        current_user_context["user_id"] = None
                        current_user_context["role"] = None
                    page.run_thread(update_page_layout)
            
            threading.Thread(target=bg_validate_license, daemon=True).start()
        
        # Hilo de verificación periódica de licencia (heartbeat de enforcement en tiempo real)
        def check_license_loop():
            import time as _time
            while True:
                _time.sleep(120)
                if client.license_key:
                    ok, msg = client.validar_licencia_online(client.license_key)
                    if ok:
                        # Si antes la licencia estaba marcada como inválida y ahora es válida (reactivación)
                        if not state.get("license_valid", False):
                            state["license_valid"] = True
                            state["error_license"] = None
                            state["reactivating_license"] = True
                            page.run_thread(update_page_layout)
                            _time.sleep(4) # Espera visual de la imagen
                            state["reactivating_license"] = False
                            page.run_thread(update_page_layout)
                    else:
                        # Si no es válida por razones explícitas (suspensión, eliminación, etc)
                        # Ignoramos fallas temporales de red/conexión y errores de servidor/HTTP/rate-limit
                        if ("conexión" not in msg.lower() and 
                            "connect" not in msg.lower() and 
                            "http" not in msg.lower() and 
                            "servidor" not in msg.lower()):
                            if state.get("license_valid", False):
                                state["license_valid"] = False
                                state["error_license"] = msg
                                # Forzar cierre inmediato de sesión si el usuario está logueado
                                if state.get("logged_in", False):
                                    state["logged_in"] = False
                                    state["username"] = None
                                    state["role"] = None
                                    state["user_id"] = None
                                    current_user_context["user_id"] = None
                                    current_user_context["role"] = None
                                
                                # Actualizar UI en el hilo principal de Flet
                                page.run_thread(update_page_layout)
        
        threading.Thread(target=check_license_loop, daemon=True).start()
        
        # Iniciar check de actualización tras renderizar la interfaz
        iniciar_check_actualizacion(page, client)

    threading.Thread(target=after_render, daemon=True).start()


if __name__ == "__main__":
    import os
    # Enforce localhost binding for Flet's underlying web server
    # This prevents anyone on the local network (LAN/Wi-Fi) from accessing the application
    os.environ["FLET_SERVER_IP"] = "127.0.0.1"
    
    inicializar_db()
    ft.run(
        main=main,
        assets_dir="assets",
        name=APP_NAME,
    )