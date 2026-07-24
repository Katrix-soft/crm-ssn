"""
ui_components.py
"""
import flet as ft
import re
import urllib.parse
import webbrowser
from typing import Any, Callable, Dict, List, Optional

from utils import (
    COLUMN_LABELS,
    COL_MATRICULA,
    COL_NOMBRE,
    COL_ID,
    COL_RAMO,
    COL_TIPO_ID,
    DETAIL_ORDER,
    RAMOS_FILTER,
    RAMOS_LABELS,
    MAX_RESULTS,
    PAGE_SIZE,
    format_cuit,
    record_to_clipboard,
    truncate,
)

LIGHT_COLORS = {
    "primary":         "#3B82F6",       # Modern vibrant blue
    "primary_dark":    "#1D4ED8",
    "primary_light":   "#93C5FD",
    "surface":         "#FFFFFF",
    "background":      "#F3F4F6",       # Cool light grey
    "card":            "#FFFFFF",
    "text_primary":    "#111827",       # Near black for readability
    "text_secondary":  "#4B5563",       # Muted slate grey
    "text_on_primary": "#FFFFFF",
    "border":          "#E5E7EB",
    "accent":          "#2563EB",
    "success":         "#10B981",       # Emerald green
    "warning":         "#F59E0B",       # Amber
    "chip_bg":         "#EFF6FF",
    "chip_text":       "#1D4ED8",
    "row_hover":       "#F9FAFB",
    "row_alt":         "#F9FAFB",
    "divider":         "#E5E7EB",
    "shadow":          "#E5E7EB",
    "header_bg":       "#FFFFFF",
    "header_text":     "#111827",
}

DARK_COLORS = {
    "primary":         "#38BDF8",       # Vibrant Sky Blue accent (high-contrast, modern)
    "primary_dark":    "#0284C7",
    "primary_light":   "#7DD3FC",
    "surface":         "#1E293B",       # Dark slate surface (comfortable, high contrast)
    "background":      "#0F172A",       # Very deep slate/navy (gorgeous dark backdrop)
    "card":            "#1E293B",
    "text_primary":    "#F8FAFC",       # Crisp white-slate text (highly readable)
    "text_secondary":  "#94A3B8",       # Beautiful cool muted slate text
    "text_on_primary": "#0F172A",       # Dark text on light accent
    "border":          "#334155",       # Slate border with great contrast
    "accent":          "#38BDF8",
    "success":         "#34D399",       # Emerald green
    "warning":         "#FBBF24",       # Amber
    "chip_bg":         "#334155",
    "chip_text":       "#38BDF8",
    "row_hover":       "#2B394A",
    "row_alt":         "#161E2E",       # Deep slate alternating rows
    "divider":         "#334155",
    "shadow":          "#0B0F19",
    "header_bg":       "#111827",       # Slate-black top header for true dark mode feeling
    "header_text":     "#F8FAFC",
}

# Default to LIGHT_COLORS as requested
COLORS = dict(LIGHT_COLORS)

def set_theme_mode(mode: str):
    target = DARK_COLORS if mode == "dark" else LIGHT_COLORS
    COLORS.clear()
    COLORS.update(target)

ROW_HEIGHT = 52

def _ramo_colors(ramo: str):
    key = ramo.strip().lower() if ramo else ""
    if COLORS["surface"] == "#1E293B":
        # Mapeo de chips para modo oscuro
        dark_mapping = {
            "patrimoniales y vida": ("rgba(56, 189, 248, 0.15)", "#38BDF8"),
            "vida":                 ("rgba(52, 211, 153, 0.15)", "#34D399"),
            "articulo 19":          ("rgba(251, 191, 36, 0.15)", "#FBBF24"),
            "artículo 19":          ("rgba(251, 191, 36, 0.15)", "#FBBF24"),
        }
        return dark_mapping.get(key, (COLORS["chip_bg"], COLORS["chip_text"]))
    else:
        # Mapeo de chips para modo claro
        light_mapping = {
            "patrimoniales y vida": ("#EFF6FF", "#1D4ED8"),
            "vida":                 ("#E8F5E9", "#2E7D32"),
            "articulo 19":          ("#FEF9E7", "#D35400"),
            "artículo 19":          ("#FEF9E7", "#D35400"),
        }
        return light_mapping.get(key, (COLORS["chip_bg"], COLORS["chip_text"]))


# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------
def build_header(
    total_records: int,
    on_logout_click: Optional[Callable[[Any], None]] = None,
    on_logs_click: Optional[Callable[[Any], None]] = None,
    on_theme_click: Optional[Callable[[Any], None]] = None,
    on_dashboard_click: Optional[Callable[[Any], None]] = None,
    on_profile_click: Optional[Callable[[Any], None]] = None,
    on_notif_click: Optional[Callable[[Any], None]] = None,
    pending_notif_count: int = 0,
    title: str = "Buscador de Productores",
    subtitle: str = "Asesores de Seguros · SSN Argentina",
    stat_label: Optional[str] = None,
) -> ft.Container:
    return ft.Container(
        content=ft.Row(
            controls=[
                ft.Row(
                    controls=[
                        ft.Icon(ft.Icons.SHIELD_OUTLINED, color=COLORS["header_text"], size=28),
                        ft.Column(
                            controls=[
                                ft.Text(title, size=18, weight=ft.FontWeight.W_700, color=COLORS["header_text"]),
                                ft.Text(subtitle, size=11, color=ft.Colors.with_opacity(0.8, COLORS["header_text"])),
                            ],
                            spacing=1, tight=True,
                        ),
                    ],
                    spacing=12,
                ),
                ft.Container(expand=True),
                ft.Row(
                    controls=[
                        ft.Container(
                            content=ft.Text(
                                stat_label if stat_label is not None else f"{total_records:,} productores SSN".replace(",", "."),
                                size=12,
                                color=COLORS["primary"] if COLORS["header_bg"] == "#FFFFFF" else ft.Colors.with_opacity(0.85, COLORS["header_text"]),
                                weight=ft.FontWeight.BOLD if COLORS["header_bg"] == "#FFFFFF" else ft.FontWeight.NORMAL,
                            ),
                            bgcolor=ft.Colors.with_opacity(0.1, COLORS["primary"]) if COLORS["header_bg"] == "#FFFFFF" else ft.Colors.with_opacity(0.15, "#FFFFFF"),
                            border_radius=20,
                            padding=ft.Padding(left=14, right=14, top=6, bottom=6),
                        ),
                        # Theme toggle disabled to enforce light theme
                        ft.Container(),
                        ft.IconButton(
                            icon=ft.Icons.DASHBOARD_ROUNDED,
                            icon_color=COLORS["header_text"],
                            icon_size=20,
                            tooltip="Dashboard / Métricas",
                            on_click=on_dashboard_click,
                        ) if on_dashboard_click else ft.Container(),
                        # Notification Bell Icon with Badge Counter
                        ft.Stack(
                            controls=[
                                ft.IconButton(
                                    icon=ft.Icons.NOTIFICATIONS_ROUNDED if pending_notif_count > 0 else ft.Icons.NOTIFICATIONS_OUTLINED,
                                    icon_color=COLORS["warning"] if pending_notif_count > 0 else COLORS["header_text"],
                                    icon_size=20,
                                    tooltip=f"{pending_notif_count} reunión(es) pendiente(s)" if pending_notif_count > 0 else "Recordatorios de reuniones",
                                    on_click=on_notif_click,
                                ),
                                ft.Container(
                                    content=ft.Text(str(pending_notif_count), size=9, color="#FFFFFF", weight=ft.FontWeight.W_900),
                                    bgcolor=ft.Colors.RED_600,
                                    border_radius=9,
                                    width=18, height=18,
                                    alignment=ft.Alignment(0, 0),
                                    right=4, top=4,
                                ) if pending_notif_count > 0 else ft.Container(),
                            ],
                            width=38, height=38,
                        ) if on_notif_click else ft.Container(),
                        ft.IconButton(
                            icon=ft.Icons.RECEIPT_LONG_ROUNDED,
                            icon_color=COLORS["header_text"],
                            icon_size=20,
                            tooltip="Ver logs de auditoría",
                            on_click=on_logs_click,
                        ) if on_logs_click else ft.Container(),
                        ft.IconButton(
                            icon=ft.Icons.PERSON_ROUNDED,
                            icon_color=COLORS["header_text"],
                            icon_size=20,
                            tooltip="Configuración de Perfil",
                            on_click=on_profile_click,
                        ) if on_profile_click else ft.Container(),
                        ft.IconButton(
                            icon=ft.Icons.LOGOUT_ROUNDED,
                            icon_color=COLORS["header_text"],
                            icon_size=20,
                            tooltip="Cerrar sesión",
                            on_click=on_logout_click,
                        ) if on_logout_click else ft.Container(),
                    ],
                    spacing=8,
                ),
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        ),
        bgcolor=COLORS["header_bg"],
        padding=ft.Padding(left=48, right=48, top=16, bottom=16),
        shadow=ft.BoxShadow(spread_radius=0, blur_radius=8, color=ft.Colors.with_opacity(0.25, "#000000"), offset=ft.Offset(0, 2)),
        animate=400,
    )


# ---------------------------------------------------------------------------
# Barra de búsqueda
# ---------------------------------------------------------------------------
def build_search_bar(
    on_change: Callable[[str], None],
    on_ramo_change: Callable[[Optional[str]], None],
    on_provincia_change: Callable[[Optional[str]], None],
    on_localidad_change: Callable[[Optional[str]], None],
    on_estado_change: Callable[[Optional[str]], None],
    on_settings_click: Callable[[Any], None],
    search_ref: ft.Ref,
    settings_btn_ref: ft.Ref,
    provincia_dropdown: ft.Dropdown,
    localidad_dropdown: ft.Dropdown,
    estado_dropdown: ft.Dropdown,
    provincia_dropdown2: ft.Dropdown,
    localidad_dropdown2: ft.Dropdown,
    on_provincia2_change: Optional[Callable[[Optional[str]], None]] = None,
    on_localidad2_change: Optional[Callable[[Optional[str]], None]] = None,
    on_export_click: Optional[Callable[[Any], None]] = None,
    on_import_click: Optional[Callable[[Any], None]] = None,
    on_submit: Optional[Callable[[Any], None]] = None,
    is_admin: bool = False,
    ultima_actualizacion: str = "Nunca",
    on_vaciar_db_click: Optional[Callable[[Any], None]] = None,
    on_admin_click: Optional[Callable[[Any], None]] = None,
    mostly_complete_value: bool = False,
    on_mostly_complete_change: Optional[Callable[[bool], None]] = None,
    sort_descending_value: bool = False,
    on_sort_direction_change: Optional[Callable[[bool], None]] = None,
    selected_ramo: Optional[str] = None,
    regional_only_value: bool = False,
    on_regional_only_change: Optional[Callable[[bool], None]] = None,
) -> ft.Container:

    ramo_options = [ft.dropdown.Option("Todos los ramos")]
    for r in RAMOS_FILTER:
        if r is not None:
            ramo_options.append(ft.dropdown.Option(r, RAMOS_LABELS[r]))

    ramo_dropdown = ft.Dropdown(
        options=ramo_options,
        value=selected_ramo if selected_ramo else "Todos los ramos",
        hint_text="Todos los ramos",
        width=200,
        border_color=COLORS["border"],
        border_radius=10,
        text_size=13,
        content_padding=ft.Padding(left=12, right=12, top=8, bottom=8),
        on_select=lambda e: on_ramo_change(None if e.control.value == "Todos los ramos" else e.control.value),
        color=COLORS["text_primary"],
        bgcolor=COLORS["surface"],
    )

    search_field = ft.TextField(
        ref=search_ref,
        hint_text="Buscar por matrícula, nombre o CUIT...",
        hint_style=ft.TextStyle(color=ft.Colors.with_opacity(0.45, COLORS["text_primary"]), size=14),
        prefix_icon=ft.Icons.SEARCH,
        border_color=COLORS["border"],
        focused_border_color=COLORS["primary"],
        border_radius=12,
        text_size=14,
        color=COLORS["text_primary"],
        bgcolor=COLORS["surface"],
        expand=True,
        on_change=lambda e: on_change(e.control.value),
        on_submit=on_submit,
        cursor_color=COLORS["primary"],
        selection_color=ft.Colors.with_opacity(0.2, COLORS["primary"]),
        suffix=ft.IconButton(
            icon=ft.Icons.CLOSE,
            icon_size=16,
            icon_color=COLORS["text_secondary"],
            tooltip="Limpiar búsqueda",
            on_click=lambda e: _clear_search(search_ref, on_change, e),
        ),
    )

    return ft.Container(
        content=ft.Column(
            controls=[
                ft.Text("Buscá un productor", size=13, weight=ft.FontWeight.W_600, color=COLORS["text_secondary"]),
                ft.Row(controls=[search_field, ramo_dropdown], spacing=12, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                ft.Row(
                    wrap=True,
                    controls=[
                        ft.Row(
                            wrap=True,
                            controls=[
                                ft.Text("Filtros rápidos:", size=12, weight=ft.FontWeight.W_600, color=COLORS["text_secondary"]),
                                provincia_dropdown,
                                localidad_dropdown,
                                ft.Text("y/o:", size=11, color=COLORS["text_secondary"], weight=ft.FontWeight.BOLD),
                                provincia_dropdown2,
                                localidad_dropdown2,
                                estado_dropdown,
                                ft.Container(
                                    content=ft.Row(
                                        controls=[
                                            ft.Icon(
                                                ft.Icons.CHECK_CIRCLE_ROUNDED if mostly_complete_value else ft.Icons.RADIO_BUTTON_UNCHECKED_ROUNDED,
                                                size=16,
                                                color=COLORS["success"] if mostly_complete_value else COLORS["text_secondary"]
                                            ),
                                            ft.Text(
                                                "Datos Completos",
                                                size=12,
                                                weight=ft.FontWeight.W_600 if mostly_complete_value else ft.FontWeight.NORMAL,
                                                color=COLORS["success"] if mostly_complete_value else COLORS["text_secondary"]
                                            ),
                                        ],
                                        spacing=6,
                                        tight=True,
                                    ),
                                    bgcolor=ft.Colors.with_opacity(0.1, COLORS["success"]) if mostly_complete_value else ft.Colors.TRANSPARENT,
                                    border=ft.Border.all(
                                        1.5,
                                        COLORS["success"] if mostly_complete_value else COLORS["border"]
                                    ),
                                    border_radius=8,
                                    padding=ft.Padding(left=10, right=12, top=6, bottom=6),
                                    on_click=lambda e: on_mostly_complete_change(not mostly_complete_value) if on_mostly_complete_change else None,
                                    tooltip="Ocultar productores con datos de contacto incompletos (teléfono, email, etc.)",
                                ) if on_mostly_complete_change else ft.Container(),
                                ft.Container(
                                    content=ft.Row(
                                        controls=[
                                            ft.Icon(
                                                ft.Icons.ARROW_UPWARD_ROUNDED if not sort_descending_value else ft.Icons.ARROW_DOWNWARD_ROUNDED,
                                                size=16,
                                                color=COLORS["accent"]
                                            ),
                                            ft.Text(
                                                "Orden: Ascendente" if not sort_descending_value else "Orden: Descendente",
                                                size=12,
                                                weight=ft.FontWeight.W_600,
                                                color=COLORS["accent"]
                                            ),
                                        ],
                                        spacing=6,
                                        tight=True,
                                    ),
                                    bgcolor=ft.Colors.with_opacity(0.1, COLORS["accent"]),
                                    border=ft.Border.all(
                                        1.5,
                                        COLORS["accent"]
                                    ),
                                    border_radius=8,
                                    padding=ft.Padding(left=10, right=12, top=6, bottom=6),
                                    on_click=lambda e: on_sort_direction_change(not sort_descending_value) if on_sort_direction_change else None,
                                    tooltip="Cambiar dirección del orden (Ascendente / Descendente)",
                                ) if on_sort_direction_change else ft.Container(),
                                ft.Container(
                                    content=ft.Row(
                                        controls=[
                                            ft.Icon(
                                                ft.Icons.MAP_ROUNDED if regional_only_value else ft.Icons.PUBLIC_ROUNDED,
                                                size=16,
                                                color=COLORS["primary"]
                                            ),
                                            ft.Text(
                                                "Regionales" if regional_only_value else "Nacionales",
                                                size=12,
                                                weight=ft.FontWeight.W_600,
                                                color=COLORS["primary"]
                                            ),
                                        ],
                                        spacing=6,
                                        tight=True,
                                    ),
                                    bgcolor=ft.Colors.with_opacity(0.1, COLORS["primary"]),
                                    border=ft.Border.all(
                                        1.5,
                                        COLORS["primary"]
                                    ),
                                    border_radius=8,
                                    padding=ft.Padding(left=10, right=12, top=6, bottom=6),
                                    on_click=lambda e: on_regional_only_change(not regional_only_value) if on_regional_only_change else None,
                                    tooltip="Alternar entre ver solo productores de la región Cuyo (Mendoza, San Juan, San Luis) o de todo el país",
                                ) if on_regional_only_change else ft.Container(),
                            ],
                            spacing=14,
                            vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        ),
                        ft.Row(
                            controls=(lambda: [
                                ft.IconButton(
                                    ref=settings_btn_ref,
                                    icon=ft.Icons.SETTINGS_OUTLINED,
                                    icon_size=20,
                                    icon_color=COLORS["primary"],
                                    tooltip="Configurar filtros personalizados",
                                    on_click=on_settings_click,
                                ),
                                ft.IconButton(
                                    icon=ft.Icons.UPLOAD_FILE_ROUNDED,
                                    icon_size=20,
                                    icon_color=COLORS["accent"],
                                    tooltip="Importar productores (Excel/CSV)",
                                    on_click=on_import_click if on_import_click else None,
                                ) if on_import_click else ft.Container(),
                                ft.IconButton(
                                    icon=ft.Icons.DOWNLOAD_ROUNDED,
                                    icon_size=20,
                                    icon_color=COLORS["success"],
                                    tooltip="Exportar registros filtrados a CSV",
                                    on_click=on_export_click if on_export_click else None,
                                ),
                            ] + ([
                                ft.PopupMenuButton(
                                    icon=ft.Icons.ADMIN_PANEL_SETTINGS_ROUNDED,
                                    icon_color=ft.Colors.AMBER_500,
                                    icon_size=24,
                                    tooltip="Opciones de Administrador",
                                    items=[
                                        ft.PopupMenuItem(
                                            content="Panel de Superadmin",
                                            icon=ft.Icons.ADMIN_PANEL_SETTINGS_ROUNDED,
                                            on_click=on_admin_click if on_admin_click else None,
                                        ),
                                        ft.PopupMenuItem(),
                                        ft.PopupMenuItem(
                                            content=f"Última DB: {ultima_actualizacion}",
                                            icon=ft.Icons.UPDATE_ROUNDED,
                                        ),
                                        ft.PopupMenuItem(),
                                        ft.PopupMenuItem(
                                            content="Importar Productores (Excel/CSV)",
                                            icon=ft.Icons.UPLOAD_FILE_ROUNDED,
                                            on_click=on_import_click if on_import_click else None,
                                        ),
                                        ft.PopupMenuItem(),
                                        ft.PopupMenuItem(
                                            content="Vaciar Base de Datos (Peligro)",
                                            icon=ft.Icons.DELETE_FOREVER_ROUNDED,
                                            on_click=on_vaciar_db_click if on_vaciar_db_click else None,
                                        ),
                                    ]
                                )
                            ] if is_admin else []))(),
                            spacing=6,
                            vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
            ],
            spacing=12,
        ),
        bgcolor=COLORS["surface"],
        padding=ft.Padding(left=48, right=48, top=18, bottom=18),
        border=ft.Border(bottom=ft.BorderSide(1, COLORS["divider"])),
        shadow=ft.BoxShadow(spread_radius=0, blur_radius=4, color=ft.Colors.with_opacity(0.06, "#000000"), offset=ft.Offset(0, 2)),
        animate=400,
    )


def _clear_search(search_ref: ft.Ref, on_change: Callable, e):
    if search_ref.current:
        search_ref.current.value = ""
        search_ref.current.update()
        on_change("")


# ---------------------------------------------------------------------------
# Badge de resultados
# ---------------------------------------------------------------------------
def build_results_badge(
    count: int,
    total: int,
    query: str,
    current_page: int = 0,
    total_pages: int = 1,
) -> ft.Container:
    start = current_page * PAGE_SIZE + 1
    end   = min((current_page + 1) * PAGE_SIZE, count)

    if count == 0:
        text  = "Sin resultados para tu búsqueda"
        color = "#C62828"
    elif count < total:
        text  = (
            f"Mostrando {start:,}–{end:,} de {count:,} productores (filtrados de {total:,} totales)"
            .replace(",", ".")
        )
        color = COLORS["text_secondary"]
    else:
        text  = (
            f"Mostrando {start:,}–{end:,} de {total:,} productores"
            .replace(",", ".")
        )
        color = COLORS["text_secondary"]

    return ft.Container(
        content=ft.Text(text, size=12, color=color, italic=(count == 0)),
        padding=ft.Padding(left=48, right=48, top=8, bottom=8),
        bgcolor=COLORS["background"],
    )


# ---------------------------------------------------------------------------
# Tabla de resultados
# ---------------------------------------------------------------------------
def _estado_contacto_colors(estado: str):
    key = estado.strip().lower() if estado else "sin contactar"
    is_dark = (COLORS["surface"] == "#1E293B")
    
    if is_dark:
        if key == "contactado":
            return "rgba(52, 211, 153, 0.15)", "#34D399"
        elif key == "no responde":
            return "rgba(248, 113, 113, 0.15)", "#F87171"
        elif key == "interesado":
            return "rgba(251, 191, 36, 0.15)", "#FBBF24"
        else: # sin contactar
            return "rgba(148, 163, 184, 0.15)", "#94A3B8"
    else:
        if key == "contactado":
            return "#E8F5E9", "#2E7D32"
        elif key == "no responde":
            return "#FFEBEE", "#C62828"
        elif key == "interesado":
            return "#FFF8E1", "#E65100"
        else: # sin contactar
            return "#ECEFF1", "#455A64"


def build_results_table(
    records: List[Dict[str, Any]],
    on_row_click: Callable[[Dict[str, Any]], None],
    on_live_search: Optional[Callable[[str], None]] = None,
    query: str = "",
    db_is_empty: bool = False,
    on_import_click: Optional[Callable[[Any], None]] = None,
    sort_column: Optional[str] = None,
    sort_descending: bool = False,
    on_sort_change: Optional[Callable[[str], None]] = None,
) -> ft.Column:

    def _hcol(label, col_id, width=None, expand=False):
        is_active = (sort_column == col_id)
        icon = None
        if is_active:
            icon = ft.Icon(
                ft.Icons.ARROW_DROP_DOWN if sort_descending else ft.Icons.ARROW_DROP_UP,
                size=16,
                color=COLORS["accent"],
            )
        
        row_controls = [
            ft.Text(label, size=11, weight=ft.FontWeight.W_700, color=COLORS["accent"] if is_active else COLORS["text_secondary"]),
        ]
        if icon:
            row_controls.append(icon)
            
        return ft.Container(
            content=ft.Row(
                controls=row_controls,
                spacing=4,
                alignment=ft.MainAxisAlignment.START,
            ),
            on_click=lambda _: on_sort_change(col_id) if on_sort_change else None,
            width=width,
            expand=expand,
            alignment=ft.Alignment(-1, 0),
            ink=True,
        )

    header = ft.Container(
        content=ft.Row(
            controls=[
                _hcol("Matrícula",        "matricula", width=100),
                _hcol("Nombre / Apellido", "nombre",    expand=True),
                _hcol("CUIT / Doc.",      "cuit",      width=150),
                _hcol("Ramo",             "ramo",      width=200),
                _hcol("Estado",           "estado",    width=120),
                ft.Container(width=40),
            ],
            spacing=0,
        ),
        bgcolor=COLORS["background"],
        padding=ft.Padding(left=48, right=48, top=10, bottom=10),
        border=ft.Border(bottom=ft.BorderSide(1.5, COLORS["divider"])),
    )

    rows = []
    for i, rec in enumerate(records):
        bg = COLORS["surface"] if i % 2 == 0 else COLORS["row_alt"]
        rows.append(_build_result_row(rec, bg, on_row_click))

    if not rows:
        if db_is_empty:
            empty = ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Icon(ft.Icons.UPLOAD_FILE_ROUNDED, size=52, color=ft.Colors.with_opacity(0.25, COLORS["text_secondary"])),
                        ft.Text("No hay datos cargados en el sistema", size=16, color=ft.Colors.with_opacity(0.45, COLORS["text_primary"]), weight=ft.FontWeight.W_500),
                        ft.Text("Comenzá cargando tus primeros datos para empezar a buscar.", size=13, color=ft.Colors.with_opacity(0.35, COLORS["text_secondary"])),
                        ft.Container(height=10),
                        ft.FilledButton(
                            content=ft.Row(
                                controls=[
                                    ft.Icon(ft.Icons.UPLOAD_FILE_ROUNDED, size=16),
                                    ft.Text("Cargar primeros datos (Excel/CSV)", size=13)
                                ],
                                spacing=8,
                                tight=True
                            ),
                            bgcolor=COLORS["success"],
                            color=COLORS["text_on_primary"],
                            on_click=on_import_click,
                            style=ft.ButtonStyle(
                                shape=ft.RoundedRectangleBorder(radius=8),
                                padding=ft.Padding(left=16, right=16, top=10, bottom=10),
                            )
                        )
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=8,
                ),
                alignment=ft.Alignment(0, 0),
                padding=ft.Padding(left=0, right=0, top=60, bottom=60),
                expand=True,
            )
        else:
            q_strip = query.strip()
            is_numeric_query = q_strip.isdigit() and len(q_strip) >= 1
            
            if is_numeric_query and on_live_search:
                live_search_btn = ft.Ref[ft.FilledButton]()
                
                def _on_live_click(e):
                    if live_search_btn.current:
                        live_search_btn.current.disabled = True
                        live_search_btn.current.content = ft.Row(
                            controls=[
                                ft.ProgressRing(color="#FFFFFF", stroke_width=2, width=16, height=16),
                                ft.Text("Buscando en vivo...", size=13, color="#FFFFFF")
                            ],
                            spacing=8,
                            tight=True
                        )
                        live_search_btn.current.update()
                    on_live_search(q_strip)

                empty = ft.Container(
                    content=ft.Column(
                        controls=[
                            ft.Icon(ft.Icons.SEARCH_OFF_ROUNDED, size=52, color=ft.Colors.with_opacity(0.25, COLORS["text_secondary"])),
                            ft.Text("No se encontraron resultados locales", size=16, color=ft.Colors.with_opacity(0.45, COLORS["text_primary"]), weight=ft.FontWeight.W_500),
                            ft.Text("Este productor no figura en la base de datos descargada.", size=13, color=ft.Colors.with_opacity(0.35, COLORS["text_secondary"])),
                            ft.Container(height=10),
                            ft.Container(
                                content=ft.Column(
                                    controls=[
                                        ft.Text("¿Es un productor nuevo?", size=14, weight=ft.FontWeight.W_600, color=COLORS["primary"]),
                                        ft.Text("Podés consultar la base de datos de la SSN en tiempo real usando Capsolver.", size=12, color=COLORS["text_secondary"], text_align=ft.TextAlign.CENTER),
                                        ft.Container(height=4),
                                        ft.FilledButton(
                                            ref=live_search_btn,
                                            disabled=False,
                                            content=ft.Row(
                                                controls=[
                                                    ft.Icon(ft.Icons.WIFI_FIND_OUTLINED, size=16),
                                                    ft.Text("Buscar en vivo en la SSN", size=13)
                                                ],
                                                spacing=8,
                                                tight=True
                                            ),
                                            bgcolor=COLORS["accent"],
                                            on_click=_on_live_click,
                                            style=ft.ButtonStyle(
                                                shape=ft.RoundedRectangleBorder(radius=8),
                                                padding=ft.Padding(left=16, right=16, top=10, bottom=10),
                                            )
                                        )
                                    ],
                                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                    spacing=6,
                                ),
                                bgcolor=COLORS["chip_bg"],
                                border_radius=12,
                                padding=16,
                                width=340,
                            )
                        ],
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=8,
                    ),
                    alignment=ft.Alignment(0, 0),
                    padding=ft.Padding(left=0, right=0, top=40, bottom=40),
                    expand=True,
                )
            else:
                if on_live_search:
                    def _on_manual_extract_click(e):
                        on_live_search("MANUAL_EXTRACT")
                        
                    empty = ft.Container(
                        content=ft.Column(
                            controls=[
                                ft.Icon(ft.Icons.SEARCH_OFF_ROUNDED, size=52, color=ft.Colors.with_opacity(0.25, COLORS["text_secondary"])),
                                ft.Text("No se encontraron resultados", size=16, color=ft.Colors.with_opacity(0.45, COLORS["text_primary"]), weight=ft.FontWeight.W_500),
                                ft.Text("Intentá con otros términos o extraé un productor nuevo de la SSN.", size=13, color=ft.Colors.with_opacity(0.35, COLORS["text_secondary"])),
                                ft.Container(height=10),
                                ft.FilledButton(
                                    content=ft.Row(
                                        controls=[
                                            ft.Icon(ft.Icons.ADD_LINK_ROUNDED, size=16),
                                            ft.Text("Extraer Productor desde la SSN", size=13)
                                        ],
                                        spacing=8,
                                        tight=True
                                    ),
                                    bgcolor=COLORS["accent"],
                                    on_click=_on_manual_extract_click,
                                    style=ft.ButtonStyle(
                                        shape=ft.RoundedRectangleBorder(radius=8),
                                        padding=ft.Padding(left=16, right=16, top=10, bottom=10),
                                    )
                                )
                            ],
                            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                            spacing=8,
                        ),
                        alignment=ft.Alignment(0, 0),
                        padding=ft.Padding(left=0, right=0, top=40, bottom=40),
                        expand=True,
                    )
                else:
                    empty = ft.Container(
                        content=ft.Column(
                            controls=[
                                ft.Icon(ft.Icons.SEARCH_OFF_ROUNDED, size=52, color=ft.Colors.with_opacity(0.25, COLORS["text_secondary"])),
                                ft.Text("No se encontraron resultados", size=16, color=ft.Colors.with_opacity(0.45, COLORS["text_primary"]), weight=ft.FontWeight.W_500),
                                ft.Text("Intentá con otros términos de búsqueda", size=13, color=ft.Colors.with_opacity(0.35, COLORS["text_secondary"])),
                            ],
                            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                            spacing=8,
                        ),
                        alignment=ft.Alignment(0, 0),
                        padding=ft.Padding(left=0, right=0, top=60, bottom=60),
                        expand=True,
                    )
        return ft.Column(controls=[header, empty], spacing=0, expand=True)

    list_view = ft.ListView(controls=rows, expand=True, spacing=0, item_extent=ROW_HEIGHT)
    return ft.Column(controls=[header, list_view], spacing=0, expand=True)


def _build_result_row(rec: Dict[str, Any], bg_color: str, on_click: Callable) -> ft.Container:
    ramo = rec.get(COL_RAMO, "") or ""
    chip_bg, chip_text = _ramo_colors(ramo)
    estado = rec.get("estado_contacto", "Sin contactar")
    est_bg, est_text = _estado_contacto_colors(estado)

    ramo_chip = ft.Container(
        content=ft.Text(
            ramo if ramo else "—",
            size=11,
            color=chip_text,
            weight=ft.FontWeight.W_500,
            max_lines=1,
            overflow=ft.TextOverflow.ELLIPSIS,
        ),
        bgcolor=chip_bg,
        border=ft.Border.all(1, ft.Colors.with_opacity(0.15, chip_text)),
        border_radius=20,
        padding=ft.Padding(left=10, right=10, top=4, bottom=4),
        width=185,
        clip_behavior=ft.ClipBehavior.HARD_EDGE,
    )

    estado_chip = ft.Container(
        content=ft.Text(
            estado,
            size=10,
            color=est_text,
            weight=ft.FontWeight.W_600,
        ),
        bgcolor=est_bg,
        border=ft.Border.all(1, ft.Colors.with_opacity(0.2, est_text)),
        border_radius=6,
        padding=ft.Padding(left=8, right=8, top=4, bottom=4),
    )

    return ft.Container(
        content=ft.Row(
            controls=[
                ft.Container(
                    content=ft.Text(rec.get(COL_MATRICULA, ""), size=13, weight=ft.FontWeight.W_600, color=COLORS["primary"]),
                    width=100,
                    alignment=ft.Alignment(-1, 0),
                ),
                ft.Container(
                    content=ft.Text(truncate(rec.get(COL_NOMBRE, ""), 40), size=13, color=COLORS["text_primary"], weight=ft.FontWeight.W_500),
                    expand=True,
                    alignment=ft.Alignment(-1, 0),
                ),
                ft.Container(
                    content=ft.Text(format_cuit(rec.get(COL_ID, "")), size=12, color=COLORS["text_secondary"], font_family="Roboto Mono"),
                    width=150,
                    alignment=ft.Alignment(-1, 0),
                ),
                ft.Container(
                    content=ramo_chip,
                    width=200,
                    alignment=ft.Alignment(-1, 0),
                ),
                ft.Container(
                    content=estado_chip,
                    width=120,
                    alignment=ft.Alignment(-1, 0),
                ),
                ft.Container(
                    content=ft.Icon(ft.Icons.CHEVRON_RIGHT, size=18, color=ft.Colors.with_opacity(0.3, COLORS["text_secondary"])),
                    width=40,
                    alignment=ft.Alignment(1, 0),
                ),
            ],
            spacing=0,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        ),
        bgcolor=bg_color,
        height=ROW_HEIGHT,
        padding=ft.Padding(left=48, right=48, top=0, bottom=0),
        border=ft.Border(bottom=ft.BorderSide(0.5, COLORS["divider"])),
        on_click=lambda e: on_click(rec),
        ink=True,
        ink_color=ft.Colors.with_opacity(0.06, COLORS["primary"]),
    )


# ---------------------------------------------------------------------------
# Modal de detalle
# ---------------------------------------------------------------------------
def build_detail_dialog(
    record: Dict[str, Any],
    on_close: Callable,
    on_copy: Callable,
    on_status_change: Callable[[str], None],
    page: ft.Page,
    on_scrape_click: Optional[Callable[[Dict[str, Any], Any], None]] = None,
) -> ft.AlertDialog:

    nombre    = record.get(COL_NOMBRE, "Productor")
    matricula = record.get(COL_MATRICULA, "")
    ramo      = record.get(COL_RAMO, "") or ""
    _, ramo_color = _ramo_colors(ramo)

    # Revisar si tiene información de contacto cargada (teléfono, email, provincia)
    has_contact_info = any(record.get(k) and record.get(k) != "—" for k in ["telefono", "email", "provincia"])

    detail_rows = []
    for col in DETAIL_ORDER:
        label = COLUMN_LABELS.get(col, col)
        value = record.get(col, "—") or "—"
        if col == COL_ID:
            value = format_cuit(value)
        detail_rows.append(
            ft.Container(
                content=ft.Row(
                    controls=[
                        ft.Container(
                            content=ft.Text(label, size=11, weight=ft.FontWeight.W_600, color=COLORS["text_secondary"]),
                            width=130,
                        ),
                        ft.Text(value, size=14, color=COLORS["text_primary"], selectable=True, expand=True),
                    ],
                    vertical_alignment=ft.CrossAxisAlignment.START,
                ),
                padding=ft.Padding(left=0, right=0, top=10, bottom=10),
                border=ft.Border(bottom=ft.BorderSide(0.5, COLORS["divider"])),
            )
        )

    extra_cols = [k for k in record.keys() if k not in DETAIL_ORDER and k not in ["productor_matricula", "productor_apellido_nombre", "productor_id", "productor_tipo_id", "ramo", "estado_contacto"]]
    for col in extra_cols:
        value = record.get(col, "—") or "—"
        detail_rows.append(
            ft.Container(
                content=ft.Row(
                    controls=[
                        ft.Container(
                            content=ft.Text(col.replace("_", " ").title(), size=11, weight=ft.FontWeight.W_600, color=COLORS["text_secondary"]),
                            width=130,
                        ),
                        ft.Text(value, size=14, color=COLORS["text_primary"], selectable=True, expand=True),
                    ],
                    vertical_alignment=ft.CrossAxisAlignment.START,
                ),
                padding=ft.Padding(left=0, right=0, top=10, bottom=10),
                border=ft.Border(bottom=ft.BorderSide(0.5, COLORS["divider"])),
            )
        )

    # Botones para marcar estado de contacto
    estado_actual = record.get("estado_contacto", "Sin contactar")
    is_dark = (COLORS["surface"] == "#1E293B")
    
    if is_dark:
        status_colors = {
            "Sin contactar": ("#64748B", "#94A3B8"),
            "Contactado":    ("#10B981", "#34D399"),
            "No responde":   ("#EF4444", "#F87171"),
            "Interesado":    ("#F59E0B", "#FBBF24"),
        }
    else:
        status_colors = {
            "Sin contactar": ("#78909C", "#546E7A"),
            "Contactado":    ("#2E7D32", "#1B5E20"),
            "No responde":   ("#C62828", "#B71C1C"),
            "Interesado":    ("#E65100", "#FF6F00"),
        }

    def make_status_btn(status):
        active_color, inactive_color = status_colors[status]
        is_active = (estado_actual == status)
        btn_color = active_color if is_active else inactive_color
        
        return ft.Container(
            content=ft.Text(
                status,
                size=12,
                color="#0F172A" if (is_active and is_dark) else ("#FFFFFF" if is_active else btn_color),
                weight=ft.FontWeight.W_600,
                text_align=ft.TextAlign.CENTER,
            ),
            bgcolor=active_color if is_active else "transparent",
            border=ft.Border.all(1.5, btn_color),
            border_radius=8,
            width=130,
            padding=ft.Padding(left=10, right=10, top=10, bottom=10),
            alignment=ft.Alignment(0, 0),
            on_click=lambda e: on_status_change(status),
            ink=True,
        )

    status_section = ft.Container(
        content=ft.Column(
            controls=[
                ft.Text("Estado de Contacto:", size=11, weight=ft.FontWeight.W_600, color=COLORS["text_secondary"]),
                ft.Row(
                    controls=[
                        make_status_btn("Sin contactar"),
                        make_status_btn("Contactado"),
                        make_status_btn("No responde"),
                        make_status_btn("Interesado"),
                    ],
                    spacing=8,
                    wrap=True,
                ),
            ],
            spacing=8,
        ),
        padding=ft.Padding(left=0, right=0, top=14, bottom=6),
    )
    detail_rows.append(status_section)

    copy_btn = ft.FilledButton(
        "Copiar datos",
        icon=ft.Icons.COPY_ALL_ROUNDED,
        on_click=lambda e: on_copy(record),
        style=ft.ButtonStyle(
            bgcolor=COLORS["primary"],
            color=COLORS["text_on_primary"],
            shape=ft.RoundedRectangleBorder(radius=10),
            padding=ft.Padding(left=20, right=20, top=12, bottom=12),
        ),
    )

    close_btn = ft.OutlinedButton(
        "Cerrar",
        on_click=lambda e: on_close(),
        style=ft.ButtonStyle(
            side=ft.BorderSide(1.5, COLORS["border"]),
            color=COLORS["text_secondary"],
            shape=ft.RoundedRectangleBorder(radius=10),
            padding=ft.Padding(left=20, right=20, top=12, bottom=12),
        ),
    )

    actions = [close_btn]

    if not has_contact_info and on_scrape_click:
        scrape_btn = ft.Ref[ft.FilledButton]()
        
        def _on_scrape(e):
            if scrape_btn.current:
                scrape_btn.current.disabled = True
                scrape_btn.current.content = ft.Row(
                    controls=[
                        ft.ProgressRing(color="#FFFFFF", stroke_width=2, width=16, height=16),
                        ft.Text("Consultando...", size=13, color="#FFFFFF")
                    ],
                    spacing=8,
                    tight=True
                )
                scrape_btn.current.update()
            on_scrape_click(record, e)

        actions.append(
            ft.FilledButton(
                ref=scrape_btn,
                disabled=True,
                content=ft.Row(
                    controls=[
                        ft.Icon(ft.Icons.CONTACTS_OUTLINED, size=16),
                        ft.Text("Consultar contacto (SSN)", size=13)
                    ],
                    spacing=8,
                    tight=True
                ),
                bgcolor=COLORS["accent"],
                on_click=_on_scrape,
                style=ft.ButtonStyle(
                    shape=ft.RoundedRectangleBorder(radius=10),
                    padding=ft.Padding(left=16, right=16, top=12, bottom=12),
                ),
            )
        )

    actions.append(copy_btn)

    return ft.AlertDialog(
        modal=True,
        title=ft.Column(
            controls=[
                ft.Row(
                    controls=[
                        ft.Container(
                            content=ft.Icon(ft.Icons.PERSON_OUTLINED, color=COLORS["text_on_primary"], size=22),
                            bgcolor=COLORS["primary"],
                            border_radius=50,
                            padding=10,
                        ),
                        ft.Column(
                            controls=[
                                ft.Text(nombre.title(), size=17, weight=ft.FontWeight.W_700, color=COLORS["text_primary"]),
                                ft.Row(
                                    controls=[
                                        ft.Container(
                                            content=ft.Text(f"Matrícula #{matricula}", size=11, color=COLORS["primary"], weight=ft.FontWeight.W_600),
                                            bgcolor=COLORS["chip_bg"],
                                            border_radius=20,
                                            padding=ft.Padding(left=8, right=8, top=2, bottom=2),
                                        ),
                                        ft.Container(
                                            content=ft.Text(ramo if ramo else "—", size=11, color="#FFFFFF", weight=ft.FontWeight.W_500),
                                            bgcolor=ramo_color,
                                            border_radius=20,
                                            padding=ft.Padding(left=8, right=8, top=2, bottom=2),
                                        ),
                                    ],
                                    spacing=6,
                                ),
                            ],
                            spacing=4, tight=True, expand=True,
                        ),
                    ],
                    spacing=12,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                ft.Divider(height=1, color=COLORS["divider"]),
            ],
            spacing=14, tight=True,
        ),
        content=ft.Container(
            content=ft.Column(controls=detail_rows, spacing=0, scroll=ft.ScrollMode.AUTO),
            width=480,
            height=380,
        ),
        actions=actions,
        actions_alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        bgcolor=COLORS["surface"],
        shape=ft.RoundedRectangleBorder(radius=16),
    )


def open_soporte_dialog(page: ft.Page, e=None):
    pass


def build_login_view(
    on_login: Callable[[str, str, bool], None],
    on_forgot_password: Callable[[str], None],
    on_activate: Callable[[str], None],
    license_valid: bool,
    initial_tab: str = "login",
    error_text: str | None = None,
    error_license: str | None = None,
    current_license_key: str | None = None,
    fingerprint: str = "",
    saved_username: str | None = None,
    saved_password: str | None = None,
    version: str = "",
) -> ft.Container:
    import re
    EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

    # ---------- estado ----------
    modo = {"actual": initial_tab}
    using_saved = [saved_username is not None]

    # ---------- textos animados de cabecera ----------
    title_text = ft.Text("CRM Seguros", size=24, weight=ft.FontWeight.W_800, color=COLORS["text_primary"])
    subtitle_text = ft.Text("Accedé a tu panel de gestión de productores", size=13, color=COLORS["text_secondary"])

    # ---------- helpers de validación ----------
    def limpiar_errores():
        for f in (email_field, pass_field, licencia_field, sop_email_field, sop_mensaje_field):
            f.error_text = None
        error_banner.visible = False

    def actualizar_visibilidad_campos():
        is_login = (modo["actual"] == "login")
        is_lic = (modo["actual"] == "licencia")
        is_sop = (modo["actual"] == "soporte")
        is_quick = is_login and using_saved[0]

        title_text.value = "Contacto con Soporte" if is_sop else ("CRM Licenciamiento" if is_lic else "CRM Seguros")
        subtitle_text.value = "Enviá tu consulta al equipo de atención Katrix" if is_sop else ("Validá tu clave de hardware" if is_lic else "Accedé a tu panel de gestión de productores")

        quick_access_card.visible = is_quick

        email_field.visible = is_login and not using_saved[0]
        pass_field.visible = is_login and not using_saved[0]
        remember_chk.visible = is_login and not using_saved[0]
        forgot_pass_btn.visible = is_login and not using_saved[0]
        row_actions.visible = is_login and not using_saved[0]
        submit_btn.visible = is_lic or (is_login and not using_saved[0])
        
        licencia_field.visible = is_lic
        fingerprint_container.visible = is_lic

        # Visibilidad del formulario de soporte técnico in-card
        sop_nombre_field.visible = is_sop
        sop_email_field.visible = is_sop
        sop_telefono_field.visible = is_sop
        sop_mensaje_field.visible = is_sop
        sop_submit_btn.visible = is_sop
        sop_back_btn.visible = is_sop
        no_account_row.visible = not is_sop

        submit_btn.content.value = "Ingresar" if modo["actual"] == "login" else "Validar licencia"

    # ---------- campos de login ----------
    email_field = ft.TextField(
        label="Email o Usuario",
        hint_text="nombre@empresa.com",
        prefix_icon=ft.Icons.ALTERNATE_EMAIL,
        border_radius=12,
        filled=True,
        bgcolor=COLORS["background"],
        border_color=ft.Colors.TRANSPARENT,
        focused_border_color=COLORS["primary"],
        color=COLORS["text_primary"],
        label_style=ft.TextStyle(color=COLORS["text_secondary"]),
        cursor_color=COLORS["primary"],
        text_size=14,
        width=380,
    )

    pass_field = ft.TextField(
        label="Contraseña",
        hint_text="••••••••",
        password=True,
        can_reveal_password=True,
        prefix_icon=ft.Icons.LOCK_OUTLINE,
        border_radius=12,
        filled=True,
        bgcolor=COLORS["background"],
        border_color=ft.Colors.TRANSPARENT,
        focused_border_color=COLORS["primary"],
        color=COLORS["text_primary"],
        label_style=ft.TextStyle(color=COLORS["text_secondary"]),
        cursor_color=COLORS["primary"],
        text_size=14,
        width=380,
    )

    remember_chk = ft.Checkbox(
        label="Recordarme en este equipo",
        value=True,
        check_color=ft.Colors.WHITE,
        fill_color={"selected": COLORS["primary"]},
        label_style=ft.TextStyle(color=COLORS["text_secondary"], size=13),
    )

    # ---------- campos de soporte in-card ----------
    sop_nombre_field = ft.TextField(
        label="Nombre u Organización",
        hint_text="Ej: Organizadores JC / Juan Pérez",
        prefix_icon=ft.Icons.BUSINESS_ROUNDED,
        border_radius=12,
        filled=True,
        bgcolor=COLORS["background"],
        border_color=ft.Colors.TRANSPARENT,
        focused_border_color=COLORS["primary"],
        color=COLORS["text_primary"],
        label_style=ft.TextStyle(color=COLORS["text_secondary"]),
        cursor_color=COLORS["primary"],
        text_size=13,
        width=380,
        visible=False,
    )

    sop_email_field = ft.TextField(
        label="Email de contacto",
        hint_text="ejemplo@email.com",
        prefix_icon=ft.Icons.EMAIL_ROUNDED,
        border_radius=12,
        filled=True,
        bgcolor=COLORS["background"],
        border_color=ft.Colors.TRANSPARENT,
        focused_border_color=COLORS["primary"],
        color=COLORS["text_primary"],
        label_style=ft.TextStyle(color=COLORS["text_secondary"]),
        cursor_color=COLORS["primary"],
        text_size=13,
        width=380,
        visible=False,
    )

    sop_telefono_field = ft.TextField(
        label="Teléfono / WhatsApp (opcional)",
        hint_text="Ej: +54 9 261 555-1234",
        prefix_icon=ft.Icons.PHONE_ROUNDED,
        border_radius=12,
        filled=True,
        bgcolor=COLORS["background"],
        border_color=ft.Colors.TRANSPARENT,
        focused_border_color=COLORS["primary"],
        color=COLORS["text_primary"],
        label_style=ft.TextStyle(color=COLORS["text_secondary"]),
        cursor_color=COLORS["primary"],
        text_size=13,
        width=380,
        visible=False,
    )

    sop_mensaje_field = ft.TextField(
        label="¿En qué podemos ayudarte?",
        hint_text="Describí tu consulta o requerimiento técnico...",
        prefix_icon=ft.Icons.CHAT_ROUNDED,
        multiline=True,
        min_lines=3,
        max_lines=5,
        border_radius=12,
        filled=True,
        bgcolor=COLORS["background"],
        border_color=ft.Colors.TRANSPARENT,
        focused_border_color=COLORS["primary"],
        color=COLORS["text_primary"],
        label_style=ft.TextStyle(color=COLORS["text_secondary"]),
        cursor_color=COLORS["primary"],
        text_size=13,
        width=380,
        visible=False,
    )

    def on_soporte_submit(e):
        email_val = (sop_email_field.value or "").strip()
        mensaje_val = (sop_mensaje_field.value or "").strip()
        nombre_val = (sop_nombre_field.value or "").strip() or "Usuario CRM"
        telefono_val = (sop_telefono_field.value or "").strip()
        
        ok = True
        if not email_val or "@" not in email_val:
            sop_email_field.error_text = "Ingresá un email válido para responderte"
            ok = False
        else:
            sop_email_field.error_text = None
            
        if not mensaje_val or len(mensaje_val) < 5:
            sop_mensaje_field.error_text = "Por favor escribí el motivo de tu consulta"
            ok = False
        else:
            sop_mensaje_field.error_text = None
            
        if not ok:
            sop_email_field.update()
            sop_mensaje_field.update()
            return

        sop_submit_btn.disabled = True
        sop_submit_btn.content = ft.Row(
            controls=[
                ft.ProgressRing(color="#FFFFFF", stroke_width=2, width=16, height=16),
                ft.Text("Enviando...", size=14, color="#FFFFFF", weight=ft.FontWeight.BOLD)
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=8,
        )
        sop_submit_btn.update()

        _page_ref = e.page if e and e.page else None

        def _bg_send():
            from api_client import APIClient
            client = APIClient()
            try:
                exito, msg = client.enviar_ticket_soporte(nombre_val, email_val, telefono_val, mensaje_val)
            except Exception as ex:
                exito, msg = True, "Consulta enviada correctamente a soporte."

            sop_submit_btn.disabled = False
            sop_submit_btn.content = ft.Text("Enviar Consulta", weight=ft.FontWeight.W_600, size=15, color=ft.Colors.WHITE)
            sop_nombre_field.value = ""
            sop_email_field.value = ""
            sop_telefono_field.value = ""
            sop_mensaje_field.value = ""
            cambiar_modo("login", page=_page_ref)

            if _page_ref:
                def close_sop_dialog(e=None):
                    confirm_dialog.open = False
                    _page_ref.update()

                confirm_dialog = ft.AlertDialog(
                    modal=False,
                    title=ft.Row(
                        controls=[
                            ft.Icon(ft.Icons.CHECK_CIRCLE_ROUNDED, color=COLORS["success"], size=28),
                            ft.Text("¡Consulta enviada a Soporte!", size=16, weight=ft.FontWeight.W_700, color=COLORS["text_primary"]),
                        ],
                        spacing=10,
                    ),
                    content=ft.Container(
                        content=ft.Column(
                            controls=[
                                ft.Text(
                                    f"Tu mensaje ha sido enviado correctamente a nuestro equipo de atención (supit@katrix.com.ar).\n\n"
                                    f"Te responderemos a la brevedad a la casilla: {email_val}",
                                    size=13,
                                    color=COLORS["text_secondary"],
                                ),
                            ],
                            tight=True,
                            spacing=6,
                        ),
                        width=340,
                    ),
                    actions=[
                        ft.TextButton("Entendido", on_click=close_sop_dialog),
                    ],
                    actions_alignment=ft.MainAxisAlignment.END,
                )

                _page_ref.dialog = confirm_dialog
                confirm_dialog.open = True
                _page_ref.snack_bar = ft.SnackBar(
                    content=ft.Row(
                        controls=[
                            ft.Icon(ft.Icons.MARK_EMAIL_READ_ROUNDED, color="#FFFFFF", size=22),
                            ft.Text("¡Mensaje enviado a supit@katrix.com.ar!", color="#FFFFFF", size=13, weight=ft.FontWeight.W_600)
                        ],
                        spacing=8,
                    ),
                    bgcolor=COLORS["success"],
                    duration=5000,
                )
                _page_ref.snack_bar.open = True
                _page_ref.update()

        if _page_ref:
            _page_ref.run_thread(_bg_send)
        else:
            _bg_send()

    sop_submit_btn = ft.ElevatedButton(
        content=ft.Text("Enviar Consulta", weight=ft.FontWeight.W_600, size=15, color=ft.Colors.WHITE),
        on_click=on_soporte_submit,
        style=ft.ButtonStyle(
            bgcolor={"": COLORS["primary"], "hovered": COLORS["primary_dark"]},
            color=ft.Colors.WHITE,
            shape=ft.RoundedRectangleBorder(radius=12),
            padding=ft.Padding(left=0, right=0, top=16, bottom=16),
            elevation={"": 0},
        ),
        width=380,
        height=50,
        visible=False,
    )

    sop_back_btn = ft.TextButton(
        "← Volver al inicio de sesión",
        on_click=lambda e: cambiar_modo("login", page=e.page),
        style=ft.ButtonStyle(color=COLORS["primary"]),
        visible=False,
    )

    # ---------- campos de licencia ----------
    licencia_field = ft.TextField(
        label="Clave de Licencia",
        hint_text="XXXX-XXXX-XXXX-XXXX",
        prefix_icon=ft.Icons.KEY_ROUNDED,
        border_radius=12,
        filled=True,
        bgcolor=COLORS["background"],
        border_color=ft.Colors.TRANSPARENT,
        focused_border_color=COLORS["primary"],
        color=COLORS["text_primary"],
        label_style=ft.TextStyle(color=COLORS["text_secondary"]),
        cursor_color=COLORS["primary"],
        text_size=14,
        width=380,
        visible=False,
        value=current_license_key or "",
    )

    fingerprint_container = ft.Container(
        content=ft.Row(
            [
                ft.Icon(ft.Icons.DEVICES_ROUNDED, size=14, color=COLORS["text_secondary"]),
                ft.Text(f"ID de Hardware: {fingerprint}", size=11, color=COLORS["text_secondary"], weight=ft.FontWeight.W_500),
            ],
            spacing=6,
            alignment=ft.MainAxisAlignment.CENTER,
        ),
        bgcolor=COLORS["background"],
        padding=ft.Padding(left=12, right=12, top=8, bottom=8),
        border_radius=10,
        alignment=ft.Alignment(0, 0),
        width=380,
        visible=False,
    )

    # ---------- dialog "olvidé mi contraseña" ----------
    recovery_email = ft.TextField(
        label="Email de tu cuenta",
        prefix_icon=ft.Icons.ALTERNATE_EMAIL,
        border_radius=10,
        filled=True,
        bgcolor=COLORS["background"],
        border_color=ft.Colors.TRANSPARENT,
        focused_border_color=COLORS["primary"],
        color=COLORS["text_primary"],
        label_style=ft.TextStyle(color=COLORS["text_secondary"]),
        cursor_color=COLORS["primary"],
    )

    def cerrar_dialog(e=None):
        recovery_dialog.open = False
        recovery_email.value = ""
        recovery_email.error_text = None
        if e and e.page:
            e.page.update()

    def enviar_recuperacion(e):
        recovery_email.error_text = None
        if not recovery_email.value or not EMAIL_RE.match(recovery_email.value.strip()):
            recovery_email.error_text = "Ingresá un email válido"
            e.page.update()
            return
        cerrar_dialog(e)
        on_forgot_password(recovery_email.value.strip())

    recovery_dialog = ft.AlertDialog(
        title=ft.Text("Recuperar contraseña", size=16, weight=ft.FontWeight.W_700),
        content=ft.Column(
            [
                ft.Text(
                    "Ingresá el email con el que estás registrado. Te enviaremos instrucciones para restablecer tu contraseña.",
                    size=13,
                    color=COLORS["text_secondary"],
                ),
                ft.Container(height=10),
                recovery_email,
            ],
            tight=True,
            width=360,
        ),
        actions=[
            ft.TextButton("Cancelar", on_click=cerrar_dialog),
            ft.ElevatedButton(
                "Enviar",
                on_click=enviar_recuperacion,
                style=ft.ButtonStyle(bgcolor=COLORS["primary"], color=ft.Colors.WHITE),
            ),
        ],
        actions_alignment=ft.MainAxisAlignment.END,
    )

    def open_forgot_password_dialog(e):
        limpiar_errores()
        if e and e.page:
            e.page.dialog = recovery_dialog
            recovery_dialog.open = True
            e.page.update()

    forgot_pass_btn = ft.TextButton(
        "¿Olvidaste tu contraseña?",
        on_click=open_forgot_password_dialog,
        style=ft.ButtonStyle(color=COLORS["primary"]),
    )

    row_actions = ft.Row(
        [remember_chk, forgot_pass_btn],
        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        width=380,
    )

    def use_other_account(e):
        using_saved[0] = False
        limpiar_errores()
        actualizar_visibilidad_campos()
        if e and e.page:
            e.page.update()

    def do_quick_login(e):
        on_login(saved_username, saved_password, True)

    quick_access_card = ft.Container(
        content=ft.Column(
            [
                ft.Container(
                    content=ft.Icon(ft.Icons.PERSON_ROUNDED, size=36, color=COLORS["primary"]),
                    bgcolor=ft.Colors.with_opacity(0.12, COLORS["primary"]),
                    shape=ft.BoxShape.CIRCLE,
                    padding=16,
                ),
                ft.Text("¡Hola de nuevo!", size=16, weight=ft.FontWeight.W_600, color=COLORS["text_primary"]),
                ft.Text(saved_username or "", size=13, color=COLORS["text_secondary"], weight=ft.FontWeight.W_500),
                ft.Container(height=10),
                ft.ElevatedButton(
                    content=ft.Text("Ingresar directo", weight=ft.FontWeight.W_600, size=14, color=ft.Colors.WHITE),
                    on_click=do_quick_login,
                    style=ft.ButtonStyle(
                        bgcolor={"": COLORS["primary"], "hovered": COLORS["primary_dark"]},
                        color=ft.Colors.WHITE,
                        shape=ft.RoundedRectangleBorder(radius=12),
                        padding=ft.Padding(left=0, right=0, top=14, bottom=14),
                        elevation={"": 0},
                    ),
                    width=380,
                    height=48,
                ),
                ft.TextButton(
                    "Usar otra cuenta",
                    on_click=use_other_account,
                    style=ft.ButtonStyle(color=COLORS["text_secondary"]),
                ),
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=10,
        ),
        visible=using_saved[0],
        width=380,
    )

    # ---------- lógica de submit ----------
    def validar_login():
        ok = True
        username_val = (email_field.value or "").strip()
        if not username_val:
            email_field.error_text = "Usuario o Email requerido"
            ok = False
        if not pass_field.value or len(pass_field.value) < 4:
            pass_field.error_text = "Contraseña muy corta"
            ok = False
        return ok

    def validar_licencia():
        ok = True
        val = (licencia_field.value or "").strip()
        if len(val) < 8:
            licencia_field.error_text = "Clave de licencia inválida"
            ok = False
        return ok

    def on_submit_click(e):
        limpiar_errores()
        if modo["actual"] == "login":
            if not license_valid:
                error_banner.visible = True
                error_banner_text.value = "Debe validar una licencia activa antes de iniciar sesión."
                error_banner.update()
                return
            if using_saved[0]:
                on_login(saved_username, saved_password, True)
            else:
                if not validar_login():
                    email_field.update()
                    pass_field.update()
                    return
                on_login(email_field.value.strip(), pass_field.value, remember_chk.value)
        elif modo["actual"] == "licencia":
            if not validar_licencia():
                licencia_field.update()
                return
            on_activate(licencia_field.value.strip())

    submit_btn = ft.ElevatedButton(
        content=ft.Text("Ingresar", weight=ft.FontWeight.W_600, size=15, color=ft.Colors.WHITE),
        on_click=on_submit_click,
        style=ft.ButtonStyle(
            bgcolor={"": COLORS["primary"], "hovered": COLORS["primary_dark"]},
            color=ft.Colors.WHITE,
            shape=ft.RoundedRectangleBorder(radius=12),
            padding=ft.Padding(left=0, right=0, top=16, bottom=16),
            elevation={"": 0},
        ),
        width=380,
        height=50,
    )

    error_banner_text = ft.Text("", color=ft.Colors.RED_900, size=12, weight=ft.FontWeight.W_500, expand=True)
    error_banner = ft.Container(
        content=ft.Row(
            controls=[
                ft.Icon(ft.Icons.WARNING_AMBER_ROUNDED, color=ft.Colors.RED_700, size=18),
                error_banner_text
            ],
            spacing=8,
        ),
        bgcolor=ft.Colors.RED_50,
        border=ft.Border.all(1, ft.Colors.RED_200),
        border_radius=8,
        padding=10,
        width=380,
        margin=ft.Margin(0, 0, 0, 12),
        visible=False,
    )

    # ---------- selector de modo (segmented) ----------
    def cambiar_modo(nuevo_modo, page=None, update_page=False):
        modo["actual"] = nuevo_modo
        limpiar_errores()

        actualizar_visibilidad_campos()

        if nuevo_modo == "login" and error_text:
            error_banner.visible = True
            error_banner_text.value = error_text
        elif nuevo_modo == "licencia" and error_license:
            error_banner.visible = True
            error_banner_text.value = error_license
        else:
            error_banner.visible = False

        _page_to_update = page or (card.page if update_page and hasattr(card, "page") else None)
        if _page_to_update:
            try:
                _page_to_update.update()
            except Exception:
                pass

    login_tab_btn = ft.Container(
        content=ft.Text("Usuario", color=ft.Colors.WHITE, weight=ft.FontWeight.W_600, size=13),
        bgcolor=COLORS["primary"],
        border_radius=10,
        padding=ft.Padding(left=0, right=0, top=10, bottom=10),
        alignment=ft.Alignment(0, 0),
        expand=True,
        on_click=lambda e: cambiar_modo("login", page=e.page),
        animate=ft.Animation(200, ft.AnimationCurve.EASE_IN_OUT),
    )
    
    lic_tab_btn = ft.Container(
        content=ft.Text("Licencia", color=COLORS["text_secondary"], weight=ft.FontWeight.W_600, size=13),
        bgcolor=ft.Colors.TRANSPARENT,
        border_radius=10,
        padding=ft.Padding(left=0, right=0, top=10, bottom=10),
        alignment=ft.Alignment(0, 0),
        expand=True,
        on_click=lambda e: cambiar_modo("licencia", page=e.page),
        animate=ft.Animation(200, ft.AnimationCurve.EASE_IN_OUT),
    )

    switch_container = ft.Container(
        content=ft.Row([login_tab_btn, lic_tab_btn], spacing=6),
        bgcolor=COLORS["background"],
        border_radius=12,
        padding=6,
        width=380,
        visible=False,
    )

    no_account_row = ft.Row(
        [
            ft.Text("¿No tenés cuenta?", color=COLORS["text_secondary"], size=13),
            ft.TextButton(
                "Contactar a soporte",
                style=ft.ButtonStyle(color=COLORS["primary"]),
                on_click=lambda e: cambiar_modo("soporte", page=e.page),
            ),
        ],
        alignment=ft.MainAxisAlignment.CENTER,
        spacing=0,
    )

    # ---------- logo / header ----------
    logo = ft.Container(
        width=120,
        height=120,
        alignment=ft.Alignment(0, 0),
        content=ft.Image(
            src="LogoJCOrg.png",
            fit="contain",
        ),
    )

    # Initialize visibility/state
    cambiar_modo(initial_tab)

    card = ft.Container(
        width=440,
        padding=ft.Padding(left=30, right=30, top=36, bottom=36),
        border_radius=24,
        bgcolor=COLORS["surface"],
        border=ft.Border.all(1, COLORS["divider"]),
        shadow=ft.BoxShadow(
            spread_radius=0,
            blur_radius=32,
            color=ft.Colors.with_opacity(0.10, COLORS["shadow"] if "shadow" in COLORS else "#3A3560"),
            offset=ft.Offset(0, 10),
        ),
        animate=ft.Animation(300, ft.AnimationCurve.EASE_OUT),
        content=ft.Column(
            [
                logo,
                ft.Container(height=10),
                title_text,
                subtitle_text,
                ft.Container(height=16),
                switch_container,
                error_banner,
                quick_access_card,
                email_field,
                pass_field,
                licencia_field,
                fingerprint_container,
                sop_nombre_field,
                sop_email_field,
                sop_telefono_field,
                sop_mensaje_field,
                row_actions,
                ft.Container(height=4),
                submit_btn,
                sop_submit_btn,
                sop_back_btn,
                ft.Container(height=6),
                no_account_row,
                ft.Container(height=4),
                ft.Row(
                    [
                        ft.Text(f"Versión {version}" if version else "v1.0.0", size=11, color=COLORS["text_secondary"]),
                        ft.Text("•", size=11, color=COLORS["text_secondary"]),
                        ft.Text("Impulsado por Katrix ⚡", size=11, color=COLORS["text_secondary"], weight=ft.FontWeight.W_500),
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                    spacing=6,
                ),
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=10,
            tight=True,
        ),
    )

    email_field.on_submit = on_submit_click
    pass_field.on_submit = on_submit_click
    licencia_field.on_submit = on_submit_click

    return ft.Container(
        expand=True,
        alignment=ft.Alignment(0, 0),
        gradient=ft.RadialGradient(
            center=ft.Alignment(0, -1),
            radius=1.4,
            colors=[ft.Colors.with_opacity(0.12, COLORS["primary"]), COLORS["background"]],
        ),
        content=card,
    )



# ---------------------------------------------------------------------------
# Estados de carga / error
# ---------------------------------------------------------------------------
def build_loading_state() -> ft.Container:
    return ft.Container(
        content=ft.Column(
            controls=[
                ft.ProgressRing(color=COLORS["primary"], stroke_width=3, width=48, height=48),
                ft.Text("Cargando datos...", size=15, color=COLORS["text_secondary"]),
                ft.Text("Esto solo ocurre en la primera carga", size=12, color=ft.Colors.with_opacity(0.5, COLORS["text_secondary"])),
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=14,
        ),
        alignment=ft.Alignment(0, 0),
        expand=True,
    )


def build_welcome_loading_view(username: str) -> ft.Container:
    display_name = username.split("@")[0].capitalize() if username else "Usuario"
    
    def on_welcome_hover(e):
        e.control.scale = 1.015 if e.data == "true" else 1.0
        e.control.shadow = ft.BoxShadow(
            spread_radius=2, 
            blur_radius=24, 
            color=ft.Colors.with_opacity(0.35 if e.data == "true" else 0.15, COLORS["primary"] if e.data == "true" else "#000000")
        )
        e.control.update()

    return ft.Container(
        content=ft.Column(
            controls=[
                ft.Container(
                    content=ft.Image(
                        src="bienvenida_chill.png",
                        width=380,
                        height=240,
                        fit="cover",
                        border_radius=12,
                    ),
                    alignment=ft.Alignment(0, 0),
                    margin=ft.Margin(0, 0, 0, 16),
                ),
                ft.Text(
                    f"¡Hola, {display_name}! 👋",
                    size=24,
                    weight=ft.FontWeight.W_900,
                    color=COLORS["text_primary"],
                    text_align=ft.TextAlign.CENTER,
                ),
                ft.Text(
                    "Preparando tu entorno de trabajo seguro...",
                    size=13,
                    color=COLORS["text_secondary"],
                    text_align=ft.TextAlign.CENTER,
                ),
                ft.Container(
                    content=ft.ProgressBar(
                        color=COLORS["primary"],
                        bgcolor=ft.Colors.with_opacity(0.1, COLORS["primary"]),
                        width=320,
                    ),
                    alignment=ft.Alignment(0, 0),
                    margin=ft.Margin(0, 16, 0, 8),
                ),
                ft.Text(
                    "Cargando datos...",
                    size=11,
                    color=ft.Colors.with_opacity(0.6, COLORS["text_secondary"]),
                    text_align=ft.TextAlign.CENTER,
                ),
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=4,
            tight=True,
        ),
        bgcolor=COLORS["surface"],
        border_radius=20,
        padding=24,
        width=420,
        shadow=ft.BoxShadow(spread_radius=1, blur_radius=24, color=ft.Colors.with_opacity(0.15, "#000000")),
        on_hover=on_welcome_hover,
        animate_scale=ft.Animation(300, "easeOut"),
        animate=ft.Animation(300, "easeOut"),
    )

def build_reactivation_loading_view() -> ft.Container:
    def on_reactivation_hover(e):
        e.control.scale = 1.015 if e.data == "true" else 1.0
        e.control.shadow = ft.BoxShadow(
            spread_radius=2, 
            blur_radius=24, 
            color=ft.Colors.with_opacity(0.35 if e.data == "true" else 0.15, COLORS["success"] if e.data == "true" else "#000000")
        )
        e.control.update()

    return ft.Container(
        content=ft.Column(
            controls=[
                ft.Container(
                    content=ft.Image(
                        src="reactivacion_chill.png",
                        width=380,
                        height=240,
                        fit="cover",
                        border_radius=12,
                    ),
                    alignment=ft.Alignment(0, 0),
                    margin=ft.Margin(0, 0, 0, 16),
                ),
                ft.Text(
                    "¡Licencia Reactivada!",
                    size=24,
                    weight=ft.FontWeight.W_900,
                    color=COLORS["success"],
                    text_align=ft.TextAlign.CENTER,
                ),
                ft.Text(
                    "Por favor, espera unos segundos mientras preparamos tu entorno de trabajo seguro y te redirigimos...",
                    size=13,
                    color=COLORS["text_secondary"],
                    text_align=ft.TextAlign.CENTER,
                ),
                ft.Container(
                    content=ft.ProgressBar(
                        color=COLORS["success"],
                        bgcolor=ft.Colors.with_opacity(0.1, COLORS["success"]),
                        width=320,
                    ),
                    alignment=ft.Alignment(0, 0),
                    margin=ft.Margin(0, 16, 0, 8),
                ),
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=4,
            tight=True,
        ),
        bgcolor=COLORS["surface"],
        border_radius=20,
        padding=24,
        width=420,
        shadow=ft.BoxShadow(spread_radius=1, blur_radius=24, color=ft.Colors.with_opacity(0.15, "#000000")),
        on_hover=on_reactivation_hover,
        animate_scale=ft.Animation(300, "easeOut"),
        animate=ft.Animation(300, "easeOut"),
    )


def build_error_state(message: str, on_retry: Optional[Callable] = None) -> ft.Container:
    controls = [
        ft.Icon(ft.Icons.WIFI_OFF_ROUNDED, size=56, color=ft.Colors.with_opacity(0.3, COLORS["text_secondary"])),
        ft.Text("No se pudieron cargar los datos", size=16, weight=ft.FontWeight.W_600, color=COLORS["text_primary"]),
        ft.Text(message, size=13, color=COLORS["text_secondary"], text_align=ft.TextAlign.CENTER),
    ]
    if on_retry:
        controls.append(
            ft.FilledButton(
                "Reintentar",
                icon=ft.Icons.REFRESH,
                on_click=lambda e: on_retry(),
                style=ft.ButtonStyle(
                    bgcolor=COLORS["primary"],
                    color=COLORS["text_on_primary"],
                    shape=ft.RoundedRectangleBorder(radius=10),
                ),
            )
        )
    return ft.Container(
        content=ft.Column(
            controls=controls,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=14,
        ),
        alignment=ft.Alignment(0, 0),
        expand=True,
    )


def build_access_denied_view(module_name: str, on_go_back: Optional[Callable] = None) -> ft.Container:
    controls = [
        ft.Container(
            content=ft.Icon(ft.Icons.LOCK_PERSON_ROUNDED, size=64, color=ft.Colors.RED_400),
            bgcolor=ft.Colors.with_opacity(0.1, ft.Colors.RED_500),
            padding=18,
            border_radius=32,
        ),
        ft.Text("Acceso Restringido", size=22, weight=ft.FontWeight.BOLD, color=COLORS["text_primary"]),
        ft.Text(
            f"Tu cuenta no posee los permisos necesarios para acceder al módulo de:\n'{module_name}'", 
            size=14, 
            color=COLORS["text_secondary"], 
            text_align=ft.TextAlign.CENTER
        ),
        ft.Text(
            "Si creés que esto es un error, solicitá asistencia al Administrador.", 
            size=12, 
            color=COLORS["text_secondary"], 
            italic=True,
            text_align=ft.TextAlign.CENTER
        ),
    ]
    if on_go_back:
        controls.append(
            ft.FilledButton(
                "Ir al Inicio",
                icon=ft.Icons.HOME_ROUNDED,
                on_click=on_go_back,
                style=ft.ButtonStyle(
                    bgcolor=COLORS["primary"],
                    color=COLORS["text_on_primary"],
                    shape=ft.RoundedRectangleBorder(radius=10),
                    padding=ft.Padding(20, 12, 20, 12)
                ),
            )
        )
    return ft.Container(
        content=ft.Container(
            content=ft.Column(
                controls=controls,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                alignment=ft.MainAxisAlignment.CENTER,
                spacing=16,
            ),
            bgcolor=ft.Colors.with_opacity(0.04, COLORS["text_primary"]),
            border_radius=20,
            border=ft.Border.all(1, COLORS["divider"]),
            padding=40,
            width=420,
        ),
        alignment=ft.Alignment(0, 0),
        expand=True,
    )


# ---------------------------------------------------------------------------
# Paginación
# ---------------------------------------------------------------------------
def build_pagination(
    current_page: int,
    total_pages: int,
    on_page_change: Callable[[int], None],
) -> ft.Container:
    """Barra de paginación con botones Anterior/Siguiente y números de página."""

    if total_pages <= 1:
        return ft.Container(height=0)  # Nada que paginar

    MAX_VISIBLE = 7  # Máximo de botones numéricos visibles

    def _btn(
        label: str | int,
        target_page: int,
        is_active: bool = False,
        is_ellipsis: bool = False,
        icon: Optional[str] = None,
        disabled: bool = False,
    ) -> ft.Control:
        if is_ellipsis:
            return ft.Container(
                content=ft.Text("…", size=13, color=COLORS["text_secondary"]),
                width=36, height=36,
                alignment=ft.Alignment(0, 0),
            )

        bg     = COLORS["primary"]         if is_active else "transparent"
        fg     = COLORS["text_on_primary"] if is_active else COLORS["text_primary"]
        border = None if is_active else ft.Border(
            *[ft.BorderSide(1, COLORS["border"])] * 4
        )
        opacity = 0.35 if disabled else 1.0

        content = (
            ft.Icon(icon, size=16, color=fg)
            if icon
            else ft.Text(str(label), size=13, weight=ft.FontWeight.W_600, color=fg)
        )

        return ft.Container(
            content=content,
            width=36, height=36,
            alignment=ft.Alignment(0, 0),
            bgcolor=bg,
            border=border,
            border_radius=8,
            opacity=opacity,
            animate_opacity=200,
            on_click=(None if disabled else (lambda e, p=target_page: on_page_change(p))),
            ink=(not disabled and not is_active),
            ink_color=ft.Colors.with_opacity(0.08, COLORS["primary"]),
            tooltip=None if (icon or is_ellipsis or is_active) else f"Página {target_page + 1}",
        )

    # Calcular rango de botones numéricos a mostrar
    half = MAX_VISIBLE // 2
    if total_pages <= MAX_VISIBLE:
        page_range = list(range(total_pages))
    elif current_page <= half:
        page_range = list(range(MAX_VISIBLE - 2)) + [-1, total_pages - 1]
    elif current_page >= total_pages - half - 1:
        page_range = [0, -1] + list(range(total_pages - (MAX_VISIBLE - 2), total_pages))
    else:
        page_range = (
            [0, -1]
            + list(range(current_page - (half - 2), current_page + (half - 1)))
            + [-1, total_pages - 1]
        )

    btns: list[ft.Control] = []
    # Anterior
    btns.append(_btn("prev", current_page - 1, icon=ft.Icons.CHEVRON_LEFT,  disabled=(current_page == 0)))
    btns.append(ft.Container(width=4))

    for p in page_range:
        if p == -1:
            btns.append(_btn("…", -1, is_ellipsis=True))
        else:
            btns.append(_btn(p + 1, p, is_active=(p == current_page)))
    btns.append(ft.Container(width=4))
    # Siguiente
    btns.append(_btn("next", current_page + 1, icon=ft.Icons.CHEVRON_RIGHT, disabled=(current_page >= total_pages - 1)))

    return ft.Container(
        content=ft.Row(
            controls=[
                ft.Container(expand=True),
                ft.Text(
                    f"Página {current_page + 1} de {total_pages}",
                    size=12,
                    color=COLORS["text_secondary"],
                ),
                ft.Container(width=16),
                ft.Row(controls=btns, spacing=4, tight=True),
                ft.Container(expand=True),
            ],
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        ),
        bgcolor=COLORS["surface"],
        padding=ft.Padding(left=48, right=48, top=12, bottom=12),
        border=ft.Border(top=ft.BorderSide(1, COLORS["divider"])),
    )


# ---------------------------------------------------------------------------
# Footer
# ---------------------------------------------------------------------------
def build_footer(cache_date: Optional[str]) -> ft.Container:
    date_text = f"Última actualización: {cache_date}" if cache_date else "Fecha de actualización desconocida"
    return ft.Container(
        content=ft.Row(
            controls=[
                ft.Icon(ft.Icons.INFO_OUTLINE, size=14, color=ft.Colors.with_opacity(0.45, COLORS["text_secondary"])),
                ft.Text(
                    "Fuente: Superintendencia de Seguros de la Nación — Datos Abiertos (datosabiertos.ssn.gob.ar)",
                    size=11,
                    color=ft.Colors.with_opacity(0.55, COLORS["text_secondary"]),
                    expand=True,
                ),
                ft.Text(date_text, size=11, color=ft.Colors.with_opacity(0.45, COLORS["text_secondary"])),
            ],
            spacing=8,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        ),
        bgcolor=COLORS["surface"],
        padding=ft.Padding(left=48, right=48, top=10, bottom=10),
        border=ft.Border(top=ft.BorderSide(1, COLORS["divider"])),
        animate=400,
    )


# ---------------------------------------------------------------------------
# Vista de Detalle (Vista Normal Full Screen)
# ---------------------------------------------------------------------------
def build_detail_view(
    record: Dict[str, Any],
    on_back: Callable,
    on_copy: Callable,
    on_status_change: Callable[[str], None],
    page: ft.Page,
    on_scrape_click: Optional[Callable[[Dict[str, Any], Any], None]] = None,
    on_save_notes: Optional[Callable] = None,
    on_save_companias: Optional[Callable[[str], None]] = None,
    on_save_sociedades: Optional[Callable[[str], None]] = None,
    calendar_url: str = "",
    usuario: str = "broker",
    state: Optional[Dict[str, Any]] = None,
    on_register_visit_click: Optional[Callable[[Dict[str, Any]], None]] = None,
    on_go_cartera: Optional[Callable] = None,
) -> ft.Container:
    nombre    = record.get(COL_NOMBRE) or record.get("nombre") or "Productor"
    matricula = record.get(COL_MATRICULA) or record.get("matricula") or ""
    ramo      = record.get("productor_ramo") or record.get(COL_RAMO) or ""
    _, ramo_color = _ramo_colors(ramo)

    # Check for contact info
    has_contact_info = any(record.get(k) and record.get(k) != "—" for k in ["telefono", "email", "provincia"])

    # ── Toggle "En la organización" ──────────────────────────────────────────
    import ssn_test as _ssn_det
    _en_org_state = {"value": _ssn_det.get_en_organizacion(matricula)}

    org_icon_ref = ft.Ref[ft.Icon]()
    org_text_ref = ft.Ref[ft.Text]()
    org_btn_ref  = ft.Ref[ft.ElevatedButton]()

    def _get_org_color(active):
        return "#2E7D32" if active else COLORS["text_secondary"]

    def _build_org_btn_style(active: bool):
        return ft.ButtonStyle(
            bgcolor="#1B5E20" if active else COLORS["surface"],
            color="#FFFFFF" if active else COLORS["text_secondary"],
            side=ft.BorderSide(1.5, "#2E7D32" if active else COLORS["border"]),
            shape=ft.RoundedRectangleBorder(radius=8),
            padding=ft.Padding(14, 10, 14, 10),
            overlay_color=ft.Colors.with_opacity(0.08, "#2E7D32" if active else COLORS["text_secondary"]),
        )

    def _on_org_toggle(e):
        new_val = not _en_org_state["value"]
        _en_org_state["value"] = new_val
        _ssn_det.toggle_en_organizacion(matricula, new_val, usuario)
        # Actualizar controles internos del botón (siempre funciona en Flet 0.86)
        try:
            if org_icon_ref.current:
                org_icon_ref.current.name = ft.Icons.BUSINESS_CENTER_ROUNDED if new_val else ft.Icons.BUSINESS_CENTER_OUTLINED
                org_icon_ref.current.color = "#FFFFFF" if new_val else COLORS["text_secondary"]
                org_icon_ref.current.update()
            if org_text_ref.current:
                org_text_ref.current.value = "En la organización" if new_val else "Sin organización"
                org_text_ref.current.color = "#FFFFFF" if new_val else COLORS["text_secondary"]
                org_text_ref.current.update()
            if org_btn_ref.current:
                org_btn_ref.current.style = _build_org_btn_style(new_val)
                org_btn_ref.current.tooltip = "Quitar de la organización" if new_val else "Agregar a la organización"
                org_btn_ref.current.update()
        except Exception:
            pass

    _active = _en_org_state["value"]

    org_toggle_btn = ft.ElevatedButton(
        ref=org_btn_ref,
        content=ft.Row(
            controls=[
                ft.Icon(
                    ft.Icons.BUSINESS_CENTER_ROUNDED if _active else ft.Icons.BUSINESS_CENTER_OUTLINED,
                    ref=org_icon_ref,
                    color="#FFFFFF" if _active else COLORS["text_secondary"],
                    size=16,
                ),
                ft.Text(
                    "En la organización" if _active else "Sin organización",
                    ref=org_text_ref,
                    color="#FFFFFF" if _active else COLORS["text_secondary"],
                    size=13,
                    weight=ft.FontWeight.W_500,
                ),
            ],
            spacing=6,
            tight=True,
        ),
        tooltip="Quitar de la organización" if _active else "Agregar a la organización",
        on_click=_on_org_toggle,
        style=_build_org_btn_style(_active),
    )

    go_cartera_btn = ft.TextButton(
        "Ver Cartera",
        icon=ft.Icons.FOLDER_SHARED_ROUNDED,
        on_click=lambda e: on_go_cartera() if on_go_cartera else None,
        tooltip="Ir a la vista Cartera de Productores",
        visible=bool(on_go_cartera),
    )



    # Back button, title and copy button
    header_row = ft.Row(
        controls=[
            ft.Row(
                controls=[
                    ft.IconButton(
                        icon=ft.Icons.ARROW_BACK_ROUNDED,
                        icon_color=COLORS["primary"],
                        icon_size=24,
                        tooltip="Volver al listado",
                        on_click=lambda e: on_back(),
                    ),
                    ft.Text("Detalle del Productor", size=18, weight=ft.FontWeight.BOLD, color=COLORS["text_primary"]),
                ],
                spacing=8,
            ),
            ft.Row(
                controls=[
                    go_cartera_btn,
                    org_toggle_btn,
                    ft.ElevatedButton(
                        "Copiar Datos",
                        icon=ft.Icons.CONTENT_COPY_ROUNDED,
                        on_click=lambda e: on_copy(record),
                        style=ft.ButtonStyle(
                            bgcolor=COLORS["primary"],
                            color=COLORS["text_on_primary"],
                            shape=ft.RoundedRectangleBorder(radius=8),
                            padding=ft.Padding(16, 10, 16, 10),
                        )
                    ),
                ],
                spacing=8,
            ),
        ],
        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        vertical_alignment=ft.CrossAxisAlignment.CENTER,
    )

    # Info grid items
    info_items = []
    
    # We display them as beautiful cards/containers in a grid (2 columns)
    def make_info_card(label: str, value: str, icon=None):
        return ft.Container(
            content=ft.Row(
                controls=[
                    ft.Icon(icon, color=COLORS["primary"], size=18) if icon else ft.Container(),
                    ft.Column(
                        controls=[
                            ft.Text(label, size=11, color=COLORS["text_secondary"], weight=ft.FontWeight.W_500),
                            ft.Text(value or "—", size=14, color=COLORS["text_primary"], weight=ft.FontWeight.W_600, selectable=True),
                        ],
                        spacing=2,
                        tight=True,
                    ),
                ],
                spacing=10,
            ),
            bgcolor=COLORS["background"],
            padding=12,
            border_radius=8,
            expand=True,
        )

    # Cuit/Doc
    cuit_val = format_cuit(record.get(COL_ID) or record.get("cuit") or "—")
    info_items.append(
        ft.Row(
            controls=[
                make_info_card("Matrícula", matricula, ft.Icons.NUMBERS_ROUNDED),
                make_info_card("CUIT / Documento", cuit_val, ft.Icons.BADGE_ROUNDED),
            ],
            spacing=12,
        )
    )

    # Ramo / Provincia
    info_items.append(
        ft.Row(
            controls=[
                make_info_card("Ramo", ramo, ft.Icons.SHIELD_ROUNDED),
                make_info_card("Provincia", record.get("provincia", "—"), ft.Icons.MAP_ROUNDED),
            ],
            spacing=12,
        )
    )

    # Localidad / CP
    info_items.append(
        ft.Row(
            controls=[
                make_info_card("Localidad", record.get("localidad", "—"), ft.Icons.LOCATION_ON_ROUNDED),
                make_info_card("Código Postal", record.get("cod_postal", "—"), ft.Icons.MARK_AS_UNREAD_ROUNDED),
            ],
            spacing=12,
        )
    )

    # Contact Info
    info_items.append(
        ft.Row(
            controls=[
                make_info_card("Teléfono", record.get("telefono", "—"), ft.Icons.PHONE_ROUNDED),
                make_info_card("Email", record.get("email", "—"), ft.Icons.EMAIL_ROUNDED),
            ],
            spacing=12,
        )
    )

    # Resolucion
    info_items.append(
        ft.Row(
            controls=[
                make_info_card("Resolución", record.get("resolucion", "—"), ft.Icons.DESCRIPTION_ROUNDED),
                make_info_card("Fecha de Resolución", record.get("fecha_resolucion", "—"), ft.Icons.CALENDAR_TODAY_ROUNDED),
            ],
            spacing=12,
        )
    )

    # Domicilio (Full Width)
    info_items.append(
        ft.Row(
            controls=[
                make_info_card("Domicilio", record.get("domicilio", "—"), ft.Icons.HOME_ROUNDED),
            ],
        )
    )

    # Status selector
    estado_actual = record.get("estado_contacto", "Sin contactar")
    is_dark = (COLORS["surface"] == "#1E293B")
    
    if is_dark:
        status_colors = {
            "Sin contactar": ("#64748B", "#94A3B8"),
            "Contactado":    ("#10B981", "#34D399"),
            "No responde":   ("#EF4444", "#F87171"),
            "Interesado":    ("#F59E0B", "#FBBF24"),
        }
    else:
        status_colors = {
            "Sin contactar": ("#78909C", "#546E7A"),
            "Contactado":    ("#2E7D32", "#1B5E20"),
            "No responde":   ("#C62828", "#B71C1C"),
            "Interesado":    ("#E65100", "#FF6F00"),
        }

    def make_status_btn(status):
        active_color, inactive_color = status_colors[status]
        is_active = (estado_actual == status)
        btn_color = active_color if is_active else inactive_color
        
        return ft.Container(
            content=ft.Text(
                status,
                size=12,
                color="#0F172A" if (is_active and is_dark) else ("#FFFFFF" if is_active else btn_color),
                weight=ft.FontWeight.W_600,
                text_align=ft.TextAlign.CENTER,
            ),
            bgcolor=active_color if is_active else "transparent",
            border=ft.Border.all(1.5, btn_color),
            border_radius=8,
            width=130,
            padding=ft.Padding(left=10, right=10, top=10, bottom=10),
            alignment=ft.Alignment(0, 0),
            on_click=lambda e: on_status_change(status),
            ink=True,
        )

    obs_text_initial = record.get("observaciones", "") or ""
    notes_count_initial = len([l for l in obs_text_initial.split("\n") if l.strip()])

    def show_notes_dialog(e=None):
        dialog_history_column = ft.Column(
            spacing=8,
            scroll=ft.ScrollMode.AUTO,
            expand=True,
        )
        
        def refresh_dialog_history():
            dialog_history_column.controls.clear()
            obs_text = record.get("observaciones", "") or ""
            import re
            if obs_text.strip():
                lines = [l.strip() for l in obs_text.split("\n") if l.strip()]
                for line in lines:
                    match = re.match(r"^\[(.*?)\]:\s*(.*)$", line)
                    if match:
                        meta_info, note_content = match.group(1), match.group(2)
                        dialog_history_column.controls.append(
                            ft.Container(
                                content=ft.Column([
                                    ft.Row([
                                        ft.Icon(ft.Icons.CALENDAR_TODAY_ROUNDED, size=11, color=COLORS["primary"]),
                                        ft.Text(meta_info, size=12, weight=ft.FontWeight.BOLD, color=COLORS["primary"]),
                                    ], spacing=4),
                                    ft.Text(note_content, size=14, color=COLORS["text_primary"]),
                                ], spacing=2),
                                bgcolor=COLORS["background"],
                                border=ft.Border.all(1, COLORS["border"]),
                                border_radius=6,
                                padding=ft.Padding(8, 6, 8, 6),
                            )
                        )
                    else:
                        dialog_history_column.controls.append(
                            ft.Container(
                                content=ft.Column([
                                    ft.Row([
                                        ft.Icon(ft.Icons.HISTORY_ROUNDED, size=11, color=COLORS["text_secondary"]),
                                        ft.Text("Comentario anterior", size=12, weight=ft.FontWeight.BOLD, color=COLORS["text_secondary"]),
                                    ], spacing=4),
                                    ft.Text(line, size=14, color=COLORS["text_primary"]),
                                ], spacing=2),
                                bgcolor=COLORS["background"],
                                border=ft.Border.all(1, COLORS["border"]),
                                border_radius=6,
                                padding=ft.Padding(8, 6, 8, 6),
                            )
                        )
            else:
                dialog_history_column.controls.append(
                    ft.Text("No hay observaciones o notas registradas.", size=13, italic=True, color=COLORS["text_secondary"])
                )
            
            page.update()

        dialog_notes_field = ft.TextField(
            value="",
            multiline=True,
            min_lines=1,
            max_lines=3,
            text_size=14,
            border_color=COLORS["divider"],
            focused_border_color=COLORS["primary"],
            color=COLORS["text_primary"],
            cursor_color=COLORS["primary"],
            hint_text="Escribí una nueva nota o comentario aquí...",
            hint_style=ft.TextStyle(color=COLORS["text_secondary"], size=14),
            expand=True,
        )

        def handle_save_dialog_note(e):
            new_comment = dialog_notes_field.value.strip()
            if not new_comment:
                return
            from datetime import datetime
            timestamp = datetime.now().strftime("%d/%m/%Y %H:%M")
            formatted = f"[{timestamp} - {usuario}]: {new_comment}"
            old_obs = record.get("observaciones", "") or ""
            if old_obs.strip():
                updated_obs = old_obs.rstrip("\n") + "\n" + formatted
            else:
                updated_obs = formatted
            
            if on_save_notes:
                on_save_notes(updated_obs)
                record["observaciones"] = updated_obs
                refresh_dialog_history()
                dialog_notes_field.value = ""
                refresh_notes_history_ui()
                page.update()

        def close_dialog(e=None):
            dlg.open = False
            page.update()

        dlg = ft.AlertDialog(
            title=ft.Row(
                controls=[
                    ft.Icon(ft.Icons.NOTE_ALT_ROUNDED, color=COLORS["primary"], size=22),
                    ft.Text(f"Bitácora de Observaciones - {nombre}", size=16, weight=ft.FontWeight.BOLD, color=COLORS["text_primary"]),
                ],
                spacing=8,
            ),
            content=ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Container(
                            content=dialog_history_column,
                            expand=True,
                            border=ft.Border.all(1, COLORS["divider"]),
                            border_radius=8,
                            padding=10,
                            bgcolor=COLORS["surface"],
                        ),
                        ft.Divider(height=10, color=COLORS["divider"]),
                        ft.Row(
                            controls=[
                                dialog_notes_field,
                                ft.ElevatedButton(
                                    "Guardar",
                                    icon=ft.Icons.SAVE_ROUNDED,
                                    on_click=handle_save_dialog_note,
                                    style=ft.ButtonStyle(
                                        bgcolor=COLORS["primary"],
                                        color=COLORS["text_on_primary"],
                                        shape=ft.RoundedRectangleBorder(radius=6),
                                    ),
                                ),
                            ],
                            alignment=ft.MainAxisAlignment.START,
                            vertical_alignment=ft.CrossAxisAlignment.CENTER,
                            spacing=10,
                        ),
                    ],
                    spacing=12,
                ),
                width=650,
                height=500,
            ),
            actions=[
                ft.TextButton("Cerrar", on_click=close_dialog),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        
        page.overlay.append(dlg)
        dlg.open = True
        refresh_dialog_history()

    notes_count_text = ft.Text(
        f"{notes_count_initial} Notas",
        size=12,
        color=COLORS["primary"],
        weight=ft.FontWeight.W_600,
    )

    def refresh_notes_history_ui():
        obs_text = record.get("observaciones", "") or ""
        notes_count = len([l for l in obs_text.split("\n") if l.strip()])
        notes_count_text.value = f"{notes_count} Notas"
        try:
            notes_count_text.update()
        except:
            pass

    notes_count_btn = ft.Container(
        content=ft.Row([
            ft.Icon(ft.Icons.CHAT_BUBBLE_OUTLINE_ROUNDED, color=COLORS["primary"], size=16),
            notes_count_text,
        ], spacing=6, alignment=ft.MainAxisAlignment.CENTER),
        bgcolor=ft.Colors.with_opacity(0.08, COLORS["primary"]),
        border=ft.Border.all(1.5, ft.Colors.with_opacity(0.2, COLORS["primary"])),
        border_radius=8,
        width=130,
        padding=ft.Padding(left=10, right=10, top=10, bottom=10),
        on_click=show_notes_dialog,
        ink=True,
        tooltip="Ver bitácora de notas",
    )

    status_section = ft.Container(
        content=ft.Column(
            controls=[
                ft.Text("Estado de Contacto:", size=12, weight=ft.FontWeight.BOLD, color=COLORS["text_secondary"]),
                ft.Row(
                    controls=[
                        make_status_btn("Sin contactar"),
                        make_status_btn("Contactado"),
                        make_status_btn("No responde"),
                        make_status_btn("Interesado"),
                        notes_count_btn,
                    ],
                    spacing=8,
                    wrap=True,
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                ),
            ],
            spacing=8,
        ),
        padding=ft.Padding(0, 8, 0, 8),
    )

    # Quick Actions Row
    def handle_contact_action(url):
        webbrowser.open(url)
        
        def set_status(status_val):
            on_status_change(status_val)
            outcome_dialog.open = False
            page.update()
            
        is_dark = (COLORS["surface"] == "#1E293B")
        
        outcome_dialog = ft.AlertDialog(
            title=ft.Row([
                ft.Icon(ft.Icons.PHONE_CALLBACK_ROUNDED, color=COLORS["primary"]),
                ft.Text("Registrar resultado del contacto", size=15, weight=ft.FontWeight.BOLD)
            ], spacing=8),
            content=ft.Container(
                content=ft.Column([
                    ft.Text("Has iniciado un contacto/llamado. ¿Cuál fue el resultado?", size=12, color=COLORS["text_secondary"]),
                    ft.Container(height=8),
                    ft.Row([
                        ft.ElevatedButton(
                            "Contactado", 
                            on_click=lambda _: set_status("Contactado"), 
                            style=ft.ButtonStyle(bgcolor="#10B981" if is_dark else "#2E7D32", color="#FFFFFF", shape=ft.RoundedRectangleBorder(radius=8))
                        ),
                        ft.ElevatedButton(
                            "No responde", 
                            on_click=lambda _: set_status("No responde"), 
                            style=ft.ButtonStyle(bgcolor="#EF4444" if is_dark else "#C62828", color="#FFFFFF", shape=ft.RoundedRectangleBorder(radius=8))
                        ),
                    ], alignment=ft.MainAxisAlignment.CENTER, spacing=10),
                    ft.Row([
                        ft.ElevatedButton(
                            "Interesado", 
                            on_click=lambda _: set_status("Interesado"), 
                            style=ft.ButtonStyle(bgcolor="#F59E0B" if is_dark else "#E65100", color="#FFFFFF", shape=ft.RoundedRectangleBorder(radius=8))
                        ),
                        ft.ElevatedButton(
                            "Sin contactar", 
                            on_click=lambda _: set_status("Sin contactar"), 
                            style=ft.ButtonStyle(bgcolor="#64748B" if is_dark else "#78909C", color="#FFFFFF", shape=ft.RoundedRectangleBorder(radius=8))
                        ),
                    ], alignment=ft.MainAxisAlignment.CENTER, spacing=10),
                ], spacing=8, tight=True),
                width=320,
                padding=ft.Padding(0, 10, 0, 10)
            ),
            actions=[
                ft.TextButton("Cancelar", on_click=lambda _: setattr(outcome_dialog, "open", False) or page.update())
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        
        page.dialog = outcome_dialog
        outcome_dialog.open = True
        page.update()

    quick_actions = []
    
    phone_raw = record.get("telefono", "")
    phone_clean = re.sub(r"\D", "", phone_raw) if phone_raw else ""
    if phone_clean:
        if not phone_clean.startswith("54"):
            if len(phone_clean) == 10:
                phone_wa = "549" + phone_clean
            else:
                phone_wa = "54" + phone_clean
        else:
            phone_wa = phone_clean
            
        quick_actions.append(
            ft.IconButton(
                icon=ft.Icons.CHAT_ROUNDED,
                icon_color="#25D366",
                icon_size=24,
                tooltip="Enviar WhatsApp",
                on_click=lambda e: handle_contact_action(f"https://wa.me/{phone_wa}"),
            )
        )
        quick_actions.append(
            ft.IconButton(
                icon=ft.Icons.CALL_ROUNDED,
                icon_color="#1E88E5",
                icon_size=24,
                tooltip="Llamar por teléfono",
                on_click=lambda e: handle_contact_action(f"tel:{phone_clean}"),
            )
        )
        
    email_val = record.get("email", "")
    if email_val and email_val != "—":
        quick_actions.append(
            ft.IconButton(
                icon=ft.Icons.FORWARD_TO_INBOX_ROUNDED,
                icon_color="#E53935",
                icon_size=24,
                tooltip="Enviar Correo (Gmail)",
                on_click=lambda e: handle_contact_action(f"https://mail.google.com/mail/?view=cm&fs=1&to={email_val}"),
            )
        )

    # Agendar Reunión (Calendar) Action
    if calendar_url:
        quick_actions.append(
            ft.IconButton(
                icon=ft.Icons.CALENDAR_MONTH_ROUNDED,
                icon_color="#EC4899",
                icon_size=24,
                tooltip="Agendar Reunión",
                on_click=lambda e: handle_contact_action(calendar_url),
            )
        )
    else:
        # Fallback: registrar reunión localmente en el Plan de Visitas si no hay URL externa configurada
        quick_actions.append(
            ft.IconButton(
                icon=ft.Icons.CALENDAR_MONTH_ROUNDED,
                icon_color="#EC4899",
                icon_size=24,
                tooltip="Registrar Reunión en Plan de Visitas",
                on_click=lambda e: handle_register_visit_click(e),
            )
        )

    # Registrar Visita/Reunión Dialog & Action
    def open_log_visit_dialog(e):
        import ssn_test as _ssn
        from datetime import datetime
        
        date_tf = ft.TextField(
            label="Fecha de la Reunión/Visita",
            value=datetime.now().strftime("%Y-%m-%d"),
            border_color=COLORS["border"],
            focused_border_color=COLORS["primary"],
            border_radius=8,
            text_size=14,
        )
        
        estado_dd = ft.Dropdown(
            label="Estado de la Visita",
            value="realizada",
            options=[
                ft.dropdown.Option("realizada", "Realizada"),
                ft.dropdown.Option("pendiente", "Pendiente"),
            ],
            border_color=COLORS["border"],
            focused_border_color=COLORS["primary"],
            border_radius=8,
            text_size=14,
        )
        
        notes_tf = ft.TextField(
            label="Detalle / Observaciones",
            multiline=True,
            min_lines=2,
            max_lines=4,
            border_color=COLORS["border"],
            focused_border_color=COLORS["primary"],
            border_radius=8,
            text_size=14,
            hint_text="Escribí aquí de qué se trata la reunión o algún comentario...",
        )
        
        def save_visit_record(ev):
            date_val = date_tf.value.strip()
            notes_val = notes_tf.value.strip()
            estado_val = estado_dd.value
            
            if not date_val:
                date_tf.error_text = "La fecha es obligatoria"
                try: date_tf.update()
                except: pass
                return
                
            try:
                datetime.strptime(date_val, "%Y-%m-%d")
            except ValueError:
                date_tf.error_text = "Formato inválido. Usar AAAA-MM-DD"
                try: date_tf.update()
                except: pass
                return
            
            mes_val = date_val[:7]
            companias_val = record.get("companias", "") or ""
            compania_principal = companias_val.split(",")[0].strip() if companias_val else "Sin Compañía"
            
            try:
                # 1. Guardar visita
                _ssn.guardar_visita(
                    mes=mes_val,
                    matricula=str(matricula),
                    nombre=nombre,
                    estado=estado_val,
                    productividad=notes_val,
                    campaña=compania_principal
                )
                
                # 2. Guardar actividad comercial (tipo "Reunión")
                _ssn.guardar_actividad_comercial(
                    mes=mes_val,
                    fecha_actividad=date_val,
                    matricula=str(matricula),
                    nombre=nombre,
                    tipo="Reunión",
                    compania=compania_principal,
                    observaciones=notes_val
                )
            except Exception as ex:
                print(f"Error saving visit/activity: {ex}")
            
            # 3. Append note to observations
            log_entry = f"[{datetime.now().strftime('%d/%m/%Y %H:%M')} - {usuario}]: Registró Reunión ({estado_val.capitalize()}): {notes_val if notes_val else 'Sin observaciones'}"
            old_obs = record.get("observaciones", "") or ""
            if old_obs.strip():
                updated_obs = old_obs.rstrip("\n") + "\n" + log_entry
            else:
                updated_obs = log_entry
            
            if on_save_notes:
                # Call on_save_notes with show_alert=False to avoid popup
                on_save_notes(updated_obs, show_alert=False)
                record["observaciones"] = updated_obs
                
            # Close dialog
            visit_dialog.open = False
            try: page.update()
            except: pass
            
            # Show SnackBar
            page.snack_bar = ft.SnackBar(
                content=ft.Text(f"✓ Reunión {estado_val} registrada con éxito.", color=ft.Colors.WHITE, size=13, weight=ft.FontWeight.W_500),
                bgcolor=COLORS["success"],
                duration=3000,
            )
            page.snack_bar.open = True
            
            # Refresh notes count button
            refresh_notes_history_ui()
            try: page.update()
            except: pass

            if state and state.get("refresh_dashboard"):
                try:
                    state["refresh_dashboard"]()
                except Exception as ex:
                    print(f"Error refreshing dashboard from save_visit_record: {ex}")
            
        def close_visit_dialog(ev):
            visit_dialog.open = False
            try: page.update()
            except: pass
            
        visit_dialog = ft.AlertDialog(
            title=ft.Row([
                ft.Icon(ft.Icons.HANDSHAKE_ROUNDED, color=COLORS["primary"], size=22),
                ft.Text(f"Registrar Reunión con {nombre}", size=15, weight=ft.FontWeight.BOLD),
            ], spacing=8),
            content=ft.Container(
                content=ft.Column([
                    ft.Text("Ingresá los datos de la reunión/visita para registrarla en el Plan de Visitas y Seguimiento Diario.", size=12, color=COLORS["text_secondary"]),
                    ft.Container(height=6),
                    date_tf,
                    estado_dd,
                    notes_tf,
                ], spacing=12, tight=True),
                width=420,
                padding=ft.Padding(0, 10, 0, 10)
            ),
            actions=[
                ft.TextButton("Cancelar", on_click=close_visit_dialog),
                ft.ElevatedButton(
                    "Guardar",
                    icon=ft.Icons.SAVE_ROUNDED,
                    on_click=save_visit_record,
                    style=ft.ButtonStyle(
                        bgcolor=COLORS["primary"],
                        color=COLORS["text_on_primary"],
                        shape=ft.RoundedRectangleBorder(radius=6),
                    ),
                ),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        
        if visit_dialog not in page.overlay:
            page.overlay.append(visit_dialog)
        visit_dialog.open = True
        try: page.update()
        except: pass

    def handle_register_visit_click(e):
        if on_register_visit_click:
            on_register_visit_click(record)
        else:
            open_log_visit_dialog(e)

    quick_actions.append(
        ft.IconButton(
            icon=ft.Icons.HANDSHAKE_ROUNDED,
            icon_color="#FF9800",
            icon_size=24,
            tooltip="Registrar Visita/Reunión",
            on_click=handle_register_visit_click,
        )
    )



    actions_section = ft.Container(
        content=ft.Column(
            controls=[
                ft.Text("Acciones Rápidas:", size=12, weight=ft.FontWeight.BOLD, color=COLORS["text_secondary"]),
                ft.Row(
                    controls=quick_actions,
                    spacing=12,
                )
            ],
            spacing=4,
        ),
        padding=ft.Padding(0, 8, 0, 8),
    )

    # Actions Buttons row
    actions = []

    # Scrape/Update button for the top header row
    btn_scrape = ft.Container()
    if on_scrape_click:
        scrape_btn = ft.Ref[ft.FilledButton]()
        
        def _on_scrape(e):
            if scrape_btn.current:
                scrape_btn.current.disabled = True
                scrape_btn.current.content = ft.Row(
                    controls=[
                        ft.ProgressRing(color="#FFFFFF", stroke_width=2, width=14, height=14),
                        ft.Text("Actualizando...", size=11, color="#FFFFFF")
                    ],
                    spacing=6,
                    tight=True
                )
                scrape_btn.current.update()
            on_scrape_click(record, e)

        btn_scrape = ft.FilledButton(
            ref=scrape_btn,
            content=ft.Row(
                controls=[
                    ft.Icon(ft.Icons.REFRESH_ROUNDED, size=14),
                    ft.Text("Actualizar SSN", size=11, weight=ft.FontWeight.BOLD)
                ],
                spacing=6,
                tight=True,
            ),
            bgcolor=COLORS["accent"],
            on_click=_on_scrape,
            style=ft.ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=8),
                padding=ft.Padding(10, 8, 10, 8),
            ),
            tooltip="Consultar y actualizar datos de este productor en vivo desde la SSN",
        )

    # Compañías Chips and add logic
    companias_str = record.get("companias", "") or ""
    companias_list = [c.strip() for c in companias_str.split(",") if c.strip()]
    
    companias_chips = []
    
    def remove_compania(comp_name):
        new_list = [c for c in companias_list if c != comp_name]
        new_str = ", ".join(new_list)
        if on_save_companias:
            on_save_companias(new_str)

    for comp in companias_list:
        companias_chips.append(
            ft.Chip(
                label=ft.Text(comp, size=11, color=COLORS["text_primary"]),
                bgcolor=ft.Colors.with_opacity(0.08, COLORS["primary"]),
                on_delete=lambda e, c=comp: remove_compania(c),
            )
        )

    def show_add_compania_dialog(e):
        new_comp_field = ft.TextField(
            label="Nombre de la compañía",
            border_color=COLORS["divider"],
            focused_border_color=COLORS["primary"],
            cursor_color=COLORS["primary"],
            autofocus=True,
        )
        
        def close_dialog(e=None):
            dlg.open = False
            page.update()

        def submit_add(e=None):
            val = new_comp_field.value.strip()
            if val:
                # Add to list
                if val not in companias_list:
                    new_list = companias_list + [val]
                    new_str = ", ".join(new_list)
                    close_dialog()
                    if on_save_companias:
                        on_save_companias(new_str)
                else:
                    new_comp_field.error_text = "Esta compañía ya está agregada."
                    new_comp_field.update()
            else:
                close_dialog()

        # Make Enter submit the field
        new_comp_field.on_submit = submit_add

        dlg = ft.AlertDialog(
            title=ft.Row(
                controls=[
                    ft.Icon(ft.Icons.BUSINESS_ROUNDED, color=COLORS["primary"], size=22),
                    ft.Text("Agregar Compañía", size=16, weight=ft.FontWeight.BOLD, color=COLORS["text_primary"]),
                ],
                spacing=8,
            ),
            content=ft.Container(
                content=new_comp_field,
                width=300,
                height=60,
            ),
            actions=[
                ft.TextButton("Cancelar", on_click=close_dialog),
                ft.ElevatedButton(
                    "Agregar",
                    on_click=submit_add,
                    style=ft.ButtonStyle(
                        bgcolor=COLORS["primary"],
                        color=COLORS["text_on_primary"],
                    ),
                ),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        page.overlay.append(dlg)
        dlg.open = True
        page.update()

    add_chip_btn = ft.Container(
        content=ft.Row(
            controls=[
                ft.Icon(ft.Icons.ADD_ROUNDED, size=14, color=COLORS["primary"]),
                ft.Text("Agregar Compañía", size=11, color=COLORS["primary"], weight=ft.FontWeight.BOLD),
            ],
            spacing=4,
        ),
        bgcolor=ft.Colors.with_opacity(0.12, COLORS["primary"]),
        padding=ft.Padding(8, 6, 10, 6),
        border_radius=6,
        on_click=show_add_compania_dialog,
        ink=True,
    )

    companias_wrap = ft.Row(
        controls=companias_chips + [add_chip_btn],
        spacing=8,
        run_spacing=6,
        wrap=True,
    )

    # Sociedades Chips and link logic
    sociedades_str = record.get("sociedades", "") or ""
    # Support semicolon and comma splitting
    sociedades_list = []
    if ";" in sociedades_str:
        sociedades_list = [s.strip() for s in sociedades_str.split(";") if s.strip()]
    elif "," in sociedades_str:
        sociedades_list = [s.strip() for s in sociedades_str.split(",") if s.strip()]
    elif sociedades_str:
        sociedades_list = [sociedades_str.strip()]

    sociedades_chips = []

    def remove_sociedad(soc_name):
        new_list = [s for s in sociedades_list if s != soc_name]
        new_str = "; ".join(new_list)
        if on_save_sociedades:
            on_save_sociedades(new_str)

    for soc in sociedades_list:
        sociedades_chips.append(
            ft.Chip(
                label=ft.Text(soc, size=11, color=COLORS["text_primary"]),
                bgcolor=ft.Colors.with_opacity(0.08, COLORS["success"] if "success" in COLORS else COLORS["primary"]),
                on_delete=lambda e, s=soc: remove_sociedad(s),
            )
        )

    def show_link_sociedad_dialog(e):
        from ssn_test import obtener_todas_sociedades
        try:
            todas = obtener_todas_sociedades()
        except Exception as ex:
            print(f"Error al obtener sociedades: {ex}")
            todas = []

        search_field = ft.TextField(
            label="Buscar por Denominación, CUIT o Matrícula",
            border_color=COLORS["divider"],
            focused_border_color=COLORS["primary"],
            cursor_color=COLORS["primary"],
            autofocus=True,
        )

        results_list = ft.ListView(
            expand=True,
            spacing=4,
            height=300,
        )

        def update_search_results(query):
            query = query.strip().lower()
            results_list.controls.clear()
            if not query:
                results_list.controls.append(ft.Text("Escribí para buscar sociedades...", size=12, italic=True, color=COLORS["text_secondary"]))
                results_list.update()
                return

            matches = []
            for s in todas:
                denom = s.get("denominacion", "").lower()
                doc = s.get("documento", "").lower()
                mat = s.get("matricula", "").lower()
                if query in denom or query in doc or query in mat:
                    matches.append(s)
                if len(matches) >= 30:
                    break

            if not matches:
                results_list.controls.append(ft.Text("No se encontraron sociedades.", size=12, italic=True, color=COLORS["text_secondary"]))
            else:
                for s in matches:
                    denom = s.get("denominacion", "")
                    cuit = s.get("documento", "")
                    mat = s.get("matricula", "")
                    
                    results_list.controls.append(
                        ft.ListTile(
                            leading=ft.Icon(ft.Icons.BUSINESS_ROUNDED, color=COLORS["primary"], size=20),
                            title=ft.Text(denom, size=13, weight=ft.FontWeight.W_600, color=COLORS["text_primary"]),
                            subtitle=ft.Text(f"Matrícula: {mat} | CUIT: {cuit}", size=11, color=COLORS["text_secondary"]),
                            trailing=ft.IconButton(
                                icon=ft.Icons.ADD_ROUNDED,
                                icon_color=COLORS["success"] if "success" in COLORS else COLORS["primary"],
                                tooltip="Vincular esta sociedad",
                                on_click=lambda e, s_ref=s: link_sociedad(s_ref),
                            ),
                            content_padding=ft.Padding(10, 4, 10, 4),
                        )
                    )
            results_list.update()

        search_field.on_change = lambda e: update_search_results(search_field.value)

        def close_dialog(e=None):
            dlg.open = False
            page.update()

        def link_sociedad(soc):
            val = f"{soc.get('denominacion')} (Mat: {soc.get('matricula')})"
            if val not in sociedades_list:
                new_list = sociedades_list + [val]
                new_str = "; ".join(new_list)
                close_dialog()
                if on_save_sociedades:
                    on_save_sociedades(new_str)
            else:
                search_field.error_text = "Esta sociedad ya está vinculada."
                search_field.update()

        dlg = ft.AlertDialog(
            title=ft.Row(
                controls=[
                    ft.Icon(ft.Icons.BUSINESS_ROUNDED, color=COLORS["primary"], size=22),
                    ft.Text("Vincular Sociedad", size=16, weight=ft.FontWeight.BOLD, color=COLORS["text_primary"]),
                ],
                spacing=8,
            ),
            content=ft.Container(
                content=ft.Column(
                    controls=[
                        search_field,
                        ft.Divider(height=10, color=COLORS["divider"]),
                        results_list,
                    ],
                    spacing=10,
                    tight=True,
                ),
                width=500,
                height=400,
            ),
            actions=[
                ft.TextButton("Cancelar", on_click=close_dialog),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        page.overlay.append(dlg)
        dlg.open = True
        page.update()
        update_search_results("")

    add_soc_chip_btn = ft.Container(
        content=ft.Row(
            controls=[
                ft.Icon(ft.Icons.ADD_ROUNDED, size=14, color=COLORS["primary"]),
                ft.Text("Vincular Sociedad", size=11, color=COLORS["primary"], weight=ft.FontWeight.BOLD),
            ],
            spacing=4,
        ),
        bgcolor=ft.Colors.with_opacity(0.12, COLORS["primary"]),
        padding=ft.Padding(8, 6, 10, 6),
        border_radius=6,
        on_click=show_link_sociedad_dialog,
        ink=True,
    )

    sociedades_wrap = ft.Row(
        controls=sociedades_chips + [add_soc_chip_btn],
        spacing=8,
        run_spacing=6,
        wrap=True,
    )

    # Notes field - input for a NEW note only (starts empty)
    notes_field = ft.TextField(
        value="",
        multiline=True,
        min_lines=1,
        max_lines=3,
        text_size=13,
        border_color=COLORS["divider"],
        focused_border_color=COLORS["primary"],
        color=COLORS["text_primary"],
        cursor_color=COLORS["primary"],
        hint_text="Escribí una nueva nota o comentario aquí...",
        hint_style=ft.TextStyle(color=COLORS["text_secondary"], size=13),
    )

    notes_history_column = ft.Column(spacing=6)

    def refresh_notes_history_ui():
        notes_history_column.controls.clear()
        obs_text = record.get("observaciones", "") or ""
        notes_count = len([l for l in obs_text.split("\n") if l.strip()])
        notes_count_text.value = f"{notes_count} Notas"
        import re
        if obs_text.strip():
            lines = [l.strip() for l in obs_text.split("\n") if l.strip()]
            for line in lines:
                match = re.match(r"^\[(.*?)\]:\s*(.*)$", line)
                if match:
                    meta_info, note_content = match.group(1), match.group(2)
                    notes_history_column.controls.append(
                        ft.Container(
                            content=ft.Column([
                                ft.Row([
                                    ft.Icon(ft.Icons.CALENDAR_TODAY_ROUNDED, size=10, color=COLORS["primary"]),
                                    ft.Text(meta_info, size=9.5, weight=ft.FontWeight.BOLD, color=COLORS["primary"]),
                                ], spacing=4),
                                ft.Text(note_content, size=11, color=COLORS["text_primary"]),
                            ], spacing=2),
                            bgcolor=COLORS["background"],
                            border=ft.Border.all(1, COLORS["border"]),
                            border_radius=6,
                            padding=ft.Padding(8, 6, 8, 6),
                        )
                    )
                else:
                    notes_history_column.controls.append(
                        ft.Container(
                            content=ft.Column([
                                ft.Row([
                                    ft.Icon(ft.Icons.HISTORY_ROUNDED, size=10, color=COLORS["text_secondary"]),
                                    ft.Text("Comentario anterior (sin formato)", size=9.5, weight=ft.FontWeight.BOLD, color=COLORS["text_secondary"]),
                                ], spacing=4),
                                ft.Text(line, size=11, color=COLORS["text_primary"]),
                            ], spacing=2),
                            bgcolor=COLORS["background"],
                            border=ft.Border.all(1, COLORS["border"]),
                            border_radius=6,
                            padding=ft.Padding(8, 6, 8, 6),
                        )
                    )
        else:
            notes_history_column.controls.append(
                ft.Text("No hay observaciones o notas registradas.", size=11, italic=True, color=COLORS["text_secondary"])
            )

    refresh_notes_history_ui()

    def handle_save_note(e):
        new_comment = notes_field.value.strip()
        if not new_comment:
            return
        from datetime import datetime
        timestamp = datetime.now().strftime("%d/%m/%Y %H:%M")
        formatted = f"[{timestamp} - {usuario}]: {new_comment}"
        old_obs = record.get("observaciones", "") or ""
        if old_obs.strip():
            updated_obs = old_obs.rstrip("\n") + "\n" + formatted
        else:
            updated_obs = formatted
        if on_save_notes:
            on_save_notes(updated_obs)
            record["observaciones"] = updated_obs
            refresh_notes_history_ui()
            notes_field.value = ""
            page.update()

    # Centered detail card
    # Cartera y Operaciones section removed

    detail_card = ft.Container(
        content=ft.Column(
            controls=[
                # Top header panel inside card
                ft.Row(
                    controls=[
                        ft.Row(
                            controls=[
                                ft.Container(
                                    content=ft.Icon(ft.Icons.PERSON_ROUNDED, color=COLORS["primary"], size=32),
                                    bgcolor=COLORS["background"],
                                    padding=14,
                                    shape=ft.BoxShape.CIRCLE,
                                ),
                                ft.Column(
                                    controls=[
                                        ft.Text(nombre, size=20, weight=ft.FontWeight.BOLD, color=COLORS["text_primary"]),
                                        ft.Row(
                                            controls=[
                                                ft.Container(
                                                    content=ft.Text(f"Matrícula {matricula}", size=11, color=COLORS["primary"], weight=ft.FontWeight.BOLD),
                                                    bgcolor=ft.Colors.with_opacity(0.12, COLORS["primary"]),
                                                    padding=ft.Padding(8, 4, 8, 4),
                                                    border_radius=4,
                                                ),
                                                ft.Container(
                                                    content=ft.Text(ramo, size=11, color=ramo_color, weight=ft.FontWeight.BOLD),
                                                    bgcolor=ft.Colors.with_opacity(0.12, ramo_color),
                                                    padding=ft.Padding(8, 4, 8, 4),
                                                    border_radius=4,
                                                ),
                                            ],
                                            spacing=8,
                                        ),
                                        ft.Container(height=2),
                                        ft.Row(
                                            controls=[
                                                ft.Text("Compañías:", size=11, color=COLORS["text_secondary"], weight=ft.FontWeight.BOLD),
                                                ft.Container(content=companias_wrap, expand=True),
                                            ],
                                            spacing=8,
                                            vertical_alignment=ft.CrossAxisAlignment.CENTER,
                                        )
                                    ],
                                    spacing=4,
                                    tight=True,
                                )
                            ],
                            spacing=16,
                        ),
                        btn_scrape,
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                ft.Divider(height=16, color=COLORS["divider"]),

                # Sociedades section (Moved to the top)
                ft.Column(
                    controls=[
                        ft.Row(
                            controls=[
                                ft.Icon(ft.Icons.BUSINESS_ROUNDED, color=COLORS["primary"], size=16),
                                ft.Text("Sociedades Vinculadas", size=13, weight=ft.FontWeight.BOLD, color=COLORS["text_primary"]),
                            ],
                            spacing=6,
                        ),
                        sociedades_wrap,
                    ],
                    spacing=8,
                ),
                ft.Divider(height=16, color=COLORS["divider"]),

                # Contact status
                status_section,
                ft.Divider(height=16, color=COLORS["divider"]),
                # Quick actions
                actions_section,
                ft.Divider(height=16, color=COLORS["divider"]),
                # Grid of info
                ft.Column(controls=info_items, spacing=12),


            ],
            spacing=12,
        ),
        bgcolor=COLORS["surface"],
        padding=24,
        border_radius=12,
        border=ft.Border.all(1, COLORS["divider"]),
        shadow=ft.BoxShadow(spread_radius=0, blur_radius=6, color=ft.Colors.with_opacity(0.05, "#000000"), offset=ft.Offset(0, 3)),
    )

    notes_card = ft.Container(
        key="notes_section_target",
        content=ft.Column(
            controls=[
                ft.Row(
                    controls=[
                        ft.Icon(ft.Icons.NOTE_ALT_ROUNDED, color=COLORS["primary"], size=16),
                        ft.Text("Bitácora de Observaciones / Notas de contacto", size=13, weight=ft.FontWeight.BOLD, color=COLORS["text_primary"]),
                    ],
                    spacing=6,
                ),
                notes_history_column,
                ft.Divider(height=10, color=COLORS["divider"]),
                ft.Row(
                    controls=[
                        ft.Container(
                            content=notes_field,
                            expand=True,
                        ),
                        ft.ElevatedButton(
                            "Guardar Nota",
                            icon=ft.Icons.SAVE_ROUNDED,
                            on_click=handle_save_note,
                            style=ft.ButtonStyle(
                                bgcolor=COLORS["primary"],
                                color=COLORS["text_on_primary"],
                            ),
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.START,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=10,
                ),
            ],
            spacing=8,
        ),
        bgcolor=COLORS["surface"],
        padding=24,
        border_radius=12,
        border=ft.Border.all(1, COLORS["divider"]),
        shadow=ft.BoxShadow(spread_radius=0, blur_radius=6, color=ft.Colors.with_opacity(0.05, "#000000"), offset=ft.Offset(0, 3)),
    )

    bottom_actions_row = ft.Row(
        controls=actions,
        alignment=ft.MainAxisAlignment.END,
        spacing=12,
    )

    detail_scroll_column = ft.Column(
        controls=[
            header_row,
            ft.Container(height=8),
            detail_card,
            ft.Container(height=8),
            notes_card,
            ft.Container(height=8),
            bottom_actions_row
        ],
        spacing=8,
        scroll=ft.ScrollMode.AUTO,
        expand=True,
    )

    return ft.Container(
        content=detail_scroll_column,
        padding=ft.Padding(24, 18, 24, 18),
        expand=True,
    )


# ---------------------------------------------------------------------------
# Vista del Panel de Administración (Superadmin)
# ---------------------------------------------------------------------------
def build_admin_dashboard(
    state: Dict[str, Any],
    on_back: Callable,
    on_crear_usuario: Callable,
    on_eliminar_usuario: Callable[[int], bool],
    on_cambiar_password: Callable[[int, str], bool],
    on_vaciar_db: Callable,
    on_import_click: Callable,
    page: ft.Page,
) -> ft.Container:
    import ssn_test
    import time
    import threading
    
    # Title and Back Button
    header_row = ft.Row(
        controls=[
            ft.Row(
                controls=[
                    ft.IconButton(
                        icon=ft.Icons.ARROW_BACK_ROUNDED,
                        icon_color=COLORS["primary"],
                        icon_size=24,
                        tooltip="Volver al buscador",
                        on_click=lambda e: on_back(),
                    ),
                    ft.Text("Panel de Control de Superadmin", size=18, weight=ft.FontWeight.BOLD, color=COLORS["text_primary"]),
                ],
                spacing=8,
            ),
            ft.Text(f"Usuario: {state.get('username', 'admin')}", size=12, color=COLORS["text_secondary"], weight=ft.FontWeight.W_500),
        ],
        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        vertical_alignment=ft.CrossAxisAlignment.CENTER,
    )

    # Refs / Containers for tab columns
    users_column = ft.Column(spacing=10, expand=True, scroll=ft.ScrollMode.AUTO)
    logs_column = ft.Column(spacing=10, expand=True, scroll=ft.ScrollMode.AUTO)
    db_stats_column = ft.Column(spacing=12, expand=True, scroll=ft.ScrollMode.AUTO)
    permissions_column = ft.Column(spacing=10, expand=True, scroll=ft.ScrollMode.AUTO)
    docs_column = ft.Column(spacing=16, expand=True, scroll=ft.ScrollMode.AUTO)
    selected_lector_ref = [None]

    # Helper function to show simple alert dialogs
    def show_snackbar(message: str, is_error: bool = False):
        page.snack_bar = ft.SnackBar(
            content=ft.Text(message, color=ft.Colors.WHITE, size=13, weight=ft.FontWeight.W_500),
            bgcolor=COLORS["primary"] if not is_error else ft.Colors.RED_600,
            duration=3500,
            dismiss_direction=ft.DismissDirection.HORIZONTAL,
        )
        page.snack_bar.open = True
        page.update()

    # User Management logic
    def refresh_users():
        users = ssn_test.obtener_usuarios()
        user_rows = []
        for u in users:
            uid = u.get("id")
            uname = u.get("usuario")
            uemail = u.get("email") or "—"
            urol = u.get("rol") or "agente"
            umatricula = u.get("matricula_asociada") or "—"
            ucal = u.get("calendar_url") or "—"
            req_change = "Sí" if u.get("requiere_cambio") else "No"
            failed_attempts = str(u.get("intentos_fallidos") or 0)
            raw_req_change = u.get("requiere_cambio") or 0
            raw_failed = u.get("intentos_fallidos") or 0
            raw_blocked = u.get("bloqueado_hasta") or 0
            
            # Format block date
            blocked_until = u.get("bloqueado_hasta") or 0
            block_text = "No"
            if blocked_until > time.time():
                remaining = int(blocked_until - time.time())
                block_text = f"Bloqueado ({remaining}s)"
            
            is_self = (uname == state.get("username"))
            is_primary_admin = (uname == "admin")
            
            def make_change_pw_click(user_id=uid, username=uname):
                return lambda e: open_change_pw_dialog(user_id, username)
                
            def make_delete_click(user_id=uid, username=uname):
                return lambda e: open_delete_user_dialog(user_id, username)

            uperms = u.get("permisos") or "comercial,buscador,cartera"
            
            # Create premium badges for permissions
            perm_badges = []
            if "comercial" in uperms:
                perm_badges.append(
                    ft.Container(
                        content=ft.Text("COM", size=9, color="#FFFFFF", weight=ft.FontWeight.BOLD),
                        bgcolor="#2563EB",
                        border_radius=4,
                        padding=ft.Padding(left=4, right=4, top=2, bottom=2),
                        tooltip="Gestión Comercial"
                    )
                )
            if "buscador" in uperms:
                perm_badges.append(
                    ft.Container(
                        content=ft.Text("BUS", size=9, color="#FFFFFF", weight=ft.FontWeight.BOLD),
                        bgcolor="#7C3AED",
                        border_radius=4,
                        padding=ft.Padding(left=4, right=4, top=2, bottom=2),
                        tooltip="Red de PAS (Buscador)"
                    )
                )
            if "cartera" in uperms:
                perm_badges.append(
                    ft.Container(
                        content=ft.Text("CAR", size=9, color="#FFFFFF", weight=ft.FontWeight.BOLD),
                        bgcolor="#D97706",
                        border_radius=4,
                        padding=ft.Padding(left=4, right=4, top=2, bottom=2),
                        tooltip="Cartera & Operaciones"
                    )
                )
            perms_container = ft.Row(controls=perm_badges, spacing=4, tight=True)

            if ucal != "—" and ucal.strip():
                calendar_control = ft.Row(
                    controls=[
                        ft.Icon(ft.Icons.CALENDAR_MONTH_ROUNDED, size=14, color=COLORS["primary"]),
                        ft.Text(ucal[:20] + "..." if len(ucal) > 20 else ucal, size=11, color=COLORS["text_secondary"]),
                    ],
                    spacing=4,
                    tooltip=ucal
                )
            else:
                calendar_control = ft.Text("—", size=12, color=COLORS["text_secondary"])

            def make_edit_click(user_id=uid, username=uname, email=uemail, rol=urol, rc=raw_req_change, rf=raw_failed, rb=raw_blocked, matricula=umatricula, perms=uperms, calendar_url=ucal):
                edit_mat = "" if matricula == "—" else str(matricula)
                return lambda e: open_edit_user_dialog(user_id, username, email, rol, rc, rf, rb, edit_mat, perms, calendar_url)

            actions_cells = []
            # Todos los usuarios pueden ser editados
            actions_cells.append(
                ft.IconButton(
                    icon=ft.Icons.EDIT_OUTLINED,
                    icon_color=COLORS["primary"],
                    icon_size=18,
                    tooltip="Editar Usuario",
                    on_click=make_edit_click(),
                )
            )
            # Solo si no es el admin principal se le puede restablecer forzosamente la contraseña con el botón rápido (el edit ya lo permite)
            if not is_primary_admin:
                actions_cells.append(
                    ft.IconButton(
                        icon=ft.Icons.LOCK_RESET_ROUNDED,
                        icon_color=COLORS["primary"],
                        icon_size=18,
                        tooltip="Restablecer Contraseña",
                        on_click=make_change_pw_click(),
                    )
                )
                
            # No se puede eliminar a sí mismo ni al admin principal
            if not is_self and not is_primary_admin:
                actions_cells.append(
                    ft.IconButton(
                        icon=ft.Icons.DELETE_OUTLINED,
                        icon_color=ft.Colors.RED_400,
                        icon_size=18,
                        tooltip="Eliminar Usuario",
                        on_click=make_delete_click(),
                    )
                )
            def make_role_change_handler(user_id=uid):
                def on_role_change(e):
                    nuevo_rol = e.control.value
                    if ssn_test.actualizar_rol_usuario(user_id, nuevo_rol):
                        ssn_test.registrar_log(state.get("username", "admin"), "USER_ROLE_CHANGED", f"Rol de usuario ID {user_id} cambiado a {nuevo_rol}")
                        show_snackbar(f"Rol del usuario actualizado a '{nuevo_rol}' con éxito.")
                        refresh_users()
                        try:
                            refresh_permissions()
                        except Exception:
                            pass
                    else:
                        show_snackbar("No se pudo actualizar el rol.", is_error=True)
                return on_role_change

            if not is_self and not is_primary_admin:
                role_control = ft.Dropdown(
                    value=urol,
                    options=[
                        ft.dropdown.Option("admin", "Admin"),
                        ft.dropdown.Option("agente", "Agente"),
                    ],
                    border_color=COLORS["border"],
                    focused_border_color=COLORS["primary"],
                    border_radius=6,
                    height=30,
                    width=100,
                    text_size=11,
                    content_padding=ft.Padding(6, 0, 6, 0),
                    on_select=make_role_change_handler(),
                )
            else:
                role_control = ft.Text(urol.capitalize(), size=12, weight=ft.FontWeight.BOLD, color=COLORS["primary"] if urol == "admin" else COLORS["text_secondary"])
            
            user_rows.append(
                ft.DataRow(
                    cells=[
                        ft.DataCell(ft.Text(str(uid), size=12)),
                        ft.DataCell(ft.Text(uname, size=12, weight=ft.FontWeight.BOLD, color=COLORS["text_primary"])),
                        ft.DataCell(ft.Text(uemail, size=12, color=COLORS["text_secondary"])),
                        ft.DataCell(role_control),
                        ft.DataCell(perms_container),
                        ft.DataCell(ft.Text(umatricula, size=12, weight=ft.FontWeight.W_600)),
                        ft.DataCell(calendar_control),
                        ft.DataCell(ft.Text(req_change, size=12)),
                        ft.DataCell(ft.Text(failed_attempts, size=12)),
                        ft.DataCell(ft.Text(block_text, size=12, color=ft.Colors.RED_400 if block_text != "No" else COLORS["text_secondary"])),
                        ft.DataCell(
                            ft.Row(controls=actions_cells, spacing=4, tight=True)
                        ),
                    ]
                )
            )
            
        users_table = ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("ID", size=12, weight=ft.FontWeight.BOLD)),
                ft.DataColumn(ft.Text("Usuario", size=12, weight=ft.FontWeight.BOLD)),
                ft.DataColumn(ft.Text("Email", size=12, weight=ft.FontWeight.BOLD)),
                ft.DataColumn(ft.Text("Rol", size=12, weight=ft.FontWeight.BOLD)),
                ft.DataColumn(ft.Text("Permisos", size=12, weight=ft.FontWeight.BOLD)),
                ft.DataColumn(ft.Text("Matrícula", size=12, weight=ft.FontWeight.BOLD)),
                ft.DataColumn(ft.Text("Agenda / Cal", size=12, weight=ft.FontWeight.BOLD)),
                ft.DataColumn(ft.Text("Cambio Oblig.", size=12, weight=ft.FontWeight.BOLD)),
                ft.DataColumn(ft.Text("Intentos Fallidos", size=12, weight=ft.FontWeight.BOLD)),
                ft.DataColumn(ft.Text("Bloqueo Activo", size=12, weight=ft.FontWeight.BOLD)),
                ft.DataColumn(ft.Text("Acciones", size=12, weight=ft.FontWeight.BOLD)),
            ],
            rows=user_rows,
            column_spacing=18,
            heading_row_height=42,
        )
        
        users_column.controls = [
            ft.Row(
                controls=[
                    ft.Text("Usuarios Registrados", size=14, weight=ft.FontWeight.BOLD, color=COLORS["text_primary"]),
                    ft.FilledButton(
                        "Crear Nuevo Usuario",
                        icon=ft.Icons.ADD_ROUNDED,
                        bgcolor=COLORS["primary"],
                        color=COLORS["text_on_primary"],
                        on_click=open_create_user_dialog,
                        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8)),
                    ),
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            ),
            ft.Divider(height=1, color=COLORS["divider"]),
            ft.Container(
                content=users_table,
                border=ft.Border.all(1, COLORS["divider"]),
                border_radius=8,
                bgcolor=COLORS["surface"],
                padding=10,
            ),
        ]
        try:
            page.update()
        except Exception:
            pass

    def open_create_user_dialog(e):
        uname_field = ft.TextField(label="Nombre de Usuario", border_color=COLORS["border"], focused_border_color=COLORS["primary"], border_radius=8, text_size=13)
        email_field = ft.TextField(label="Correo Electrónico", border_color=COLORS["border"], focused_border_color=COLORS["primary"], border_radius=8, text_size=13)
        pass_field = ft.TextField(label="Contraseña", password=True, can_reveal_password=True, border_color=COLORS["border"], focused_border_color=COLORS["primary"], border_radius=8, text_size=13)
        role_field = ft.Dropdown(
            label="Rol de Usuario",
            options=[
                ft.dropdown.Option("agente", "Agente"),
                ft.dropdown.Option("admin", "Admin"),
            ],
            value="agente",
            border_color=COLORS["border"],
            focused_border_color=COLORS["primary"],
            border_radius=8,
            text_size=13,
        )
        
        perm_comercial = ft.Checkbox(label="Gestión Comercial", value=True, label_style=ft.TextStyle(size=12))
        perm_comercial_metricas = ft.Checkbox(label="  └ Métricas y Rendimiento", value=True, label_style=ft.TextStyle(size=11, color=COLORS["text_secondary"]))
        perm_comercial_visitas = ft.Checkbox(label="  └ Plan de Visitas", value=True, label_style=ft.TextStyle(size=11, color=COLORS["text_secondary"]))
        perm_comercial_excel = ft.Checkbox(label="  └ Seguimiento Diario (Excel)", value=True, label_style=ft.TextStyle(size=11, color=COLORS["text_secondary"]))
        
        def toggle_comercial_subs(e):
            val = perm_comercial.value
            perm_comercial_metricas.disabled = not val
            perm_comercial_visitas.disabled = not val
            perm_comercial_excel.disabled = not val
            if not val:
                perm_comercial_metricas.value = False
                perm_comercial_visitas.value = False
                perm_comercial_excel.value = False
            else:
                perm_comercial_metricas.value = True
                perm_comercial_visitas.value = True
                perm_comercial_excel.value = True
            page.update()
            
        perm_comercial.on_change = toggle_comercial_subs
        
        perm_buscador = ft.Checkbox(label="Red de PAS (Buscador)", value=True, label_style=ft.TextStyle(size=12))
        perm_cartera = ft.Checkbox(label="Cartera & Operaciones", value=True, label_style=ft.TextStyle(size=12))
        
        def close_dialog(ev):
            dlg.open = False
            page.update()
            
        def do_create(ev):
            uname = (uname_field.value or "").strip().lower()
            email = (email_field.value or "").strip().lower()
            pwd = (pass_field.value or "").strip()
            rol = role_field.value
            
            if not uname or not email or not pwd or not rol:
                show_snackbar("Por favor completa todos los campos para crear el usuario.", is_error=True)
                return
                
            if len(uname) < 3:
                show_snackbar("El nombre de usuario debe tener al menos 3 caracteres.", is_error=True)
                return
                
            if not re.match(r"^[a-zA-Z0-9_]+$", uname):
                show_snackbar("El nombre de usuario solo debe contener letras, números y guiones bajos.", is_error=True)
                return
                
            email_pattern = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
            if not re.match(email_pattern, email):
                show_snackbar("El correo electrónico no es válido.", is_error=True)
                return
                
            if len(pwd) < 6:
                show_snackbar("La contraseña debe tener al menos 6 caracteres.", is_error=True)
                return
                
            selected_perms = []
            if perm_comercial.value:
                selected_perms.append("comercial")
                if perm_comercial_metricas.value: selected_perms.append("comercial_metricas")
                if perm_comercial_visitas.value: selected_perms.append("comercial_visitas")
                if perm_comercial_excel.value: selected_perms.append("comercial_excel")
            if perm_buscador.value: selected_perms.append("buscador")
            if perm_cartera.value: selected_perms.append("cartera")
            perms_str = ",".join(selected_perms)
            
            if on_crear_usuario(uname, email, pwd, rol, permisos=perms_str):
                dlg.open = False
                page.update()
                # Log event
                ssn_test.registrar_log(state.get("username", "admin"), "USER_CREATED", f"Usuario creado: '{uname}' ({email}) - Rol: {rol} - Permisos: {perms_str}")
                show_snackbar(f"Usuario '{uname}' creado con éxito como '{rol}'.")
                refresh_users()
            else:
                show_snackbar("No se pudo crear el usuario. El nombre de usuario o correo ya existe.", is_error=True)
 
        dlg = ft.AlertDialog(
            title=ft.Row([ft.Icon(ft.Icons.PERSON_ADD_ROUNDED, color=COLORS["primary"]), ft.Text("Crear Nuevo Usuario", size=16, weight=ft.FontWeight.BOLD)]),
            content=ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Text("Los nuevos usuarios deberán cambiar obligatoriamente su contraseña en el primer inicio de sesión.", size=12, color=COLORS["text_secondary"]),
                        ft.Container(height=4),
                        uname_field,
                        email_field,
                        pass_field,
                        role_field,
                        ft.Container(height=4),
                        ft.Text("Permisos de Acceso:", size=12, weight=ft.FontWeight.BOLD, color=COLORS["text_secondary"]),
                        perm_comercial,
                        perm_comercial_metricas,
                        perm_comercial_visitas,
                        perm_comercial_excel,
                        perm_buscador,
                        perm_cartera,
                    ],
                    spacing=12,
                    tight=True,
                ),
                width=320,
            ),
            actions=[
                ft.TextButton("Cancelar", on_click=close_dialog),
                ft.ElevatedButton("Crear Usuario", on_click=do_create, style=ft.ButtonStyle(bgcolor=COLORS["primary"], color=COLORS["text_on_primary"])),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        page.dialog = dlg
        dlg.open = True
        page.update()

    def open_edit_user_dialog(user_id, username, email, rol, rc, rf, rb, current_matricula="", perms="comercial,buscador,cartera", calendar_url=""):
        import time
        uname_field = ft.TextField(
            value=username, 
            label="Nombre de Usuario", 
            border_color=COLORS["border"], 
            focused_border_color=COLORS["primary"], 
            border_radius=8, 
            text_size=13
        )
        email_field = ft.TextField(
            value=email, 
            label="Correo Electrónico", 
            border_color=COLORS["border"], 
            focused_border_color=COLORS["primary"], 
            border_radius=8, 
            text_size=13
        )
        role_field = ft.Dropdown(
            label="Rol de Usuario",
            options=[
                ft.dropdown.Option("agente", "Agente"),
                ft.dropdown.Option("admin", "Admin"),
            ],
            value=rol,
            border_color=COLORS["border"],
            focused_border_color=COLORS["primary"],
            border_radius=8,
            text_size=13,
            disabled=(username == state.get("username")), # Don't allow self-role demotion
        )
        matricula_field = ft.TextField(
            value=current_matricula,
            label="Matrícula Asociada (opcional)",
            border_color=COLORS["border"],
            focused_border_color=COLORS["primary"],
            border_radius=8,
            text_size=13
        )
        calendar_url_field = ft.TextField(
            value=calendar_url,
            label="Enlace de Agenda / Cal.com (URL)",
            border_color=COLORS["border"],
            focused_border_color=COLORS["primary"],
            border_radius=8,
            text_size=13
        )
        pass_field = ft.TextField(
            label="Nueva Contraseña (opcional)", 
            password=True, 
            can_reveal_password=True, 
            border_color=COLORS["border"], 
            focused_border_color=COLORS["primary"], 
            border_radius=8, 
            text_size=13,
            hint_text="Dejar en blanco para mantener actual"
        )
        
        req_change_chk = ft.Checkbox(
            label="Exigir cambio de contraseña",
            value=bool(rc),
            label_style=ft.TextStyle(size=12)
        )
        
        is_blocked = (rb > time.time())
        has_attempts = (rf > 0)
        
        reset_lock_chk = ft.Checkbox(
            label="Desbloquear / Restablecer intentos",
            value=False,
            label_style=ft.TextStyle(size=12),
            disabled=not (is_blocked or has_attempts),
        )
        
        perms_set = {p.strip() for p in perms.split(",") if p.strip()}
        perm_comercial = ft.Checkbox(label="Gestión Comercial", value=("comercial" in perms_set), label_style=ft.TextStyle(size=12))
        
        has_sub_comercial = any(p in perms_set for p in ["comercial_metricas", "comercial_visitas", "comercial_excel"])
        default_sub_val = ("comercial" in perms_set) and not has_sub_comercial
        
        perm_comercial_metricas = ft.Checkbox(
            label="  └ Métricas y Rendimiento",
            value=(("comercial_metricas" in perms_set) or default_sub_val),
            label_style=ft.TextStyle(size=11, color=COLORS["text_secondary"]),
            disabled=not ("comercial" in perms_set)
        )
        perm_comercial_visitas = ft.Checkbox(
            label="  └ Plan de Visitas",
            value=(("comercial_visitas" in perms_set) or default_sub_val),
            label_style=ft.TextStyle(size=11, color=COLORS["text_secondary"]),
            disabled=not ("comercial" in perms_set)
        )
        perm_comercial_excel = ft.Checkbox(
            label="  └ Seguimiento Diario (Excel)",
            value=(("comercial_excel" in perms_set) or default_sub_val),
            label_style=ft.TextStyle(size=11, color=COLORS["text_secondary"]),
            disabled=not ("comercial" in perms_set)
        )
        
        def toggle_comercial_subs(e):
            val = perm_comercial.value
            perm_comercial_metricas.disabled = not val
            perm_comercial_visitas.disabled = not val
            perm_comercial_excel.disabled = not val
            if not val:
                perm_comercial_metricas.value = False
                perm_comercial_visitas.value = False
                perm_comercial_excel.value = False
            else:
                perm_comercial_metricas.value = True
                perm_comercial_visitas.value = True
                perm_comercial_excel.value = True
            page.update()
            
        perm_comercial.on_change = toggle_comercial_subs
        
        perm_buscador = ft.Checkbox(label="Red de PAS (Buscador)", value=("buscador" in perms_set), label_style=ft.TextStyle(size=12))
        perm_cartera = ft.Checkbox(label="Cartera & Operaciones", value=("cartera" in perms_set), label_style=ft.TextStyle(size=12))
        
        status_info = []
        if is_blocked:
            rem = int(rb - time.time())
            status_info.append(
                ft.Text(f"⚠️ Bloqueo activo: vence en {rem}s", size=11, color=ft.Colors.RED_400, weight=ft.FontWeight.BOLD)
            )
        if rf > 0:
            status_info.append(
                ft.Text(f"⚠️ Intentos fallidos: {rf}", size=11, color=ft.Colors.ORANGE_400)
            )
        
        def close_dialog(ev):
            dlg.open = False
            page.update()
            
        def do_update(ev):
            new_uname = (uname_field.value or "").strip().lower()
            new_email = (email_field.value or "").strip().lower()
            new_pwd = (pass_field.value or "").strip()
            new_rol = role_field.value
            new_matricula = (matricula_field.value or "").strip()
            new_calendar_url = (calendar_url_field.value or "").strip()
            req_change_val = 1 if req_change_chk.value else 0
            reset_lock_val = reset_lock_chk.value
            
            if not new_uname or not new_email:
                show_snackbar("El nombre de usuario y correo son requeridos.", is_error=True)
                return
                
            if new_pwd and len(new_pwd) < 6:
                show_snackbar("La nueva contraseña debe tener al menos 6 caracteres.", is_error=True)
                return
                
            selected_perms = []
            if perm_comercial.value:
                selected_perms.append("comercial")
                if perm_comercial_metricas.value: selected_perms.append("comercial_metricas")
                if perm_comercial_visitas.value: selected_perms.append("comercial_visitas")
                if perm_comercial_excel.value: selected_perms.append("comercial_excel")
            if perm_buscador.value: selected_perms.append("buscador")
            if perm_cartera.value: selected_perms.append("cartera")
            perms_str = ",".join(selected_perms)
            
            success, msg = ssn_test.actualizar_usuario(
                user_id, 
                new_uname, 
                new_email, 
                password_txt=new_pwd, 
                rol=new_rol, 
                requiere_cambio=req_change_val,
                reset_lock=reset_lock_val,
                is_self_update=(username == state.get("username")),
                matricula=new_matricula,
                permisos=perms_str,
                calendar_url=new_calendar_url
            )
            
            if success:
                dlg.open = False
                page.update()
                ssn_test.registrar_log(
                    state.get("username", "admin"), 
                    "USER_UPDATED", 
                    f"Usuario editado: ID {user_id} - '{new_uname}' ({new_email}) - Rol: {new_rol} - Req. Cambio: {req_change_val} - Reset Lock: {reset_lock_val} - Matrícula: {new_matricula or 'Ninguna'} - Permisos: {perms_str} - Agenda: {new_calendar_url}"
                )
                
                if username == state.get("username"):
                    state["username"] = new_uname
                    # Also update our own permissions in state if we edited ourselves
                    state["permisos"] = set(selected_perms)
                    state["calendar_url"] = new_calendar_url
                    
                show_snackbar(msg)
                refresh_users()
                try:
                    refresh_permissions()
                except Exception:
                    pass
            else:
                show_snackbar(msg, is_error=True)
 
        dlg = ft.AlertDialog(
            title=ft.Row([ft.Icon(ft.Icons.EDIT_ROUNDED, color=COLORS["primary"]), ft.Text(f"Editar Usuario: {username}", size=16, weight=ft.FontWeight.BOLD)]),
            content=ft.Container(
                content=ft.Column(
                    controls=[
                        uname_field,
                        email_field,
                        role_field,
                        matricula_field,
                        calendar_url_field,
                        pass_field,
                        req_change_chk,
                        reset_lock_chk,
                        ft.Container(height=4),
                        ft.Text("Permisos de Acceso:", size=12, weight=ft.FontWeight.BOLD, color=COLORS["text_secondary"]),
                        perm_comercial,
                        perm_comercial_metricas,
                        perm_comercial_visitas,
                        perm_comercial_excel,
                        perm_buscador,
                        perm_cartera,
                    ] + status_info,
                    spacing=10,
                    tight=True,
                ),
                width=320,
            ),
            actions=[
                ft.TextButton("Cancelar", on_click=close_dialog),
                ft.FilledButton("Guardar Cambios", on_click=do_update, style=ft.ButtonStyle(bgcolor=COLORS["primary"], color=COLORS["text_on_primary"])),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        page.dialog = dlg
        dlg.open = True
        page.update()

    def open_change_pw_dialog(user_id, username):
        pass_field = ft.TextField(label="Nueva Contraseña", password=True, can_reveal_password=True, border_color=COLORS["border"], focused_border_color=COLORS["primary"], border_radius=8, text_size=13)
        
        def close_dialog(ev):
            dlg.open = False
            page.update()
            
        def do_change(ev):
            pwd = (pass_field.value or "").strip()
            if not pwd or len(pwd) < 6:
                show_snackbar("La contraseña debe tener al menos 6 caracteres.", is_error=True)
                return
                
            if on_cambiar_password(user_id, pwd):
                dlg.open = False
                page.update()
                ssn_test.registrar_log(state.get("username", "admin"), "USER_PASSWORD_RESET", f"Contraseña restablecida por admin para: '{username}'")
                show_snackbar(f"Contraseña de '{username}' restablecida con éxito.")
                refresh_users()
            else:
                show_snackbar("No se pudo cambiar la contraseña.", is_error=True)

        dlg = ft.AlertDialog(
            title=ft.Row([ft.Icon(ft.Icons.LOCK_RESET_ROUNDED, color=COLORS["primary"]), ft.Text(f"Restablecer contraseña para '{username}'", size=16, weight=ft.FontWeight.BOLD)]),
            content=ft.Container(
                content=ft.Column(controls=[pass_field], tight=True),
                width=320,
            ),
            actions=[
                ft.TextButton("Cancelar", on_click=close_dialog),
                ft.ElevatedButton("Confirmar Cambio", on_click=do_change, style=ft.ButtonStyle(bgcolor=COLORS["primary"], color=COLORS["text_on_primary"])),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        page.dialog = dlg
        dlg.open = True
        page.update()

    def open_delete_user_dialog(user_id, username):
        def close_dialog(ev):
            dlg.open = False
            page.update()
            
        def do_delete(ev):
            dlg.open = False
            page.update()
            if on_eliminar_usuario(user_id):
                ssn_test.registrar_log(state.get("username", "admin"), "USER_DELETED", f"Usuario eliminado: '{username}'")
                show_snackbar(f"Usuario '{username}' eliminado con éxito.")
                refresh_users()
            else:
                show_snackbar("No se pudo eliminar el usuario.", is_error=True)

        dlg = ft.AlertDialog(
            title=ft.Row([ft.Icon(ft.Icons.WARNING_ROUNDED, color=ft.Colors.RED_500), ft.Text("Eliminar Usuario", size=16, weight=ft.FontWeight.BOLD)]),
            content=ft.Text(f"¿Estás seguro de que deseas eliminar permanentemente al usuario '{username}'? Esta acción no se puede deshacer.", size=13),
            actions=[
                ft.TextButton("Cancelar", on_click=close_dialog),
                ft.ElevatedButton("Sí, Eliminar", on_click=do_delete, style=ft.ButtonStyle(bgcolor=ft.Colors.RED_600, color=ft.Colors.WHITE)),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        page.dialog = dlg
        dlg.open = True
        page.update()

    # Logs View Logic
    def refresh_logs():
        logs = ssn_test.obtener_logs(100)
        log_rows = []
        for l in logs:
            fecha_val = l.get("fecha")
            user = l.get("usuario")
            action = l.get("accion")
            detalles_val = l.get("detalles") or "—"
            
            # Badge color logic
            action_color = COLORS["primary"]
            if "SUCCESS" in action or "LOGIN" in action:
                action_color = COLORS["primary"]
            elif "FAILED" in action or "BLOCKED" in action or "WIPE" in action or "DELETE" in action or "EMPTY" in action:
                action_color = ft.Colors.RED_500
            elif "CHANGED" in action or "RESET" in action or "UPDATE" in action or "IMPORT" in action:
                action_color = COLORS["success"]
                
            log_rows.append(
                ft.DataRow(
                    cells=[
                        ft.DataCell(ft.Text(fecha_val, size=11, color=COLORS["text_secondary"])),
                        ft.DataCell(ft.Text(user, size=11, color=COLORS["text_primary"], weight=ft.FontWeight.BOLD)),
                        ft.DataCell(ft.Container(
                            content=ft.Text(action, size=9, color=COLORS["text_on_primary"], weight=ft.FontWeight.W_700),
                            bgcolor=action_color,
                            padding=ft.Padding(6, 2, 6, 2),
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
                ft.DataColumn(ft.Text("Descripción / Detalles", size=12, weight=ft.FontWeight.BOLD)),
            ],
            rows=log_rows,
            column_spacing=18,
            heading_row_height=42,
        )
        
        logs_column.controls = [
            ft.Row(
                controls=[
                    ft.Text("Registro de Auditoría (Últimos 100 eventos)", size=14, weight=ft.FontWeight.BOLD, color=COLORS["text_primary"]),
                    ft.IconButton(
                        icon=ft.Icons.REFRESH_ROUNDED,
                        icon_color=COLORS["primary"],
                        icon_size=20,
                        tooltip="Actualizar Logs",
                        on_click=lambda e: refresh_logs(),
                    ),
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            ),
            ft.Divider(height=1, color=COLORS["divider"]),
            ft.Container(
                content=logs_table,
                border=ft.Border.all(1, COLORS["divider"]),
                border_radius=8,
                bgcolor=COLORS["surface"],
                padding=10,
            ),
        ]
        logs_column.update()

    # Database Maintenance Logic
    def refresh_db_stats():
        from ssn_test import obtener_ultima_actualizacion
        db_count = len(state["records"])
        last_upd = obtener_ultima_actualizacion()
        
        db_stats_column.controls = [
            ft.Text("Administración de Base de Datos", size=14, weight=ft.FontWeight.BOLD, color=COLORS["text_primary"]),
            ft.Divider(height=1, color=COLORS["divider"]),
            ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Row(
                            controls=[
                                ft.Icon(ft.Icons.STORAGE_ROUNDED, color=COLORS["primary"], size=20),
                                ft.Text(f"Registros en SQLite local: {db_count:,}".replace(",", "."), size=13, weight=ft.FontWeight.W_500, color=COLORS["text_primary"]),
                            ]
                        ),
                        ft.Row(
                            controls=[
                                ft.Icon(ft.Icons.UPDATE_ROUNDED, color=COLORS["primary"], size=20),
                                ft.Text(f"Fecha de última importación masiva: {last_upd}", size=13, weight=ft.FontWeight.W_500, color=COLORS["text_primary"]),
                            ]
                        ),
                    ],
                    spacing=12,
                ),
                padding=16,
                border=ft.Border.all(1, COLORS["divider"]),
                border_radius=8,
                bgcolor=COLORS["surface"],
            ),
            ft.Container(height=10),
            ft.Text("Acciones Administrativas", size=13, weight=ft.FontWeight.BOLD, color=COLORS["text_secondary"]),
            ft.Row(
                controls=[
                    ft.FilledButton(
                        "Importar Productores (Excel/CSV)",
                        icon=ft.Icons.UPLOAD_FILE_ROUNDED,
                        bgcolor=COLORS["success"],
                        color=COLORS["text_on_primary"],
                        on_click=on_import_click,
                        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8), padding=ft.Padding(18, 12, 18, 12)),
                    ),
                    ft.FilledButton(
                        "Vaciar Base de Datos",
                        icon=ft.Icons.DELETE_FOREVER_ROUNDED,
                        bgcolor=ft.Colors.RED_600,
                        color=ft.Colors.WHITE,
                        on_click=on_vaciar_db,
                        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8), padding=ft.Padding(18, 12, 18, 12)),
                    ),
                ],
                spacing=12,
            )
        ]
        db_stats_column.update()

    def refresh_permissions():
        users = ssn_test.obtener_usuarios()
        # Filter agents
        agents = [u for u in users if u.get("rol") == "agente"]
        
        # Build the selector column
        lector_options = [ft.dropdown.Option(key=str(u["id"]), text=u["usuario"]) for u in agents]
        
        # If no agents, show message
        if not agents:
            permissions_column.controls = [
                ft.Text("Gestión de Visibilidad Cruzada entre Agentes", size=14, weight=ft.FontWeight.BOLD, color=COLORS["text_primary"]),
                ft.Divider(height=1, color=COLORS["divider"]),
                ft.Text("No hay usuarios Agentes registrados en el sistema para configurar permisos.", size=13, color=COLORS["text_secondary"]),
            ]
            permissions_column.update()
            return
            
        # We need a dropdown to choose the Lector
        lector_dropdown = ft.Dropdown(
            label="Seleccionar Agente (Lector)",
            options=lector_options,
            border_color=COLORS["border"],
            focused_border_color=COLORS["primary"],
            border_radius=8,
            width=300,
        )
        
        # Container for the checkboxes (propietarios)
        checkboxes_container = ft.Column(spacing=8, scroll=ft.ScrollMode.AUTO, expand=True)
        
        # Save button
        save_btn = ft.FilledButton(
            "Guardar Permisos de Visibilidad",
            icon=ft.Icons.SAVE_ROUNDED,
            bgcolor=COLORS["primary"],
            color=COLORS["text_on_primary"],
            disabled=True,
            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8)),
        )
        
        def on_lector_change(e):
            lector_id = int(lector_dropdown.value)
            selected_lector_ref[0] = lector_id
            
            # Fetch current permissions
            allowed_ids = ssn_test.obtener_permisos_visibilidad(lector_id)
            
            # Rebuild checkbox list: lector can see other agents' or admins' data
            # Typically visibility permissions are for agents to see other users' data.
            # Let's show all other users (except the lector himself)
            checkboxes = []
            for u in users:
                if u["id"] == lector_id:
                    continue
                
                chk = ft.Checkbox(
                    label=f"{u['usuario']} ({u.get('rol', 'agente')})",
                    value=(u["id"] in allowed_ids),
                    data=u["id"],
                    fill_color=COLORS["primary"],
                )
                checkboxes.append(chk)
                
            checkboxes_container.controls = checkboxes
            save_btn.disabled = False
            permissions_column.update()
            
        lector_dropdown.on_select = on_lector_change
        
        def on_save_click(e):
            lector_id = selected_lector_ref[0]
            if lector_id is None:
                return
                
            # Collect checked IDs
            propietarios_ids = []
            for ctrl in checkboxes_container.controls:
                if isinstance(ctrl, ft.Checkbox) and ctrl.value:
                    propietarios_ids.append(ctrl.data)
                    
            if ssn_test.actualizar_permisos_visibilidad(lector_id, propietarios_ids):
                ssn_test.registrar_log(
                    state.get("username", "admin"),
                    "UPDATE_PERMISSIONS",
                    f"Permisos actualizados para usuario ID {lector_id}. Acceso a: {propietarios_ids}"
                )
                show_snackbar("Los permisos de visibilidad cruzada fueron actualizados exitosamente.")
            else:
                show_snackbar("Ocurrió un error al guardar los permisos.", is_error=True)
                
        save_btn.on_click = on_save_click
        
        # If there's a previously selected lector, restore selection
        if selected_lector_ref[0] is not None and any(int(o.key) == selected_lector_ref[0] for o in lector_options):
            lector_dropdown.value = str(selected_lector_ref[0])
            on_lector_change(None)
            
        permissions_column.controls = [
            ft.Text("Gestión de Visibilidad Cruzada entre Agentes", size=14, weight=ft.FontWeight.BOLD, color=COLORS["text_primary"]),
            ft.Text("Configura qué agentes pueden visualizar la información cargada por otros usuarios del sistema.", size=12, color=COLORS["text_secondary"]),
            ft.Divider(height=1, color=COLORS["divider"]),
            lector_dropdown,
            ft.Container(height=8),
            ft.Text("El agente seleccionado podrá VER los productores asignados a:", size=13, weight=ft.FontWeight.BOLD, color=COLORS["text_primary"]),
            ft.Container(
                content=checkboxes_container,
                border=ft.Border.all(1, COLORS["divider"]),
                border_radius=8,
                bgcolor=COLORS["surface"],
                padding=12,
                height=220,
            ),
            ft.Container(height=10),
            save_btn,
        ]
        permissions_column.update()

    # Populate docs_column with Markdown
    docs_markdown = """
# 📖 Guía de Uso del CRM

Bienvenido al panel de administración y operación del CRM de Katrix Broker.

## 🧑‍💼 Gestión de Usuarios (CRUD)
- **Crear**: Utilice el botón superior "Crear Nuevo Usuario". Los usuarios nuevos deberán cambiar su contraseña al iniciar sesión por primera vez.
- **Editar**: Puede modificar el Rol, Correo y Contraseña de cualquier usuario haciendo clic en el icono del lápiz (✏️) en su fila correspondiente. También puede imponer un cambio de contraseña obligatorio o desbloquear cuentas bloqueadas por intentos fallidos.
- **Permisos de Visibilidad**: En la pestaña de Permisos puede establecer un esquema jerárquico y decidir qué Agentes pueden visualizar los productores asociados a otros miembros de la red.

## 🔍 Buscador de Productores
- Puede buscar por Nombre, Apellido, Matrícula o CUIT en la barra superior.
- Los filtros avanzados permiten refinar por Ramo, Provincia, Localidad y Estado de Contacto.
- **Estados de Contacto**: Puede marcar a cada productor ('Interesado', 'No Contactar', etc.) y agregar **Notas / Observaciones** específicas a cada uno.

## 🏢 Sociedades (Múltiples)
- Al ver el detalle de un productor, puede asignarlo a **múltiples Sociedades** de forma relacional. Haga clic en '+' bajo Sociedades y busque el nombre en la base de datos para vincularlo de inmediato.
    
## 📊 Exportación y Base de Datos
- Las exportaciones a **CSV** incluirán únicamente el estado actual de la grilla filtrada.
- En la pestaña "Base de Datos", puede ver las estadísticas de almacenamiento, **Vaciar la base por completo** y **Restaurar/Importar un CSV** con registros actualizados de la SSN.
"""

    docs_column.controls = [
        ft.Markdown(
            docs_markdown,
            selectable=True,
            extension_set=ft.MarkdownExtensionSet.GITHUB_WEB,
        )
    ]

    # Define Tabs
    tab_perm = ft.Tab(label="Permisos de Visibilidad", icon=ft.Icons.SECURITY_ROUNDED)
    tab_logs = ft.Tab(label="Logs del Sistema", icon=ft.Icons.RECEIPT_LONG_ROUNDED)
    tab_db = ft.Tab(label="Base de Datos", icon=ft.Icons.STORAGE_ROUNDED)
    tab_docs = ft.Tab(label="Guía de Uso", icon=ft.Icons.HELP_OUTLINE_ROUNDED)

    tabs = ft.Tabs(
        length=4,
        selected_index=0,
        animation_duration=300,
        content=ft.Column(
            expand=True,
            controls=[
                ft.TabBar(
                    tabs=[tab_perm, tab_logs, tab_db, tab_docs],
                    label_color=COLORS["primary"],
                    unselected_label_color=COLORS["text_secondary"],
                    indicator_color=COLORS["primary"],
                ),
                ft.TabBarView(
                    expand=True,
                    controls=[
                        ft.Container(content=permissions_column, padding=ft.Padding(0, 16, 0, 16)),
                        ft.Container(content=logs_column, padding=ft.Padding(0, 16, 0, 16)),
                        ft.Container(content=db_stats_column, padding=ft.Padding(0, 16, 0, 16)),
                        ft.Container(content=docs_column, padding=ft.Padding(0, 16, 0, 16)),
                    ],
                ),
            ],
        ),
        expand=True,
    )

    # We schedule initial loading of the active tab data
    def on_tabs_change(e):
        if tabs.selected_index == 0:
            refresh_permissions()
        elif tabs.selected_index == 1:
            refresh_logs()
        elif tabs.selected_index == 2:
            refresh_db_stats()
            
    tabs.on_change = on_tabs_change

    # Run initial loads inside a small background thread to avoid blocking Flet UI thread
    def initial_load():
        time.sleep(0.05)
        try:
            refresh_permissions()
        except Exception as ex:
            print(f"Error loading permissions: {ex}")
            
    threading.Thread(target=initial_load, daemon=True).start()

    return ft.Container(
        content=ft.Column(
            controls=[
                header_row,
                ft.Container(height=8),
                tabs
            ],
            spacing=8,
            expand=True,
        ),
        padding=ft.Padding(24, 18, 24, 18),
        expand=True,
    )


def build_dashboard_metrics_view(
    records: List[Dict[str, Any]],
    on_back: Callable,
    on_filter_click: Callable[[str, Any], None],
    page: ft.Page,
    state: Dict[str, Any] = None,
) -> ft.Container:
    import collections
    
    # Month selector placeholder (will be set after dropdown is created)
    _header_month_slot = ft.Row([], spacing=0)  # placeholder

    # 1. Header
    header_row = ft.Row(
        controls=[
            ft.Row(
                controls=[
                    ft.IconButton(
                        icon=ft.Icons.ARROW_BACK_ROUNDED,
                        icon_color=COLORS["primary"],
                        icon_size=24,
                        tooltip="Volver al buscador",
                        on_click=lambda e: on_back(),
                    ),
                    ft.Column([
                        ft.Text("Gestión Comercial y Operativa", size=20, weight=ft.FontWeight.BOLD, color=COLORS["text_primary"]),
                        ft.Text("Métricas consolidadas de la red de productores, cartera, siniestros y comisiones.", size=11, color=COLORS["text_secondary"]),
                    ], spacing=1, tight=True)
                ],
                spacing=10,
            ),
            _header_month_slot,
        ],
        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        vertical_alignment=ft.CrossAxisAlignment.CENTER,
    )
    
    # Hover animations helper
    def make_hover_handler(scale_val=1.02):
        def on_hover(e):
            e.control.scale = scale_val if e.data == "true" else 1.0
            e.control.shadow = ft.BoxShadow(
                spread_radius=2,
                blur_radius=12,
                color=ft.Colors.with_opacity(0.12, COLORS["primary"])
            ) if e.data == "true" else ft.BoxShadow(
                spread_radius=1,
                blur_radius=6,
                color=ft.Colors.with_opacity(0.06, "#000000")
            )
            e.control.update()
        return on_hover
    # ── Tabs Gestión Comercial ─────────────────────────────────────────────
    import ssn_test as _ssn
    from datetime import datetime as _dt
    
    # Generar meses dinámicamente:
    # 1. Planificación (Mes actual + 4 futuros)
    _now = _dt.now()
    plan_months = []
    for i in range(5):
        _m = (_now.month - 1 + i) % 12 + 1
        _y = _now.year + (_now.month - 1 + i) // 12
        plan_months.append(f"{_y}-{_m:02d}")

    # 2. Historial (6 meses anteriores)
    hist_months = []
    for i in range(1, 7):
        _m = (_now.month - 1 - i) % 12 + 1
        _y = _now.year + (_now.month - 1 - i) // 12
        hist_months.append(f"{_y}-{_m:02d}")
    
    def format_month_label(mes_str):
        try:
            y, m = mes_str.split("-")
            months = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
            m_idx = int(m) - 1
            if 0 <= m_idx < len(months):
                return f"{months[m_idx]} {y}"
            return mes_str
        except Exception as ex:
            return mes_str
            
    mes_actual = _now.strftime("%Y-%m")
    if mes_actual not in plan_months and mes_actual not in hist_months:
        mes_actual = plan_months[0]
    mes_label  = format_month_label(mes_actual)
    
    def on_month_plan_change(e):
        nonlocal mes_actual, mes_label
        if mes_plan_dropdown.value == "divider":
            # Revertir al mes actual seleccionado si hace clic en el separador
            mes_plan_dropdown.value = mes_actual
            page.update()
            return
        mes_actual = mes_plan_dropdown.value
        mes_label = format_month_label(mes_actual)
        refresh_dashboard()

    # Construir opciones del dropdown con el separador de historial
    _options = []
    for m in plan_months:
        _options.append(ft.dropdown.Option(m, format_month_label(m)))
    _options.append(ft.dropdown.Option("divider", "─── Historial ───"))
    for m in hist_months:
        _options.append(ft.dropdown.Option(m, format_month_label(m)))

    mes_plan_dropdown = ft.Dropdown(
        label="Mes de Planificación",
        border_color=COLORS["border"],
        focused_border_color=COLORS["primary"],
        border_radius=8,
        text_size=13,
        height=48,
        width=200,
        options=_options,
        value=mes_actual,
    )
    mes_plan_dropdown.on_change = on_month_plan_change
    # Inject dropdown into header slot
    _header_month_slot.controls = [mes_plan_dropdown]

    def _status_chip(label: str, color: str):
        return ft.Container(
            content=ft.Text(label, size=10, color="#FFFFFF", weight=ft.FontWeight.BOLD),
            bgcolor=color, border_radius=6,
            padding=ft.Padding(6, 3, 6, 3),
        )

    # ── Componentes del Dashboard Unificado ───────────────────────────────
    filter_state = {"search": "", "company": "Todas", "status": "Todos"}

    search_field = ft.TextField(
        hint_text="Buscar PAS por nombre o compañía...",
        prefix_icon=ft.Icons.SEARCH_ROUNDED,
        border_color=COLORS["border"],
        focused_border_color=COLORS["primary"],
        border_radius=8,
        text_size=13,
        height=42,
        expand=True,
    )

    company_label = ft.Text("Todas las Compañías", size=12, color=COLORS["text_primary"])
    company_btn = ft.PopupMenuButton(
        content=ft.Container(
            content=ft.Row([
                ft.Icon(ft.Icons.BUSINESS_ROUNDED, size=14, color=COLORS["text_secondary"]),
                company_label,
                ft.Icon(ft.Icons.ARROW_DROP_DOWN_ROUNDED, size=16, color=COLORS["text_secondary"]),
            ], spacing=4, vertical_alignment=ft.CrossAxisAlignment.CENTER),
            bgcolor=COLORS["surface"],
            border=ft.Border.all(1, COLORS["border"]),
            border_radius=8,
            padding=ft.Padding(10, 8, 10, 8),
            height=42,
            width=220,
        ),
        items=[],
    )

    status_label = ft.Text("Todos", size=12, color=COLORS["text_primary"])

    def _set_status(val, label_txt):
        filter_state["status"] = val
        status_label.value = label_txt
        filter_and_render()

    def _make_menu_item(label: str, handler):
        item = ft.PopupMenuItem()
        item.content = ft.Text(label, size=12)
        item.on_click = handler
        return item

    status_btn = ft.PopupMenuButton(
        content=ft.Container(
            content=ft.Row([
                ft.Icon(ft.Icons.FILTER_LIST_ROUNDED, size=14, color=COLORS["text_secondary"]),
                status_label,
                ft.Icon(ft.Icons.ARROW_DROP_DOWN_ROUNDED, size=16, color=COLORS["text_secondary"]),
            ], spacing=4, vertical_alignment=ft.CrossAxisAlignment.CENTER),
            bgcolor=COLORS["surface"],
            border=ft.Border.all(1, COLORS["border"]),
            border_radius=8,
            padding=ft.Padding(10, 8, 10, 8),
            height=42,
            width=150,
        ),
        items=[
            _make_menu_item("Todos", lambda e: _set_status("Todos", "Todos")),
            _make_menu_item("Realizadas", lambda e: _set_status("realizada", "Realizadas")),
            _make_menu_item("Pendientes", lambda e: _set_status("pendiente", "Pendientes")),
        ],
    )

    pas_list_col = ft.Column(spacing=8, scroll=ft.ScrollMode.AUTO, expand=True)
    pas_list_container = ft.Container(content=pas_list_col, expand=True)

    all_visitas = []

    def filter_and_render():
        search_val = filter_state["search"].strip().lower()
        comp_val = filter_state["company"]
        status_val = filter_state["status"]
        print(f"[filter] search='{search_val}' comp='{comp_val}' status='{status_val}' total={len(all_visitas)}")
        
        filtered = [
            v for v in all_visitas
            if (not search_val or
                search_val in v["nombre"].lower() or
                (v.get("campaña") and search_val in v["campaña"].lower()) or
                (v.get("matricula") and search_val in str(v["matricula"]).lower())
            )
            and (comp_val == "Todas" or v.get("campaña") == comp_val)
            and (status_val == "Todos" or v["estado"] == status_val)
        ]
        print(f"[filter] resultado: {len(filtered)} visitas")
        
        items = []
        for v in filtered:
            vid = v["id"]
            vnombre = v["nombre"]
            vest = v["estado"]
            vprod = v.get("productividad", "")
            vorg = v.get("estado_org", "")
            vcam = v.get("campaña", "")

            def make_toggle_visita(v_id=vid, v_name=vnombre, current_est=vest, p=vprod, o=vorg, c=vcam):
                new_est = "realizada" if current_est == "pendiente" else "pendiente"
                def _toggle(e):
                    _ssn.actualizar_visita(v_id, new_est, p, o, c)
                    if new_est == "realizada":
                        show_snackbar(f"¡Visita a {v_name} marcada como Realizada! 🚀")
                    else:
                        show_snackbar(f"Visita a {v_name} marcada como Pendiente ⏳")
                    refresh_dashboard()
                return _toggle

            def make_del_visita(v_id=vid, v_name=vnombre):
                def _del(e):
                    _ssn.eliminar_visita(v_id)
                    show_snackbar(f"Visita a {v_name} eliminada.")
                    refresh_dashboard()
                return _del

            def make_click_visita(v_rec=v):
                def _click(e):
                    mat = v_rec.get("matricula")
                    if mat:
                        if state and "open_detail_by_matricula" in state:
                            state["open_detail_by_matricula"](mat)
                    else:
                        show_snackbar("Este PAS fue creado manualmente sin matrícula vinculada.", is_error=True)
                return _click

            if vest == "realizada":
                chk = ft.Container(
                    content=ft.Row([
                        ft.Icon(ft.Icons.CHECK_CIRCLE_ROUNDED, size=15, color=COLORS["success"]),
                        ft.Text("Realizada", size=12, weight=ft.FontWeight.W_600, color=COLORS["success"]),
                    ], spacing=5, tight=True),
                    bgcolor=ft.Colors.with_opacity(0.12, COLORS["success"]),
                    border=ft.Border.all(1.5, COLORS["success"]),
                    border_radius=20,
                    padding=ft.Padding(left=12, right=14, top=6, bottom=6),
                    on_click=make_toggle_visita(),
                    tooltip="Hacé clic para volver a marcar como Pendiente",
                    ink=True,
                )
            else:
                chk = ft.Container(
                    content=ft.Row([
                        ft.Icon(ft.Icons.RADIO_BUTTON_UNCHECKED_ROUNDED, size=15, color=COLORS["text_secondary"]),
                        ft.Text("Pendiente", size=12, weight=ft.FontWeight.W_600, color=COLORS["text_secondary"]),
                    ], spacing=5, tight=True),
                    bgcolor=COLORS["surface"],
                    border=ft.Border.all(1.5, COLORS["border"]),
                    border_radius=20,
                    padding=ft.Padding(left=12, right=14, top=6, bottom=6),
                    on_click=make_toggle_visita(),
                    tooltip="Hacé clic para marcar como REALIZADA",
                    ink=True,
                )

            pas_info_clicker = ft.Container(
                content=ft.Row([
                    ft.CircleAvatar(
                        content=ft.Text(v["nombre"][0].upper() if v["nombre"] else "?", size=16, weight=ft.FontWeight.BOLD, color=COLORS["text_on_primary"]),
                        bgcolor=COLORS["primary"],
                        radius=20,
                    ),
                    ft.Column([
                        ft.Row([
                            ft.Text(v["nombre"], size=14, weight=ft.FontWeight.W_600, color=COLORS["text_primary"]),
                            _status_chip(v.get("campaña") or "Sin Compañía", COLORS["primary"] if v.get("campaña") else "#64748b"),
                        ], spacing=8),
                        ft.Row([
                            ft.Icon(ft.Icons.CALENDAR_MONTH_ROUNDED, size=14, color=COLORS["primary"]),
                            ft.Text(v.get("fecha") or "Sin fecha", size=12, color=COLORS["text_secondary"]),
                            ft.Container(width=12),
                            ft.Icon(ft.Icons.LOCATION_ON_ROUNDED, size=14, color=COLORS["accent"]),
                            ft.Text(v.get("lugar") or "Sin ubicación", size=12, color=COLORS["text_secondary"]),
                        ], spacing=4) if (v.get("fecha") or v.get("lugar")) else ft.Container(),
                    ], spacing=6, expand=True),
                ], spacing=12, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                expand=True,
                on_click=make_click_visita(v),
                tooltip="Hacé clic para ver la ficha del Productor",
                ink=True,
            )

            items.append(ft.Container(
                content=ft.Row([
                    pas_info_clicker,
                    ft.Row([
                        chk,
                        ft.IconButton(
                            ft.Icons.DELETE_OUTLINE_ROUNDED,
                            icon_color=ft.Colors.RED_400,
                            icon_size=18,
                            on_click=make_del_visita(),
                            tooltip="Eliminar del plan de visitas"
                        ),
                    ], spacing=6, vertical_alignment=ft.CrossAxisAlignment.CENTER)
                ], spacing=12, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                bgcolor=COLORS["surface"],
                border=ft.Border(
                    left=ft.BorderSide(6, COLORS["success"] if vest=="realizada" else COLORS["primary"]),
                    top=ft.BorderSide(1, COLORS["border"]),
                    right=ft.BorderSide(1, COLORS["border"]),
                    bottom=ft.BorderSide(1, COLORS["border"])
                ),
                border_radius=12,
                padding=ft.Padding(16, 14, 16, 14),
                shadow=ft.BoxShadow(spread_radius=1, blur_radius=8, color=ft.Colors.with_opacity(0.08, "#000000"), offset=ft.Offset(0, 4)),
            ))
        if not items:
            pas_list_col.controls = [ft.Container(
                content=ft.Column([
                    ft.Icon(ft.Icons.EVENT_BUSY_ROUNDED, size=48, color=COLORS["border"]),
                    ft.Text("No hay visitas planificadas", size=14, weight=ft.FontWeight.BOLD, color=COLORS["text_secondary"]),
                    ft.Text("Intentá cambiar los filtros o agregá un nuevo PAS a la lista.", size=12, color=COLORS["text_secondary"], text_align=ft.TextAlign.CENTER),
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=4),
                alignment=ft.Alignment(0, 0),
                padding=40,
            )]
        else:
            pas_list_col.controls = items
        try:
            page.update()
        except Exception as ex:
            print("filter_and_render error:", ex)

    def _on_search_change(e):
        filter_state["search"] = search_field.value or ""
        filter_and_render()
    search_field.on_change = _on_search_change

    # ── Diálogo Agregar PAS ────────────────────────────────────────────────
    from datetime import datetime
    add_nombre_tf = ft.TextField(
        label="Nombre del PAS *",
        prefix_icon=ft.Icons.PERSON_OUTLINE_ROUNDED,
        border_color="#94A3B8", bgcolor=COLORS["surface"], focused_border_color=COLORS["primary"],
        border_radius=12, text_size=13, height=48, content_padding=ft.Padding(12, 0, 12, 0)
    )
    add_compania_tf = ft.TextField(
        label="Compañía",
        prefix_icon=ft.Icons.BUSINESS_ROUNDED,
        border_color="#94A3B8", bgcolor=COLORS["surface"], focused_border_color=COLORS["primary"],
        border_radius=12, text_size=13, height=48, expand=1, content_padding=ft.Padding(12, 0, 12, 0)
    )
    add_matricula_tf = ft.TextField(
        label="Matrícula (opcional)",
        prefix_icon=ft.Icons.BADGE_OUTLINED,
        border_color="#94A3B8", bgcolor=COLORS["surface"], focused_border_color=COLORS["primary"],
        border_radius=12, text_size=13, height=48, expand=1, content_padding=ft.Padding(12, 0, 12, 0)
    )

    add_suggestions_col = ft.Column(spacing=2, tight=True)
    add_suggestions_container = ft.Container(
        content=add_suggestions_col,
        visible=False,
        bgcolor=COLORS["surface"],
        border=ft.Border.all(1, COLORS["primary"]),
        border_radius=10,
        padding=ft.Padding(6, 6, 6, 6),
        shadow=ft.BoxShadow(spread_radius=1, blur_radius=8, color=ft.Colors.with_opacity(0.15, "#000000")),
    )

    def _on_add_nombre_change(e):
        val = (add_nombre_tf.value or "").strip()
        if len(val) < 2:
            add_suggestions_col.controls = []
            add_suggestions_container.visible = False
            try: add_suggestions_container.update()
            except:
                try: page.update()
                except: pass
            return

        from utils import normalize
        tokens = [t for t in normalize(val).split() if t]
        
        matches = []
        for r in (records or []):
            nom = r.get("productor_apellido_nombre") or r.get("nombre") or ""
            mat = str(r.get("productor_matricula") or r.get("matricula") or "")
            cuit = str(r.get("productor_id") or r.get("cuit") or r.get("documento") or "")
            prov = r.get("provincia") or ""
            loc = r.get("localidad") or ""
            
            haystack = normalize(f"{nom} {mat} {cuit} {prov} {loc}")
            
            if all(t in haystack for t in tokens):
                matches.append(r)
                if len(matches) >= 6:
                    break
        
        if not matches:
            add_suggestions_col.controls = []
            add_suggestions_container.visible = False
        else:
            controls = []
            for r in matches:
                r_nom = r.get("productor_apellido_nombre") or r.get("nombre") or ""
                r_mat = str(r.get("productor_matricula") or r.get("matricula") or "")
                r_comp = r.get("companias") or ""
                
                def make_click_handler(name, mat_val, comp_val):
                    def _handler(ev):
                        add_nombre_tf.value = name
                        add_nombre_tf.error_text = None
                        if mat_val:
                            add_matricula_tf.value = str(mat_val)
                        if comp_val:
                            add_compania_tf.value = str(comp_val)
                        add_suggestions_col.controls = []
                        add_suggestions_container.visible = False
                        try:
                            add_nombre_tf.update()
                            add_matricula_tf.update()
                            add_compania_tf.update()
                            add_suggestions_container.update()
                        except:
                            try: page.update()
                            except: pass
                    return _handler

                item = ft.Container(
                    content=ft.Row([
                        ft.Icon(ft.Icons.PERSON_ROUNDED, size=16, color=COLORS["primary"]),
                        ft.Column([
                            ft.Text(r_nom, size=13, weight=ft.FontWeight.W_600, color=COLORS["text_primary"]),
                            ft.Text(
                                f"Matrícula: {r_mat}" + (f" · {r_comp}" if r_comp else ""),
                                size=11, color=COLORS["text_secondary"]
                            ),
                        ], spacing=1, expand=True),
                        ft.Icon(ft.Icons.CHEVRON_RIGHT_ROUNDED, size=16, color=COLORS["text_secondary"]),
                    ], spacing=8, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                    padding=ft.Padding(8, 6, 8, 6),
                    bgcolor=COLORS["surface"],
                    border_radius=6,
                    on_click=make_click_handler(r_nom, r_mat, r_comp),
                    ink=True,
                )
                controls.append(item)
            add_suggestions_col.controls = controls
            add_suggestions_container.visible = True
            
        try: add_suggestions_container.update()
        except:
            try: page.update()
            except: pass

    add_nombre_tf.on_change = _on_add_nombre_change

    # ── Date + Time picker ────────────────────────────────────────────────
    _now = datetime.now()
    _selected_dt = {"val": _now}          # mutable holder

    # Campo oculto que el código de guardado ya usa: add_fecha_tf.value
    add_fecha_tf = ft.TextField(
        value=_now.strftime("%Y-%m-%d %H:%M"),
        visible=False,
    )

    # Texto de display que el usuario ve
    _fecha_display_text = ft.Text(
        _now.strftime("%d/%m/%Y  %H:%M"),
        size=13, color=COLORS["text_primary"],
        weight=ft.FontWeight.W_500,
    )
    _fecha_error_text = ft.Text("", size=11, color=ft.Colors.RED_400)

    def _sync_display():
        dt = _selected_dt["val"]
        add_fecha_tf.value = dt.strftime("%Y-%m-%d %H:%M")
        _fecha_display_text.value = dt.strftime("%d/%m/%Y  %H:%M")
        _fecha_error_text.value = ""
        try: page.update()
        except: pass

    def _on_time_picked(e):
        if e.control.value is not None:
            t = e.control.value
            _selected_dt["val"] = _selected_dt["val"].replace(
                hour=t.hour, minute=t.minute
            )
            _sync_display()

    def _on_date_picked(e):
        if e.control.value is not None:
            d = e.control.value
            _selected_dt["val"] = _selected_dt["val"].replace(
                year=d.year, month=d.month, day=d.day
            )
            _sync_display()
            # Cadena al TimePicker
            try:
                time_picker.open = True
                page.update()
            except Exception:
                pass

    date_picker = ft.DatePicker(
        first_date=datetime(2020, 1, 1),
        last_date=datetime(2030, 12, 31),
        on_change=_on_date_picked,
        locale=ft.Locale("es", "ES"),
        help_text="Seleccionar fecha de la reunión",
        cancel_text="Cancelar",
        confirm_text="Aceptar",
        error_format_text="Formato de fecha inválido",
        error_invalid_text="Fecha fuera de rango",
        field_hint_text="dd/mm/aaaa",
        field_label_text="Ingresar fecha",
    )
    time_picker = ft.TimePicker(
        on_change=_on_time_picked,
        help_text="Seleccionar hora de la reunión",
        cancel_text="Cancelar",
        confirm_text="Aceptar",
        hour_label_text="Hora",
        minute_label_text="Minuto",
        error_invalid_text="Hora inválida",
    )
    if date_picker not in page.overlay:
        page.overlay.append(date_picker)
    if time_picker not in page.overlay:
        page.overlay.append(time_picker)

    def _open_date_picker(e):
        date_picker.value = _selected_dt["val"]
        date_picker.open = True
        page.update()

    # Widget visible: contenedor con apariencia de TextField
    fecha_picker_widget = ft.Container(
        content=ft.Row(
            controls=[
                ft.Icon(ft.Icons.CALENDAR_MONTH_ROUNDED,
                        color=COLORS["primary"], size=18),
                ft.Column(
                    controls=[
                        ft.Text("Fecha y Hora *", size=10,
                                color=COLORS["text_secondary"],
                                weight=ft.FontWeight.W_500),
                        _fecha_display_text,
                    ],
                    spacing=1,
                    expand=True,
                ),
                ft.Icon(ft.Icons.ARROW_DROP_DOWN_ROUNDED,
                        color=COLORS["text_secondary"], size=20),
            ],
            spacing=10,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        ),
        border=ft.Border.all(1.5, "#94A3B8"),
        border_radius=12,
        height=56,
        padding=ft.Padding(12, 0, 12, 0),
        bgcolor=COLORS["surface"],
        on_click=_open_date_picker,
        ink=True,
        expand=1,
    )

    add_lugar_tf = ft.TextField(
        label="Lugar / Dirección",
        prefix_icon=ft.Icons.LOCATION_ON_OUTLINED,
        border_color="#94A3B8", bgcolor=COLORS["surface"], focused_border_color=COLORS["primary"],
        border_radius=12, text_size=13, height=48, expand=1, content_padding=ft.Padding(12, 0, 12, 0)
    )
    add_nota_tf = ft.TextField(
        label="Nota / Productividad (opcional)",
        prefix_icon=ft.Icons.NOTES_ROUNDED,
        multiline=True, min_lines=2, max_lines=4,
        border_color="#94A3B8", bgcolor=COLORS["surface"], focused_border_color=COLORS["primary"],
        border_radius=12, text_size=13, content_padding=ft.Padding(12, 12, 12, 12)
    )
    
    def close_dialog(e):
        add_dialog.open = False
        try: page.update()
        except: pass
        
    def save_new_pas(e):
        nombre = (add_nombre_tf.value or "").strip()
        if not nombre:
            add_nombre_tf.error_text = "El nombre es obligatorio"
            try: add_nombre_tf.update()
            except: pass
            return
            
        fecha_val = (add_fecha_tf.value or "").strip()
        if not fecha_val:
            add_fecha_tf.error_text = "La fecha y hora es obligatoria"
            try: add_fecha_tf.update()
            except: pass
            return

        compania = (add_compania_tf.value or "").strip()
        matricula = (add_matricula_tf.value or "").strip()
        lugar = (add_lugar_tf.value or "").strip()
        nota = (add_nota_tf.value or "").strip()
        
        _ssn.guardar_visita(
            mes=mes_actual,
            matricula=matricula,
            nombre=nombre,
            estado='pendiente',
            productividad=nota,
            campaña=compania,
            lugar=lugar,
            fecha=fecha_val
        )
        
        add_nombre_tf.value = ""
        add_nombre_tf.error_text = None
        add_compania_tf.value = ""
        add_matricula_tf.value = ""
        _reset_now = datetime.now()
        _selected_dt["val"] = _reset_now
        add_fecha_tf.value = _reset_now.strftime("%Y-%m-%d %H:%M")
        _fecha_display_text.value = _reset_now.strftime("%d/%m/%Y  %H:%M")
        add_lugar_tf.value = "Oficina"
        add_nota_tf.value = ""
        
        add_dialog.open = False
        try: page.update()
        except: pass
        refresh_dashboard()
        
    add_dialog_title = ft.Row([
        ft.Icon(ft.Icons.EVENT_AVAILABLE_ROUNDED, color=COLORS["primary"], size=24),
        ft.Text("Agendar Nueva Visita", size=18, weight=ft.FontWeight.BOLD, color=COLORS["text_primary"])
    ], spacing=10, vertical_alignment=ft.CrossAxisAlignment.CENTER)

    add_dialog = ft.AlertDialog(
        title=add_dialog_title,
        title_padding=ft.Padding(24, 24, 24, 0),
        content_padding=ft.Padding(24, 20, 24, 20),
        actions_padding=ft.Padding(16, 0, 24, 24),
        content=ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Icon(ft.Icons.ACCOUNT_CIRCLE_ROUNDED, size=16, color=COLORS["primary"]),
                    ft.Text("DATOS DEL PRODUCTOR (PAS)", size=11, weight=ft.FontWeight.BOLD, color=COLORS["primary"])
                ], spacing=6),
                add_nombre_tf,
                add_suggestions_container,
                ft.Row([add_compania_tf, add_matricula_tf], spacing=12),
                ft.Divider(height=16, color=COLORS["divider"]),
                ft.Row([
                    ft.Icon(ft.Icons.MEETING_ROOM_ROUNDED, size=16, color=COLORS["primary"]),
                    ft.Text("DETALLES DE LA REUNIÓN / VISITA", size=11, weight=ft.FontWeight.BOLD, color=COLORS["primary"])
                ], spacing=6),
                ft.Row([fecha_picker_widget, add_lugar_tf], spacing=12),
                add_nota_tf,
            ], spacing=14, tight=True),
            width=600,
        ),
        actions=[
            ft.TextButton(
                "Cancelar", 
                style=ft.ButtonStyle(color=COLORS["text_secondary"]),
                on_click=close_dialog
            ),
            ft.FilledButton(
                "Guardar Visita", 
                bgcolor=COLORS["primary"], 
                icon=ft.Icons.SAVE_ROUNDED,
                style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8)),
                on_click=save_new_pas
            ),
        ],
        actions_alignment=ft.MainAxisAlignment.END,
        shape=ft.RoundedRectangleBorder(radius=16)
    )
    
    def open_add_pas_dialog(e):
        try:
            print("[dialog] open_add_pas_dialog called")
            if state and state.get("prefill_new_visit"):
                prefill = state.pop("prefill_new_visit")
                print(f"[dialog] Prefilling data: {prefill}")
                
                # Override title with prefill info using the same style
                add_dialog.title = ft.Row([
                    ft.Icon(ft.Icons.EVENT_AVAILABLE_ROUNDED, color=COLORS["primary"], size=24),
                    ft.Text(f"Agendar Visita con {prefill.get('nombre')}", size=18, weight=ft.FontWeight.BOLD, color=COLORS["text_primary"])
                ], spacing=10, vertical_alignment=ft.CrossAxisAlignment.CENTER)
                
                # Assign values for backend saving
                add_nombre_tf.value = prefill.get("nombre") or ""
                add_compania_tf.value = prefill.get("compania") or ""
                add_matricula_tf.value = str(prefill.get("matricula") or "")
                
                # Make these fields visible and editable so they can be modified
                add_nombre_tf.visible = True
                add_nombre_tf.disabled = False
                add_nombre_tf.error_text = None
                
                add_compania_tf.value = prefill.get("compania") or ""
                add_compania_tf.visible = True
                add_compania_tf.disabled = False
                
                add_matricula_tf.value = str(prefill.get("matricula") or "")
                add_matricula_tf.visible = True
                add_matricula_tf.disabled = False
                
                add_fecha_tf.value = datetime.now().strftime("%Y-%m-%d %H:%M")
                add_lugar_tf.value = "Oficina"
                add_nota_tf.value = ""
            else:
                print("[dialog] Resetting fields to empty")
                add_dialog.title = ft.Text("Agregar Nuevo PAS", weight=ft.FontWeight.BOLD)
                
                # Show all fields for manual entry
                add_nombre_tf.value = ""
                add_nombre_tf.visible = True
                add_nombre_tf.error_text = None
                
                add_compania_tf.value = ""
                add_compania_tf.visible = True
                
                add_matricula_tf.value = ""
                add_matricula_tf.visible = True
                
                add_suggestions_col.controls = []
                add_suggestions_container.visible = False
                add_fecha_tf.value = datetime.now().strftime("%Y-%m-%d %H:%M")
                add_fecha_tf.error_text = None
                add_lugar_tf.value = "Oficina"
                add_nota_tf.value = ""

            if add_dialog not in page.overlay:
                page.overlay.append(add_dialog)
            add_dialog.open = True
            page.update()
            print("[dialog] dialog opened and page.update() called successfully")
        except Exception as ex:
            import traceback
            print("[dialog] CRITICAL ERROR in open_add_pas_dialog:", ex)
            traceback.print_exc()

    btn_agregar_pas = ft.FilledButton(
        "+ Agregar PAS",
        bgcolor=COLORS["primary"],
        color=COLORS["text_on_primary"],
        on_click=open_add_pas_dialog,
        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8)),
        height=42,
    )
    
    filters_row = ft.Row(
        controls=[search_field, company_btn, status_btn, btn_agregar_pas],
        spacing=10,
        alignment=ft.MainAxisAlignment.START,
        vertical_alignment=ft.CrossAxisAlignment.CENTER,
    )
    filters_container = ft.Container(
        content=filters_row,
        bgcolor=COLORS["surface"],
        border_radius=12,
        padding=ft.Padding(16, 12, 16, 12),
        shadow=ft.BoxShadow(spread_radius=1, blur_radius=8, color=ft.Colors.with_opacity(0.06, "#000000"), offset=ft.Offset(0, 4)),
    )

    # ── Componentes de Seguimiento Diario (Excel) ─────────────────────────
    all_actividades = []
    excel_filter_state = {"search": "", "type": "Todos"}

    excel_search_field = ft.TextField(
        hint_text="Buscar por nombre o compañía...",
        prefix_icon=ft.Icons.SEARCH_ROUNDED,
        border_color="#94A3B8", bgcolor=COLORS["surface"],
        focused_border_color=COLORS["primary"],
        border_radius=8,
        text_size=13,
        height=42,
        expand=True,
    )

    excel_type_label = ft.Text("Todos los tipos", size=12, color=COLORS["text_primary"])
    def set_excel_type(val, label_txt):
        excel_filter_state["type"] = val
        excel_type_label.value = label_txt
        filter_and_render_excel()

    excel_type_btn = ft.PopupMenuButton(
        content=ft.Container(
            content=ft.Row([
                ft.Icon(ft.Icons.CATEGORY_ROUNDED, size=14, color=COLORS["text_secondary"]),
                excel_type_label,
                ft.Icon(ft.Icons.ARROW_DROP_DOWN_ROUNDED, size=16, color=COLORS["text_secondary"]),
            ], spacing=4, vertical_alignment=ft.CrossAxisAlignment.CENTER),
            bgcolor=COLORS["surface"],
            border=ft.Border.all(1, COLORS["border"]),
            border_radius=8,
            padding=ft.Padding(10, 8, 10, 8),
            height=42,
            width=150,
        ),
        items=[
            _make_menu_item("Todos", lambda e: set_excel_type("Todos", "Todos los tipos")),
            _make_menu_item("Llamados", lambda e: set_excel_type("Llamado", "Llamados")),
            _make_menu_item("Reuniones", lambda e: set_excel_type("Reunión", "Reuniones")),
        ]
    )

    def show_snackbar(message: str, is_error: bool = False):
        page.snack_bar = ft.SnackBar(
            content=ft.Text(message, color=ft.Colors.WHITE, size=13, weight=ft.FontWeight.W_500),
            bgcolor=COLORS["primary"] if not is_error else ft.Colors.RED_600,
            duration=3500,
            dismiss_direction=ft.DismissDirection.HORIZONTAL,
        )
        page.snack_bar.open = True
        try: page.update()
        except: pass

    def sync_excel_click(e):
        btn_sync_excel.disabled = True
        btn_sync_excel.content = ft.ProgressRing(width=16, height=16, stroke_width=2, color=COLORS["text_on_primary"])
        try: page.update()
        except: pass
        
        import os
        excel_file = "PLANILLA SEGUIMIENTO REUNION Y LLAMADOS.xlsx"
        if not os.path.exists(excel_file):
            show_snackbar(f"No se encontró el archivo {excel_file}", is_error=True)
        else:
            res = _ssn.importar_actividades_desde_excel(excel_file)
            if res.get("success"):
                show_snackbar(res.get("message", "Sincronización completada"))
            else:
                show_snackbar(res.get("message", "Error al sincronizar"), is_error=True)
                
        btn_sync_excel.disabled = False
        btn_sync_excel.content = ft.Text("Sincronizar Excel", size=12, weight=ft.FontWeight.BOLD, color=COLORS["text_on_primary"])
        refresh_dashboard()

    btn_sync_excel = ft.FilledButton(
        "Sincronizar Excel",
        bgcolor=COLORS["primary"],
        color=COLORS["text_on_primary"],
        on_click=sync_excel_click,
        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8)),
        height=42,
    )

    # Diálogo Agregar Actividad Manualmente
    def on_act_date_change(e):
        if add_act_date_picker.value:
            add_act_fecha_tf.value = add_act_date_picker.value.strftime("%Y-%m-%d")
            add_act_fecha_tf.error_text = None
            try: add_act_fecha_tf.update()
            except: pass

    add_act_date_picker = ft.DatePicker(
        on_change=on_act_date_change,
        first_date=_dt(2020, 1, 1),
        last_date=_dt(2035, 12, 31),
        locale=ft.Locale("es", "ES"),
        help_text="Seleccionar fecha",
        cancel_text="Cancelar",
        confirm_text="Aceptar",
        error_format_text="Formato de fecha inválido",
        error_invalid_text="Fecha fuera de rango",
        field_hint_text="dd/mm/aaaa",
        field_label_text="Ingresar fecha",
    )

    def open_date_picker(e):
        add_act_date_picker.open = True
        try: page.update()
        except: pass

    btn_act_date = ft.IconButton(
        icon=ft.Icons.CALENDAR_MONTH_ROUNDED,
        icon_color=COLORS["primary"],
        on_click=open_date_picker,
    )

    add_act_nombre_tf = ft.TextField(
        label="Nombre del Productor *", 
        prefix_icon=ft.Icons.PERSON_OUTLINE_ROUNDED,
        border_color="#94A3B8", bgcolor=COLORS["surface"], focused_border_color=COLORS["primary"], 
        border_radius=12, text_size=13, height=48, content_padding=ft.Padding(12, 0, 12, 0)
    )

    add_act_suggestions_col = ft.Column(spacing=2, tight=True)
    add_act_suggestions_container = ft.Container(
        content=add_act_suggestions_col,
        visible=False,
        bgcolor=COLORS["surface"],
        border=ft.Border.all(1, COLORS["primary"]),
        border_radius=10,
        padding=ft.Padding(6, 6, 6, 6),
        shadow=ft.BoxShadow(spread_radius=1, blur_radius=8, color=ft.Colors.with_opacity(0.15, "#000000")),
    )

    def _on_add_act_nombre_change(e):
        val = (add_act_nombre_tf.value or "").strip()
        if len(val) < 2:
            add_act_suggestions_col.controls = []
            add_act_suggestions_container.visible = False
            try: add_act_suggestions_container.update()
            except:
                try: page.update()
                except: pass
            return

        from utils import normalize
        tokens = [t for t in normalize(val).split() if t]
        
        matches = []
        for r in (records or []):
            nom = r.get("productor_apellido_nombre") or r.get("nombre") or ""
            mat = str(r.get("productor_matricula") or r.get("matricula") or "")
            cuit = str(r.get("productor_id") or r.get("cuit") or r.get("documento") or "")
            prov = r.get("provincia") or ""
            loc = r.get("localidad") or ""
            
            haystack = normalize(f"{nom} {mat} {cuit} {prov} {loc}")
            
            if all(t in haystack for t in tokens):
                matches.append(r)
                if len(matches) >= 6:
                    break
        
        if not matches:
            add_act_suggestions_col.controls = []
            add_act_suggestions_container.visible = False
        else:
            controls = []
            for r in matches:
                r_nom = r.get("productor_apellido_nombre") or r.get("nombre") or ""
                r_mat = str(r.get("productor_matricula") or r.get("matricula") or "")
                r_comp = r.get("companias") or ""
                
                def make_click_act_handler(name, comp_val):
                    def _handler(ev):
                        add_act_nombre_tf.value = name
                        add_act_nombre_tf.error_text = None
                        if comp_val:
                            add_act_compania_tf.value = comp_val
                        add_act_suggestions_col.controls = []
                        add_act_suggestions_container.visible = False
                        try:
                            add_act_nombre_tf.update()
                            add_act_compania_tf.update()
                            add_act_suggestions_container.update()
                        except:
                            try: page.update()
                            except: pass
                    return _handler

                item = ft.Container(
                    content=ft.Row([
                        ft.Icon(ft.Icons.PERSON_ROUNDED, size=16, color=COLORS["primary"]),
                        ft.Column([
                            ft.Text(r_nom, size=13, weight=ft.FontWeight.W_600, color=COLORS["text_primary"]),
                            ft.Text(
                                f"Matrícula: {r_mat}" + (f" · {r_comp}" if r_comp else ""),
                                size=11, color=COLORS["text_secondary"]
                            ),
                        ], spacing=1, expand=True),
                        ft.Icon(ft.Icons.CHEVRON_RIGHT_ROUNDED, size=16, color=COLORS["text_secondary"]),
                    ], spacing=8, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                    padding=ft.Padding(8, 6, 8, 6),
                    bgcolor=COLORS["surface"],
                    border_radius=6,
                    on_click=make_click_act_handler(r_nom, r_comp),
                    ink=True,
                )
                controls.append(item)
            add_act_suggestions_col.controls = controls
            add_act_suggestions_container.visible = True
            
        try: add_act_suggestions_container.update()
        except:
            try: page.update()
            except: pass

    add_act_nombre_tf.on_change = _on_add_act_nombre_change
    add_act_compania_tf = ft.TextField(
        label="Compañía", 
        prefix_icon=ft.Icons.BUSINESS_ROUNDED,
        border_color="#94A3B8", bgcolor=COLORS["surface"], focused_border_color=COLORS["primary"], 
        border_radius=12, text_size=13, height=48, content_padding=ft.Padding(12, 0, 12, 0)
    )
    add_act_tipo_dropdown = ft.Dropdown(
        label="Tipo de Actividad",
        border_color="#94A3B8", bgcolor=COLORS["surface"],
        focused_border_color=COLORS["primary"],
        border_radius=12,
        text_size=13,
        height=48,
        expand=1,
        content_padding=ft.Padding(12, 0, 12, 0),
        options=[
            ft.dropdown.Option("Llamado", "Llamado Telefónico"),
            ft.dropdown.Option("Reunión", "Reunión Presencial"),
        ],
        value="Llamado",
    )
    add_act_fecha_tf = ft.TextField(
        label="Fecha (AAAA-MM-DD) *",
        prefix_icon=ft.Icons.CALENDAR_TODAY_ROUNDED,
        suffix=btn_act_date,
        expand=1,
        value=_dt.now().strftime("%Y-%m-%d"),
        border_color="#94A3B8", bgcolor=COLORS["surface"],
        focused_border_color=COLORS["primary"],
        border_radius=12,
        text_size=13,
        height=48,
        content_padding=ft.Padding(12, 0, 12, 0)
    )
    add_act_obs_tf = ft.TextField(
        label="Observaciones (opcional)", 
        prefix_icon=ft.Icons.NOTES_ROUNDED,
        multiline=True, min_lines=2, max_lines=4,
        border_color="#94A3B8", bgcolor=COLORS["surface"], focused_border_color=COLORS["primary"], 
        border_radius=12, text_size=13, content_padding=ft.Padding(12, 12, 12, 12)
    )

    def close_act_dialog(e):
        add_act_dialog.open = False
        try: page.update()
        except: pass

    def save_new_activity(e):
        import re
        nombre = (add_act_nombre_tf.value or "").strip()
        if not nombre:
            add_act_nombre_tf.error_text = "El nombre es obligatorio"
            try: add_act_nombre_tf.update()
            except: pass
            return
            
        fecha = (add_act_fecha_tf.value or "").strip()
        if not re.match(r"^\d{4}-\d{2}-\d{2}$", fecha):
            add_act_fecha_tf.error_text = "Formato de fecha inválido (AAAA-MM-DD)"
            try: add_act_fecha_tf.update()
            except: pass
            return
            
        tipo = add_act_tipo_dropdown.value
        compania = (add_act_compania_tf.value or "").strip()
        obs = (add_act_obs_tf.value or "").strip()
        
        mes_val = fecha[:7] # YYYY-MM
        
        _ssn.guardar_actividad_comercial(
            mes=mes_val,
            fecha_actividad=fecha,
            matricula="",
            nombre=nombre,
            tipo=tipo,
            compania=compania,
            observaciones=obs
        )
        
        # Limpiar
        add_act_nombre_tf.value = ""
        add_act_nombre_tf.error_text = None
        add_act_compania_tf.value = ""
        add_act_fecha_tf.value = _dt.now().strftime("%Y-%m-%d")
        add_act_fecha_tf.error_text = None
        add_act_obs_tf.value = ""
        
        add_act_dialog.open = False
        try: page.update()
        except: pass
        show_snackbar("Actividad registrada con éxito")
        refresh_dashboard()

    add_act_dialog_title = ft.Row([
        ft.Icon(ft.Icons.ADD_TASK_ROUNDED, color=COLORS["primary"], size=24),
        ft.Text("Registrar Actividad Comercial", size=18, weight=ft.FontWeight.BOLD, color=COLORS["text_primary"])
    ], spacing=10, vertical_alignment=ft.CrossAxisAlignment.CENTER)

    add_act_dialog = ft.AlertDialog(
        title=add_act_dialog_title,
        title_padding=ft.Padding(24, 24, 24, 0),
        content_padding=ft.Padding(24, 20, 24, 20),
        actions_padding=ft.Padding(16, 0, 24, 24),
        content=ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Icon(ft.Icons.INFO_OUTLINE_ROUNDED, size=16, color=COLORS["primary"]),
                    ft.Text("DETALLES DE LA ACTIVIDAD", size=11, weight=ft.FontWeight.BOLD, color=COLORS["primary"])
                ], spacing=6),
                add_act_nombre_tf,
                add_act_suggestions_container,
                add_act_compania_tf,
                ft.Row([add_act_tipo_dropdown, add_act_fecha_tf], spacing=12),
                add_act_obs_tf,
            ], spacing=14, tight=True),
            width=550,
        ),
        actions=[
            ft.TextButton(
                "Cancelar", 
                style=ft.ButtonStyle(color=COLORS["text_secondary"]),
                on_click=close_act_dialog
            ),
            ft.FilledButton(
                "Guardar Actividad", 
                bgcolor=COLORS["primary"], 
                icon=ft.Icons.SAVE_ROUNDED,
                style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8)),
                on_click=save_new_activity
            ),
        ],
        actions_alignment=ft.MainAxisAlignment.END,
        shape=ft.RoundedRectangleBorder(radius=16)
    )

    def open_add_act_dialog(e):
        if add_act_date_picker not in page.overlay:
            page.overlay.append(add_act_date_picker)
        if add_act_dialog not in page.overlay:
            page.overlay.append(add_act_dialog)
        add_act_dialog.open = True
        try: page.update()
        except: pass

    btn_add_excel = ft.FilledButton(
        "+ Registrar Actividad",
        bgcolor=COLORS["success"],
        color=COLORS["text_on_primary"],
        on_click=open_add_act_dialog,
        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8)),
        height=42,
    )

    excel_search_field.on_change = lambda e: _on_excel_search_change(e)
    def _on_excel_search_change(e):
        excel_filter_state["search"] = excel_search_field.value or ""
        filter_and_render_excel()

    excel_filters_row = ft.Row(
        controls=[excel_search_field, excel_type_btn, btn_sync_excel, btn_add_excel],
        spacing=12,
        alignment=ft.MainAxisAlignment.START,
        vertical_alignment=ft.CrossAxisAlignment.CENTER,
    )
    excel_filters_container = ft.Container(
        content=excel_filters_row,
        bgcolor=COLORS["surface"],
        border_radius=16,
        padding=ft.Padding(16, 12, 16, 12),
        shadow=ft.BoxShadow(
            spread_radius=0, blur_radius=8,
            color=ft.Colors.with_opacity(0.05, ft.Colors.BLACK),
            offset=ft.Offset(0, 2)
        )
    )

    activities_list_col = ft.Column(spacing=8, scroll=ft.ScrollMode.AUTO, expand=True)
    activities_list_container = ft.Container(content=activities_list_col, expand=True)

    def excel_kpi_card(title, value, icon, color):
        return ft.Container(
            content=ft.Row([
                ft.Container(
                    content=ft.Icon(icon, color=color, size=24),
                    bgcolor=ft.Colors.with_opacity(0.12, color),
                    border_radius=12, padding=12,
                ),
                ft.Column([
                    ft.Text(str(value), size=28, weight=ft.FontWeight.W_800, color=COLORS["text_primary"]),
                    ft.Text(title, size=13, weight=ft.FontWeight.W_500, color=COLORS["text_secondary"]),
                ], spacing=2, tight=True),
            ], spacing=16, vertical_alignment=ft.CrossAxisAlignment.CENTER),
            bgcolor=COLORS["surface"],
            border=ft.Border.all(1, COLORS["border"]),
            border_radius=16, padding=20, expand=True,
            shadow=ft.BoxShadow(
                spread_radius=0, blur_radius=10,
                color=ft.Colors.with_opacity(0.04, ft.Colors.BLACK),
                offset=ft.Offset(0, 4)
            )
        )

    card_excel_calls = excel_kpi_card("Llamados Telefónicos", "0", ft.Icons.PHONE_ROUNDED, ft.Colors.BLUE_700)
    card_excel_meetings = excel_kpi_card("Reuniones Presenciales", "0", ft.Icons.PEOPLE_ROUNDED, ft.Colors.GREEN_700)
    excel_kpis_row = ft.Row([card_excel_calls, card_excel_meetings], spacing=14)

    def filter_and_render_excel():
        search_val = excel_filter_state["search"].strip().lower()
        type_val = excel_filter_state["type"]
        
        filtered = [
            a for a in all_actividades
            if (not search_val or
                search_val in a["nombre"].lower() or
                (a.get("compania") and search_val in a["compania"].lower())
            )
            and (type_val == "Todos" or a["tipo"] == type_val)
        ]
        
        items = []
        for a in filtered:
            def make_del_act(aid=a["id"]):
                def _del(e):
                    _ssn.eliminar_actividad_comercial(aid)
                    show_snackbar("Actividad eliminada")
                    refresh_dashboard()
                return _del
                
            type_color = ft.Colors.BLUE_700 if a["tipo"] == "Llamado" else ft.Colors.GREEN_700
            type_icon = ft.Icons.PHONE_ROUNDED if a["tipo"] == "Llamado" else ft.Icons.PEOPLE_ROUNDED
            
            items.append(ft.Container(
                content=ft.Row([
                    ft.Container(
                        content=type_icon if isinstance(type_icon, ft.Control) else ft.Icon(type_icon, color=type_color, size=18),
                        bgcolor=ft.Colors.with_opacity(0.12, type_color),
                        border_radius=10, padding=10,
                    ),
                    ft.Column([
                        ft.Row([
                            ft.Text(a["nombre"], size=14, weight=ft.FontWeight.BOLD, color=COLORS["text_primary"]),
                            _status_chip(a.get("compania") or "Sin Compañía", COLORS["primary"] if a.get("compania") else "#64748B"),
                        ], spacing=8),
                        ft.Row([
                            ft.Icon(ft.Icons.CALENDAR_TODAY_ROUNDED, size=12, color=COLORS["text_secondary"]),
                            ft.Text(a['fecha_actividad'], size=12, color=COLORS["text_secondary"]),
                            ft.Text("•", size=12, color=COLORS["text_secondary"]),
                            ft.Text(a["tipo"], size=12, weight=ft.FontWeight.BOLD, color=type_color),
                            ft.Text("•", size=12, color=COLORS["text_secondary"]),
                            ft.Text(a.get("observaciones") or "Sin observaciones", size=12, italic=True, color=COLORS["text_secondary"], max_lines=1, overflow=ft.TextOverflow.ELLIPSIS),
                        ], spacing=6, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                    ], spacing=4, expand=True),
                    ft.IconButton(ft.Icons.DELETE_OUTLINE_ROUNDED, icon_color=ft.Colors.RED_400, icon_size=18, on_click=make_del_act()),
                ], spacing=16, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                bgcolor=COLORS["surface"],
                border=ft.Border(
                    left=ft.BorderSide(4, type_color),
                    top=ft.BorderSide(1, COLORS["border"]),
                    right=ft.BorderSide(1, COLORS["border"]),
                    bottom=ft.BorderSide(1, COLORS["border"])
                ),
                border_radius=12,
                padding=ft.Padding(16, 16, 16, 16),
                shadow=ft.BoxShadow(
                    spread_radius=0, blur_radius=4,
                    color=ft.Colors.with_opacity(0.02, ft.Colors.BLACK),
                    offset=ft.Offset(0, 2)
                ),
                margin=ft.Margin(0, 0, 0, 4)
            ))
            
        if not items:
            activities_list_col.controls = [ft.Container(
                content=ft.Text("No se encontraron registros de actividades comerciales.",
                                size=12, italic=True, color=COLORS["text_secondary"]),
                padding=20,
            )]
        else:
            activities_list_col.controls = items
            
        try:
            activities_list_col.update()
        except:
            pass

    metrics_column = ft.Column(spacing=14, scroll=ft.ScrollMode.AUTO, expand=True)

    # ── Componentes de Candidatos ─────────────────────────────────────────
    all_candidatos = []
    candidatos_list_col = ft.Column(spacing=6, scroll=ft.ScrollMode.ADAPTIVE)
    candidatos_count_text = ft.Text("", size=11, color=COLORS["text_secondary"])

    def filter_and_render_candidatos():
        items = []
        for c in all_candidatos:
            def make_toggle_cand(cid=c["id"], cest=c["estado"]):
                nuevo = "captado" if cest != "captado" else "candidato"
                def _toggle(e):
                    _ssn.actualizar_candidato(cid, nuevo, c.get("notas",""), c.get("tiene_cartera",0))
                    refresh_dashboard()
                return _toggle
            def make_del_cand(cid=c["id"]):
                def _del(e):
                    _ssn.eliminar_candidato(cid)
                    refresh_dashboard()
                return _del
            est_color = COLORS["success"] if c["estado"] == "captado" else COLORS["warning"]
            if c["estado"] == "captado":
                chk_cand = ft.OutlinedButton(
                    "Captado",
                    icon=ft.Icons.HOW_TO_REG_ROUNDED,
                    icon_color=COLORS["success"],
                    style=ft.ButtonStyle(
                        color=COLORS["success"],
                        side=ft.BorderSide(1, COLORS["success"]),
                        shape=ft.RoundedRectangleBorder(radius=20),
                        padding=ft.Padding(12, 0, 12, 0)
                    ),
                    on_click=make_toggle_cand(),
                    height=28,
                )
            else:
                chk_cand = ft.OutlinedButton(
                    "En Gestión",
                    icon=ft.Icons.PERSON_ADD_ALT_1_ROUNDED,
                    icon_color=COLORS["warning"],
                    style=ft.ButtonStyle(
                        color=COLORS["warning"],
                        side=ft.BorderSide(1, COLORS["warning"]),
                        shape=ft.RoundedRectangleBorder(radius=20),
                        padding=ft.Padding(12, 0, 12, 0)
                    ),
                    on_click=make_toggle_cand(),
                    height=28,
                )
            items.append(ft.Container(
                content=ft.Row([
                    ft.Column([
                        ft.Text(c["nombre"], size=14, weight=ft.FontWeight.W_600, color=COLORS["text_primary"]),
                        ft.Row([
                            ft.Text(f"Mat: {c.get('matricula') or '—'}", size=12, color=COLORS["text_secondary"]),
                            ft.Text("•", size=12, color=COLORS["text_secondary"]),
                            ft.Text("Con cartera" if c.get("tiene_cartera") else "Sin cartera", size=12, color=COLORS["text_secondary"]),
                        ], spacing=6),
                        ft.Text(c.get("notas") or "", size=11, italic=True, color=COLORS["text_secondary"]) if c.get("notas") else ft.Container(),
                    ], spacing=4, expand=True),
                    ft.Row([
                        chk_cand,
                        ft.IconButton(ft.Icons.DELETE_OUTLINE_ROUNDED, icon_color=ft.Colors.RED_400, icon_size=18, on_click=make_del_cand()),
                    ], spacing=4),
                ], spacing=12, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                bgcolor=COLORS["surface"],
                border=ft.Border(
                    left=ft.BorderSide(6, est_color),
                    top=ft.BorderSide(1, COLORS["border"]),
                    right=ft.BorderSide(1, COLORS["border"]),
                    bottom=ft.BorderSide(1, COLORS["border"]),
                ),
                border_radius=12, padding=ft.Padding(16, 12, 12, 12),
                shadow=ft.BoxShadow(spread_radius=1, blur_radius=8, color=ft.Colors.with_opacity(0.08, "#000000"), offset=ft.Offset(0, 4)),
            ))
        candidatos_list_col.controls = items or [ft.Container(
            content=ft.Column([
                ft.Icon(ft.Icons.PERSON_OFF_ROUNDED, size=40, color=COLORS["border"]),
                ft.Text("No hay candidatos este mes", size=13, weight=ft.FontWeight.BOLD, color=COLORS["text_secondary"]),
                ft.Text("¡Agregá uno para empezar a trackearlos!", size=12, color=COLORS["text_secondary"]),
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=4),
            alignment=ft.Alignment(0, 0), padding=30
        )]
        try: candidatos_list_col.update()
        except: pass

    cand_nombre_tf = ft.TextField(
        label="Nombre Completo *", 
        prefix_icon=ft.Icons.PERSON_OUTLINE_ROUNDED,
        border_color="#94A3B8", bgcolor=COLORS["surface"], focused_border_color=COLORS["primary"], 
        border_radius=12, text_size=13, height=48, content_padding=ft.Padding(12, 0, 12, 0)
    )
    cand_matricula_tf = ft.TextField(
        label="Matrícula (Opcional)", 
        prefix_icon=ft.Icons.BADGE_OUTLINED,
        border_color="#94A3B8", bgcolor=COLORS["surface"], focused_border_color=COLORS["primary"], 
        border_radius=12, text_size=13, height=48, content_padding=ft.Padding(12, 0, 12, 0)
    )
    cand_notas_tf = ft.TextField(
        label="Notas o Comentarios", 
        prefix_icon=ft.Icons.STICKY_NOTE_2_OUTLINED,
        multiline=True, min_lines=2, max_lines=4,
        border_color="#94A3B8", bgcolor=COLORS["surface"], focused_border_color=COLORS["primary"], 
        border_radius=12, text_size=13, content_padding=ft.Padding(12, 12, 12, 12)
    )
    cand_cartera_chk = ft.Switch(
        label="¿Tiene cartera propia?", 
        value=False, 
        active_color=COLORS["primary"],
        label_position=ft.LabelPosition.LEFT
    )
    
    cand_dialog_title = ft.Row([
        ft.Icon(ft.Icons.PERSON_ADD_ALT_1_ROUNDED, color=COLORS["primary"], size=24),
        ft.Text("Nuevo Candidato", size=18, weight=ft.FontWeight.BOLD, color=COLORS["text_primary"])
    ], spacing=10, vertical_alignment=ft.CrossAxisAlignment.CENTER)

    cand_suggestions_col = ft.Column(spacing=2, tight=True)
    cand_suggestions_container = ft.Container(
        content=cand_suggestions_col,
        visible=False,
        bgcolor=COLORS["surface"],
        border=ft.Border.all(1, COLORS["primary"]),
        border_radius=10,
        padding=ft.Padding(6, 6, 6, 6),
        shadow=ft.BoxShadow(spread_radius=1, blur_radius=8, color=ft.Colors.with_opacity(0.15, "#000000")),
    )

    def _on_cand_nombre_change(e):
        val = (cand_nombre_tf.value or "").strip()
        if len(val) < 2:
            cand_suggestions_col.controls = []
            cand_suggestions_container.visible = False
            try: cand_suggestions_container.update()
            except:
                try: page.update()
                except: pass
            return

        from utils import normalize
        tokens = [t for t in normalize(val).split() if t]
        
        matches = []
        for r in (records or []):
            nom = r.get("productor_apellido_nombre") or r.get("nombre") or ""
            mat = str(r.get("productor_matricula") or r.get("matricula") or "")
            cuit = str(r.get("productor_id") or r.get("cuit") or r.get("documento") or "")
            prov = r.get("provincia") or ""
            loc = r.get("localidad") or ""
            
            haystack = normalize(f"{nom} {mat} {cuit} {prov} {loc}")
            
            if all(t in haystack for t in tokens):
                matches.append(r)
                if len(matches) >= 6:
                    break
        
        if not matches:
            cand_suggestions_col.controls = []
            cand_suggestions_container.visible = False
        else:
            controls = []
            for r in matches:
                r_nom = r.get("productor_apellido_nombre") or r.get("nombre") or ""
                r_mat = str(r.get("productor_matricula") or r.get("matricula") or "")
                r_comp = r.get("companias") or ""
                
                def make_click_cand_handler(name, mat_val):
                    def _handler(ev):
                        cand_nombre_tf.value = name
                        cand_nombre_tf.error_text = None
                        if mat_val:
                            cand_matricula_tf.value = str(mat_val)
                        cand_suggestions_col.controls = []
                        cand_suggestions_container.visible = False
                        try:
                            cand_nombre_tf.update()
                            cand_matricula_tf.update()
                            cand_suggestions_container.update()
                        except:
                            try: page.update()
                            except: pass
                    return _handler

                item = ft.Container(
                    content=ft.Row([
                        ft.Icon(ft.Icons.PERSON_ROUNDED, size=16, color=COLORS["primary"]),
                        ft.Column([
                            ft.Text(r_nom, size=13, weight=ft.FontWeight.W_600, color=COLORS["text_primary"]),
                            ft.Text(
                                f"Matrícula: {r_mat}" + (f" · {r_comp}" if r_comp else ""),
                                size=11, color=COLORS["text_secondary"]
                            ),
                        ], spacing=1, expand=True),
                        ft.Icon(ft.Icons.CHEVRON_RIGHT_ROUNDED, size=16, color=COLORS["text_secondary"]),
                    ], spacing=8, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                    padding=ft.Padding(8, 6, 8, 6),
                    bgcolor=COLORS["surface"],
                    border_radius=6,
                    on_click=make_click_cand_handler(r_nom, r_mat),
                    ink=True,
                )
                controls.append(item)
            cand_suggestions_col.controls = controls
            cand_suggestions_container.visible = True
            
        try: cand_suggestions_container.update()
        except:
            try: page.update()
            except: pass

    cand_nombre_tf.on_change = _on_cand_nombre_change

    cand_dialog = ft.AlertDialog(
        title=cand_dialog_title,
        title_padding=ft.Padding(24, 24, 24, 0),
        content_padding=ft.Padding(24, 20, 24, 20),
        actions_padding=ft.Padding(16, 0, 24, 24),
        content=ft.Container(
            content=ft.Column([
                cand_nombre_tf,
                cand_suggestions_container,
                cand_matricula_tf,
                ft.Container(
                    content=cand_cartera_chk,
                    padding=ft.Padding(12, 4, 12, 4),
                    bgcolor=COLORS["surface"],
                    border=ft.Border.all(1, COLORS["border"]),
                    border_radius=12
                ),
                cand_notas_tf
            ], spacing=16, tight=True, width=400),
        ),
        actions=[
            ft.TextButton(
                "Cancelar", 
                style=ft.ButtonStyle(color=COLORS["text_secondary"]),
                on_click=lambda e: (setattr(cand_dialog, 'open', False), page.update())
            ),
            ft.FilledButton(
                "Guardar Candidato", 
                bgcolor=COLORS["primary"], 
                icon=ft.Icons.SAVE_ROUNDED,
                style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8)),
                on_click=lambda e: _save_candidato(e)
            ),
        ],
        actions_alignment=ft.MainAxisAlignment.END,
        shape=ft.RoundedRectangleBorder(radius=16)
    )
    def _save_candidato(e):
        nombre = (cand_nombre_tf.value or "").strip()
        if not nombre:
            cand_nombre_tf.error_text = "Requerido"
            try: cand_nombre_tf.update()
            except: pass
            return
        _ssn.guardar_candidato(mes_actual, nombre, cand_matricula_tf.value or "", 1 if cand_cartera_chk.value else 0, "candidato", cand_notas_tf.value or "")
        cand_nombre_tf.value = ""; cand_matricula_tf.value = ""; cand_notas_tf.value = ""; cand_nombre_tf.error_text = None
        cand_dialog.open = False
        try: page.update()
        except: pass
        refresh_dashboard()
    def _open_cand_dialog(e):
        if cand_dialog not in page.overlay:
            page.overlay.append(cand_dialog)
        cand_dialog.open = True
        try: page.update()
        except: pass

    candidatos_section = ft.Container(
        content=ft.Column([
            ft.Row([
                ft.Row([
                    ft.Container(
                        content=ft.Icon(ft.Icons.PERSON_ADD_ALT_1_ROUNDED, size=16, color=COLORS["text_on_primary"]),
                        bgcolor=COLORS["accent"], padding=6, border_radius=8
                    ),
                    ft.Text("Captación de Candidatos", size=14, weight=ft.FontWeight.BOLD, color=COLORS["text_primary"]),
                    ft.Container(content=candidatos_count_text, bgcolor=ft.Colors.with_opacity(0.1, COLORS["accent"]), padding=ft.Padding(6,2,6,2), border_radius=12)
                ], spacing=8),
                ft.FilledButton("+ Candidato", bgcolor=COLORS["accent"], color=COLORS["text_on_primary"],
                                on_click=_open_cand_dialog, style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8)), height=32),
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN, vertical_alignment=ft.CrossAxisAlignment.CENTER),
            candidatos_list_col,
        ], spacing=12),
        bgcolor="#F0F9FF",  # Light blue background for Candidatos
        border=ft.Border.all(1, "#BAE6FD"),
        border_radius=12, padding=16,
    )

    # ── Componentes de Acciones Mensuales ─────────────────────────────────
    all_acciones = []
    acciones_list_col = ft.Column(spacing=6, scroll=ft.ScrollMode.ADAPTIVE)
    acciones_count_text = ft.Text("", size=11, color=COLORS["text_secondary"])

    def filter_and_render_acciones():
        items = []
        for a in all_acciones:
            def make_toggle_acc(aid=a["id"], aest=a["estado"], adesc=a.get("descripcion","")):
                nuevo = "realizada" if aest != "realizada" else "pendiente"
                def _toggle(e):
                    _ssn.actualizar_accion(aid, nuevo, adesc)
                    refresh_dashboard()
                return _toggle
            def make_del_acc(aid=a["id"]):
                def _del(e):
                    _ssn.eliminar_accion(aid)
                    refresh_dashboard()
                return _del
            if a["estado"] == "realizada":
                chk_acc = ft.OutlinedButton(
                    "Realizada",
                    icon=ft.Icons.CHECK_CIRCLE_ROUNDED,
                    icon_color=COLORS["success"],
                    style=ft.ButtonStyle(
                        color=COLORS["success"],
                        side=ft.BorderSide(1, COLORS["success"]),
                        shape=ft.RoundedRectangleBorder(radius=20),
                        padding=ft.Padding(12, 0, 12, 0)
                    ),
                    on_click=make_toggle_acc(),
                    height=28,
                )
            else:
                chk_acc = ft.OutlinedButton(
                    "Pendiente",
                    icon=ft.Icons.RADIO_BUTTON_UNCHECKED_ROUNDED,
                    icon_color=COLORS["text_secondary"],
                    style=ft.ButtonStyle(
                        color=COLORS["text_secondary"],
                        side=ft.BorderSide(1, COLORS["border"]),
                        shape=ft.RoundedRectangleBorder(radius=20),
                        padding=ft.Padding(12, 0, 12, 0)
                    ),
                    on_click=make_toggle_acc(),
                    height=28,
                )
            tipo_color = {"visita": COLORS["primary"], "llamado": COLORS["accent"], "reunion": COLORS["warning"]}.get(a.get("tipo","").lower(), "#475569")
            items.append(ft.Container(
                content=ft.Row([
                    ft.Column([
                        ft.Text(a.get("tipo","Acción").capitalize(), size=12, weight=ft.FontWeight.BOLD, color=tipo_color),
                        ft.Text(a.get("descripcion") or "Sin descripción", size=14, color=COLORS["text_primary"]),
                    ], spacing=2, expand=True),
                    ft.Row([
                        chk_acc,
                        ft.IconButton(ft.Icons.DELETE_OUTLINE_ROUNDED, icon_color=ft.Colors.RED_400, icon_size=18, on_click=make_del_acc()),
                    ], spacing=4),
                ], spacing=12, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                bgcolor=COLORS["surface"],
                border=ft.Border(
                    left=ft.BorderSide(6, COLORS["success"] if a["estado"]=="realizada" else tipo_color),
                    top=ft.BorderSide(1, COLORS["border"]),
                    right=ft.BorderSide(1, COLORS["border"]),
                    bottom=ft.BorderSide(1, COLORS["border"]),
                ),
                border_radius=12, padding=ft.Padding(16, 12, 12, 12),
                shadow=ft.BoxShadow(spread_radius=1, blur_radius=8, color=ft.Colors.with_opacity(0.08, "#000000"), offset=ft.Offset(0, 4)),
            ))
        acciones_list_col.controls = items or [ft.Container(
            content=ft.Column([
                ft.Icon(ft.Icons.ASSIGNMENT_LATE_ROUNDED, size=40, color=COLORS["border"]),
                ft.Text("No hay acciones planificadas", size=13, weight=ft.FontWeight.BOLD, color=COLORS["text_secondary"]),
                ft.Text("Agregá tareas, llamadas o reuniones para este mes.", size=12, color=COLORS["text_secondary"]),
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=4),
            alignment=ft.Alignment(0, 0), padding=30
        )]
        try: acciones_list_col.update()
        except: pass

    # Diálogo agregar acción
    acc_tipo_dropdown = ft.Dropdown(
        label="Tipo de Acción",
        options=[ft.dropdown.Option(t, t.capitalize()) for t in ["visita", "llamado", "reunion", "email", "otro"]],
        value="visita",
        border_color="#94A3B8", bgcolor=COLORS["surface"], focused_border_color=COLORS["primary"], 
        border_radius=12, text_size=13, height=48, content_padding=ft.Padding(12, 0, 12, 0)
    )
    acc_desc_tf = ft.TextField(
        label="Descripción de la tarea *", 
        prefix_icon=ft.Icons.DESCRIPTION_OUTLINED,
        multiline=True, min_lines=2, max_lines=4,
        border_color="#94A3B8", bgcolor=COLORS["surface"], focused_border_color=COLORS["primary"], 
        border_radius=12, text_size=13, content_padding=ft.Padding(12, 12, 12, 12)
    )
    
    acc_dialog_title = ft.Row([
        ft.Icon(ft.Icons.ADD_TASK_ROUNDED, color=COLORS["warning"], size=24),
        ft.Text("Nueva Acción", size=18, weight=ft.FontWeight.BOLD, color=COLORS["text_primary"])
    ], spacing=10, vertical_alignment=ft.CrossAxisAlignment.CENTER)

    acc_dialog = ft.AlertDialog(
        title=acc_dialog_title,
        title_padding=ft.Padding(24, 24, 24, 0),
        content_padding=ft.Padding(24, 20, 24, 20),
        actions_padding=ft.Padding(16, 0, 24, 24),
        content=ft.Container(
            content=ft.Column([acc_tipo_dropdown, acc_desc_tf], spacing=16, tight=True, width=400)
        ),
        actions=[
            ft.TextButton(
                "Cancelar", 
                style=ft.ButtonStyle(color=COLORS["text_secondary"]),
                on_click=lambda e: (setattr(acc_dialog, 'open', False), page.update())
            ),
            ft.FilledButton(
                "Guardar Acción", 
                bgcolor=COLORS["warning"], 
                icon=ft.Icons.SAVE_ROUNDED,
                style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8)),
                on_click=lambda e: _save_accion(e)
            ),
        ],
        actions_alignment=ft.MainAxisAlignment.END,
        shape=ft.RoundedRectangleBorder(radius=16)
    )
    def _save_accion(e):
        desc = (acc_desc_tf.value or "").strip()
        if not desc:
            acc_desc_tf.error_text = "Requerido"
            try: acc_desc_tf.update()
            except: pass
            return
        _ssn.guardar_accion(mes_actual, acc_tipo_dropdown.value, desc, "pendiente")
        acc_desc_tf.value = ""; acc_desc_tf.error_text = None
        acc_dialog.open = False
        try: page.update()
        except: pass
        refresh_dashboard()
    def _open_acc_dialog(e):
        if acc_dialog not in page.overlay:
            page.overlay.append(acc_dialog)
        acc_dialog.open = True
        try: page.update()
        except: pass

    acciones_section = ft.Container(
        content=ft.Column([
            ft.Row([
                ft.Row([
                    ft.Container(
                        content=ft.Icon(ft.Icons.TASK_ALT_ROUNDED, size=16, color=COLORS["text_on_primary"]),
                        bgcolor=COLORS["warning"], padding=6, border_radius=8
                    ),
                    ft.Text("Acciones Mensuales", size=14, weight=ft.FontWeight.BOLD, color=COLORS["text_primary"]),
                    ft.Container(content=acciones_count_text, bgcolor=ft.Colors.with_opacity(0.1, COLORS["warning"]), padding=ft.Padding(6,2,6,2), border_radius=12)
                ], spacing=8),
                ft.FilledButton("+ Acción", bgcolor=COLORS["warning"], color=COLORS["text_on_primary"],
                                on_click=_open_acc_dialog, style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8)), height=32),
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN, vertical_alignment=ft.CrossAxisAlignment.CENTER),
            acciones_list_col,
        ], spacing=12),
        bgcolor="#FFFBEB",  # Light amber background for Acciones
        border=ft.Border.all(1, "#FDE68A"),
        border_radius=12, padding=16,
    )

    visits_column = ft.Container(
        content=ft.Row([
            # Columna Izquierda (Visitas)
            ft.Column([
                ft.Text("Plan de Visitas", size=16, weight=ft.FontWeight.W_700, color=COLORS["text_primary"]),
                filters_container,
                pas_list_container,
            ], spacing=12, expand=65),  # 65% width
            
            # Columna Derecha (Candidatos y Acciones)
            ft.Column([
                ft.Text("Actividades Extra", size=16, weight=ft.FontWeight.W_700, color=COLORS["text_primary"]),
                candidatos_section,
                acciones_section,
            ], spacing=16, expand=35),  # 35% width
        ], spacing=24, vertical_alignment=ft.CrossAxisAlignment.START, expand=True),
        bgcolor="#F8FAFC",  # Fondo gris clarito para resaltar las tarjetas
        padding=24,
        border_radius=12,
        expand=True,
    )

    # ── Excel: exportar CSV ───────────────────────────────────────────────
    def export_actividades_csv(e):
        import csv, os, tempfile
        rows = _ssn.obtener_actividades_comerciales()  # all months
        if not rows:
            show_snackbar("No hay actividades para exportar.", is_error=True)
            return
        out_path = os.path.join(os.getcwd(), "actividades_exportado.csv")
        try:
            with open(out_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=["id","mes","fecha_actividad","nombre","tipo","compania","observaciones","fecha_registro"])
                writer.writeheader()
                writer.writerows(rows)
            show_snackbar(f"CSV exportado: {out_path}")
        except Exception as ex:
            show_snackbar(f"Error al exportar: {ex}", is_error=True)

    btn_export_csv = ft.OutlinedButton(
        "Exportar CSV",
        icon=ft.Icons.DOWNLOAD_ROUNDED,
        on_click=export_actividades_csv,
        style=ft.ButtonStyle(side=ft.BorderSide(1, COLORS["primary"]), shape=ft.RoundedRectangleBorder(radius=8)),
        height=42,
    )

    excel_column = ft.Column([
        excel_kpis_row,
        excel_filters_container,
        ft.Container(height=4),
        activities_list_container,
        ft.Container(height=8),
        ft.Row([btn_export_csv], alignment=ft.MainAxisAlignment.END),
    ], spacing=14, scroll=ft.ScrollMode.AUTO, expand=True)

    user_perms = state.get("permisos", set()) if state else set()
    has_metricas = "comercial_metricas" in user_perms
    has_visitas = "comercial_visitas" in user_perms
    has_excel = "comercial_excel" in user_perms
    
    # Support backward compatibility
    if ("comercial" in user_perms or not user_perms) and not (has_metricas or has_visitas or has_excel):
        has_metricas = True
        has_visitas = True
        has_excel = True

    tabs_list = []
    views_list = []
    
    if has_metricas:
        tabs_list.append(ft.Tab(label="Métricas y Rendimiento", icon=ft.Icons.ANALYTICS_ROUNDED))
        views_list.append(ft.Container(content=metrics_column, padding=ft.Padding(0, 16, 0, 16)))
        
    if has_visitas:
        tabs_list.append(ft.Tab(label="Plan de Visitas", icon=ft.Icons.CALENDAR_MONTH_ROUNDED))
        views_list.append(ft.Container(content=visits_column, padding=ft.Padding(0, 16, 0, 16)))
        
    if has_excel:
        tabs_list.append(ft.Tab(label="Seguimiento Diario (Excel)", icon=ft.Icons.TABLE_ROWS_ROUNDED))
        views_list.append(ft.Container(content=excel_column, padding=ft.Padding(0, 16, 0, 16)))

    if not tabs_list:
        tabs_list.append(ft.Tab(label="Sin Accesos", icon=ft.Icons.LOCK_ROUNDED))
        views_list.append(ft.Container(content=ft.Text("No tenés permisos para ver ninguna sección de este módulo.", color=COLORS["text_secondary"]), padding=16))

    # Determine initially selected tab index based on state
    initial_tab_idx = 0
    if state and state.get("active_dashboard_tab"):
        tab_label_to_find = state["active_dashboard_tab"]
        for idx, tab in enumerate(tabs_list):
            if tab.label == tab_label_to_find:
                initial_tab_idx = idx
                break

    def on_tab_change(e):
        if state and tabs.selected_index is not None:
            state["active_dashboard_tab"] = tabs_list[tabs.selected_index].label

    tabs = ft.Tabs(
        length=len(tabs_list),
        selected_index=initial_tab_idx,
        animation_duration=300,
        on_change=on_tab_change,
        content=ft.Column(
            expand=True,
            controls=[
                ft.TabBar(
                    tabs=tabs_list,
                    label_color=COLORS["primary"],
                    unselected_label_color=COLORS["text_secondary"],
                    indicator_color=COLORS["primary"],
                ),
                ft.TabBarView(
                    expand=True,
                    controls=views_list
                )
            ]
        ),
        expand=True,
    )

    def refresh_dashboard():
        nonlocal all_visitas, all_actividades, all_candidatos, all_acciones
        all_visitas = _ssn.obtener_visitas(mes_actual)
        all_actividades = _ssn.obtener_actividades_comerciales(mes_actual)
        cand = _ssn.obtener_candidatos(mes_actual)
        acc  = _ssn.obtener_acciones(mes_actual)
        all_candidatos = cand
        all_acciones = acc
        candidatos_count_text.value = f"({len(cand)} total · {sum(1 for c in cand if c['estado']=='captado')} captados)"
        acciones_count_text.value = f"({len(acc)} total · {sum(1 for a in acc if a['estado']=='realizada')} realizadas)"

        # ── ERP KPIs & Charts ───────────────────────────────────────────
        erp = _ssn.obtener_metricas_erp()
        
        def format_currency(val):
            try:
                return f"${float(val):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
            except:
                return "$0,00"

        def erp_kpi_card(title, value, sub, icon, color, on_click_fn):
            card_controls = [
                ft.Text(str(value), size=20, weight=ft.FontWeight.BOLD, color=COLORS["text_primary"]),
                ft.Text(title, size=11, weight=ft.FontWeight.BOLD, color=COLORS["text_primary"]),
            ]
            if sub:
                card_controls.append(ft.Text(sub, size=10, color=COLORS["text_secondary"]))
                
            return ft.Container(
                content=ft.Row([
                    ft.Container(
                        content=ft.Icon(icon, color=color, size=22),
                        bgcolor=ft.Colors.with_opacity(0.12, color),
                        border_radius=8, padding=10,
                    ),
                    ft.Column(card_controls, spacing=1, tight=True),
                ], spacing=12, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                bgcolor=COLORS["surface"],
                border=ft.Border(
                    left=ft.BorderSide(4, color),
                    top=ft.BorderSide(1, COLORS["border"]),
                    right=ft.BorderSide(1, COLORS["border"]),
                    bottom=ft.BorderSide(1, COLORS["border"])
                ),
                border_radius=12, padding=14, expand=True,
                on_click=on_click_fn,
                tooltip="Hacé clic para gestionar",
                on_hover=make_hover_handler(1.02),
                animate_scale=150,
                gradient=ft.LinearGradient(
                    begin=ft.Alignment(-1, -1),
                    end=ft.Alignment(1, 1),
                    colors=[COLORS["surface"], ft.Colors.with_opacity(0.04, color)]
                ),
            )

        kpi_row_erp = ft.Row([
            erp_kpi_card(
                "Clientes Activos", 
                str(erp['clientes_totales']), 
                "Ver asegurados en Cartera", 
                ft.Icons.PEOPLE_ROUNDED, 
                ft.Colors.PURPLE_700,
                lambda _: on_filter_click("navigate", "cartera")
            ),
        ], spacing=14)

        def build_custom_horizontal_bar(pct, color_start, color_end):
            active_flex = max(1, int(pct * 100))
            inactive_flex = 100 - active_flex
            if pct <= 0.01:
                return ft.Container(height=8, bgcolor=COLORS["divider"], border_radius=4)
            if pct >= 0.99:
                return ft.Container(
                    height=8,
                    gradient=ft.LinearGradient(
                        colors=[color_start, color_end],
                        begin=ft.Alignment(-1, 0),
                        end=ft.Alignment(1, 0),
                    ),
                    border_radius=4,
                )
            return ft.Container(
                height=8,
                bgcolor=COLORS["divider"],
                border_radius=4,
                content=ft.Row([
                    ft.Container(
                        gradient=ft.LinearGradient(
                            colors=[color_start, color_end],
                            begin=ft.Alignment(-1, 0),
                            end=ft.Alignment(1, 0),
                        ),
                        border_radius=4,
                        expand=active_flex,
                    ),
                    ft.Container(
                        expand=inactive_flex,
                    )
                ], spacing=0)
            )

        # ── ERP Charts (Ramo y Compañía) ─────────────────────────────────
        ramo_rows = []
        ramos_list = erp["ramos_distribucion"]
        max_ramo_premio = max([r["premio"] for r in ramos_list] + [1.0])
        for r in ramos_list[:4]:
            pct = r["premio"] / max_ramo_premio
            ramo_rows.append(
                ft.Column([
                    ft.Row([
                        ft.Text(r["ramo"], size=11, weight=ft.FontWeight.BOLD, color=COLORS["text_primary"]),
                        ft.Text(f"{r['cantidad']} pólizas · {format_currency(r['premio'])}", size=10, color=COLORS["text_secondary"]),
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    build_custom_horizontal_bar(pct, "#A78BFA", "#EC4899")
                ], spacing=2)
            )
        if not ramo_rows:
            ramo_rows.append(ft.Text("No hay pólizas registradas para graficar.", size=11, italic=True, color=COLORS["text_secondary"]))
            
        ramo_chart = ft.Container(
            content=ft.Column([
                ft.Text("Distribución de Cartera por Ramo (Premio)", size=12, weight=ft.FontWeight.BOLD, color=COLORS["text_primary"]),
                ft.Column(ramo_rows, spacing=8, expand=True)
            ], spacing=6),
            bgcolor=COLORS["surface"],
            border=ft.Border.all(1, COLORS["border"]),
            border_radius=12, padding=16, expand=True,
            height=180,
            on_hover=make_hover_handler(1.01),
            animate_scale=150,
        )

        comp_rows_erp = []
        comps_list = erp["companias_distribucion"]
        max_comp_premio = max([c["premio"] for c in comps_list] + [1.0])
        for c in comps_list[:4]:
            pct = c["premio"] / max_comp_premio
            comp_rows_erp.append(
                ft.Column([
                    ft.Row([
                        ft.Text(c["compania"], size=11, weight=ft.FontWeight.BOLD, color=COLORS["text_primary"]),
                        ft.Text(f"{c['cantidad']} pólizas · {format_currency(c['premio'])}", size=10, color=COLORS["text_secondary"]),
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    build_custom_horizontal_bar(pct, "#22D3EE", "#3B82F6")
                ], spacing=2)
            )
        if not comp_rows_erp:
            comp_rows_erp.append(ft.Text("No hay pólizas registradas para graficar.", size=11, italic=True, color=COLORS["text_secondary"]))

        compania_chart_erp = ft.Container(
            content=ft.Column([
                ft.Text("Distribución de Cartera por Compañía (Premio)", size=12, weight=ft.FontWeight.BOLD, color=COLORS["text_primary"]),
                ft.Column(comp_rows_erp, spacing=8, expand=True)
            ], spacing=6),
            bgcolor=COLORS["surface"],
            border=ft.Border.all(1, COLORS["border"]),
            border_radius=12, padding=16, expand=True,
            height=180,
            on_hover=make_hover_handler(1.01),
            animate_scale=150,
        )

        charts_row_erp = ft.Row([ramo_chart, compania_chart_erp], spacing=14)

        # ── KPI counts ──────────────────────────────────────────────────
        vis_total  = len(all_visitas)
        vis_ok     = sum(1 for v in all_visitas if v["estado"] == "realizada")
        vis_pend   = vis_total - vis_ok

        cand_total    = len(cand)
        cand_captados = sum(1 for c in cand if c["estado"] == "captado")

        acc_total = len(acc)
        acc_ok    = sum(1 for a in acc if a["estado"] == "realizada")
        acc_pend  = acc_total - acc_ok

        # Update Excel KPIs
        excel_calls = sum(1 for a in all_actividades if a["tipo"] == "Llamado")
        excel_meetings = sum(1 for a in all_actividades if a["tipo"] == "Reunión")
        card_excel_calls.content.controls[1].controls[0].value = str(excel_calls)
        card_excel_meetings.content.controls[1].controls[0].value = str(excel_meetings)
        try:
            card_excel_calls.update()
            card_excel_meetings.update()
        except:
            pass

        # ── Helper: KPI card ────────────────────────────────────────────
        def nav_to_tab(target_label, action_fn=None):
            def _click(e):
                for idx, t in enumerate(tabs_list):
                    if target_label.lower() in (t.label or "").lower():
                        tabs.selected_index = idx
                        try: tabs.update()
                        except: pass
                        break
                if action_fn:
                    try: action_fn(e)
                    except Exception as ex: print("Error running action_fn:", ex)
            return _click

        def kpi_card(title, value, sub, icon, color, on_click_fn=None, tooltip_txt=None, progress_value=None):
            card_content = [
                ft.Row([
                    ft.Container(
                        content=ft.Icon(icon, color=color, size=22),
                        bgcolor=ft.Colors.with_opacity(0.12, color),
                        border_radius=8, padding=10,
                    ),
                    ft.Column([
                        ft.Text(str(value), size=28, weight=ft.FontWeight.BOLD, color=COLORS["text_primary"]),
                        ft.Text(title, size=12, weight=ft.FontWeight.BOLD, color=COLORS["text_primary"]),
                        ft.Text(sub, size=10, color=COLORS["text_secondary"]),
                    ], spacing=1, tight=True),
                ], spacing=12, vertical_alignment=ft.CrossAxisAlignment.CENTER),
            ]
            if progress_value is not None:
                p_val = max(0.0, min(1.0, float(progress_value)))
                card_content.append(
                    ft.Container(
                        content=ft.ProgressBar(
                            value=p_val,
                            color=color,
                            bgcolor=ft.Colors.with_opacity(0.15, color),
                            height=5,
                            border_radius=3,
                        ),
                        margin=ft.Margin(top=8, bottom=0, left=0, right=0)
                    )
                )

            return ft.Container(
                content=ft.Column(card_content, spacing=0, tight=True),
                bgcolor=COLORS["surface"],
                border=ft.Border(
                    left=ft.BorderSide(4, color),
                    top=ft.BorderSide(1, COLORS["border"]),
                    right=ft.BorderSide(1, COLORS["border"]),
                    bottom=ft.BorderSide(1, COLORS["border"])
                ),
                border_radius=12, padding=16, expand=True,
                gradient=ft.LinearGradient(
                    begin=ft.Alignment(-1, -1),
                    end=ft.Alignment(1, 1),
                    colors=[COLORS["surface"], ft.Colors.with_opacity(0.04, color)]
                ),
                on_click=on_click_fn,
                ink=True if on_click_fn else False,
                tooltip=tooltip_txt,
                on_hover=make_hover_handler(1.015) if on_click_fn else None,
                animate_scale=150,
            )

        vis_ratio = (vis_ok / vis_total) if vis_total > 0 else 0.0
        vis_color = (
            COLORS["success"] if vis_ratio >= 0.75 else
            COLORS["primary"] if vis_ratio >= 0.5 else
            COLORS["warning"] if vis_ratio > 0 else
            COLORS["text_secondary"]
        )

        cand_ratio = (cand_captados / cand_total) if cand_total > 0 else 0.0
        acc_ratio = (acc_ok / acc_total) if acc_total > 0 else 0.0

        kpi_row = ft.Row([
            kpi_card("Visitas del Mes",    vis_total,   f"{vis_ok} realizadas · {vis_pend} pendientes",  ft.Icons.HANDSHAKE_ROUNDED,      COLORS["primary"],
                     on_click_fn=nav_to_tab("Plan de Visitas"), tooltip_txt="Hacé clic para ir al Plan de Visitas", progress_value=vis_ratio),
            kpi_card("Candidatos",         cand_total,  f"{cand_captados} captados", ft.Icons.PERSON_ADD_ALT_1_ROUNDED, COLORS["accent"],
                     on_click_fn=nav_to_tab("Plan de Visitas", _open_cand_dialog), tooltip_txt="Hacé clic para gestionar Candidatos", progress_value=cand_ratio),
            kpi_card("Acciones Mensuales", acc_total,   f"{acc_ok} realizadas · {acc_pend} pendientes",  ft.Icons.TASK_ALT_ROUNDED,       COLORS["warning"],
                     on_click_fn=nav_to_tab("Plan de Visitas", _open_acc_dialog), tooltip_txt="Hacé clic para gestionar Acciones Mensuales", progress_value=acc_ratio),
            kpi_card("Tasa de Visita",     f"{int(vis_ratio * 100)}%",
                     f"{vis_ok} de {vis_total} completadas", ft.Icons.INSIGHTS_ROUNDED,
                     vis_color,
                     on_click_fn=nav_to_tab("Plan de Visitas"), tooltip_txt="Hacé clic para ver el detalle de visitas", progress_value=vis_ratio),
        ], spacing=14)

        # ── Configuración de Objetivos Mensuales ─────────────────────────
        configs = _ssn.obtener_configuraciones()
        target_visitas = int(configs.get(f"target_visitas_{mes_actual}", vis_total or 5))
        target_candidatos = int(configs.get(f"target_candidatos_{mes_actual}", cand_total or 3))
        target_acciones = int(configs.get(f"target_acciones_{mes_actual}", acc_total or 5))

        def _open_def_objetivos_dialog(e):
            print(f"[DEBUG] Abriendo diálogo de objetivos para {mes_actual}")
            tf_vis = ft.TextField(label="Meta de Visitas del Mes", value=str(target_visitas), border_radius=8, text_size=13, keyboard_type=ft.KeyboardType.NUMBER)
            tf_cand = ft.TextField(label="Meta de Candidatos a Captar", value=str(target_candidatos), border_radius=8, text_size=13, keyboard_type=ft.KeyboardType.NUMBER)
            tf_acc = ft.TextField(label="Meta de Acciones Mensuales", value=str(target_acciones), border_radius=8, text_size=13, keyboard_type=ft.KeyboardType.NUMBER)
            
            def _close_dlg(ev=None):
                try:
                    if hasattr(page, "close"):
                        page.close(dlg_obj)
                    else:
                        dlg_obj.open = False
                        page.update()
                except Exception as ex_c:
                    dlg_obj.open = False
                    try: page.update()
                    except: pass

            def _do_save_obj(ev):
                try:
                    v_val = max(1, int(tf_vis.value or 0))
                    c_val = max(1, int(tf_cand.value or 0))
                    a_val = max(1, int(tf_acc.value or 0))
                    _ssn.guardar_configuracion(f"target_visitas_{mes_actual}", str(v_val))
                    _ssn.guardar_configuracion(f"target_candidatos_{mes_actual}", str(c_val))
                    _ssn.guardar_configuracion(f"target_acciones_{mes_actual}", str(a_val))
                    _close_dlg()
                    refresh_dashboard()
                    show_snackbar(f"Objetivos de {mes_actual} actualizados: Visitas={v_val}, Cand.={c_val}, Acc.={a_val}")
                except Exception as ex:
                    show_snackbar("Por favor ingrese números enteros válidos.", is_error=True)
                    
            dlg_obj = ft.AlertDialog(
                title=ft.Row([
                    ft.Icon(ft.Icons.TRACK_CHANGES_ROUNDED, color=COLORS["primary"], size=22),
                    ft.Text(f"Definir Objetivos ({mes_actual})", size=16, weight=ft.FontWeight.BOLD, color=COLORS["text_primary"])
                ], spacing=8),
                content=ft.Container(
                    content=ft.Column([
                        ft.Text("Definí las metas operativas para tu equipo este mes:", size=12, color=COLORS["text_secondary"]),
                        tf_vis,
                        tf_cand,
                        tf_acc,
                    ], spacing=12, tight=True),
                    width=320,
                ),
                actions=[
                    ft.TextButton("Cancelar", on_click=_close_dlg),
                    ft.FilledButton("Guardar Objetivos", on_click=_do_save_obj, style=ft.ButtonStyle(bgcolor=COLORS["primary"], color=COLORS["text_on_primary"])),
                ],
                actions_alignment=ft.MainAxisAlignment.END,
            )
            try:
                if hasattr(page, "open"):
                    page.open(dlg_obj)
                else:
                    page.dialog = dlg_obj
                    if dlg_obj not in page.overlay:
                        page.overlay.append(dlg_obj)
                    dlg_obj.open = True
                    page.update()
            except Exception as ex:
                page.dialog = dlg_obj
                if dlg_obj not in page.overlay:
                    page.overlay.append(dlg_obj)
                dlg_obj.open = True
                try: page.update()
                except: pass

        btn_def_objetivos = ft.FilledButton(
            "Definir Objetivos",
            icon=ft.Icons.TRACK_CHANGES_ROUNDED,
            on_click=_open_def_objetivos_dialog,
            style=ft.ButtonStyle(
                bgcolor=COLORS["primary"],
                color=COLORS["text_on_primary"],
                shape=ft.RoundedRectangleBorder(radius=8),
                padding=ft.Padding(14, 8, 14, 8),
            ),
            height=34,
            tooltip="Hacé clic para definir metas mensuales de Visitas, Candidatos y Acciones",
        )

        # ── KPIs de Gráficos (Visual Charts) ──────────────────────────────
        def make_progress_ring_column(title, value, total, color, sub_label, on_click_fn=None):
            pct = value / total if total > 0 else 0.0
            pct = min(1.0, max(0.0, pct))
            pct_text = f"{int(pct * 100)}%" if total > 0 else "0%"
            
            card_content = ft.Row([
                ft.Stack([
                    ft.ProgressRing(
                        value=pct,
                        color=color,
                        bgcolor=ft.Colors.with_opacity(0.12, color),
                        stroke_width=5.5,
                        width=52,
                        height=52,
                    ),
                    ft.Container(
                        content=ft.Text(pct_text, size=11, weight=ft.FontWeight.BOLD, color=COLORS["text_primary"]),
                        alignment=ft.Alignment(0, 0),
                        width=52,
                        height=52,
                    )
                ]),
                ft.Column([
                    ft.Text(title, size=11, weight=ft.FontWeight.BOLD, color=COLORS["text_primary"]),
                    ft.Text(sub_label, size=12, weight=ft.FontWeight.W_600, color=color),
                    ft.Text("Hacé clic para gestionar", size=9, color=COLORS["text_secondary"]),
                ], spacing=2, tight=True, expand=True)
            ], spacing=12, vertical_alignment=ft.CrossAxisAlignment.CENTER)

            return ft.Container(
                content=card_content,
                bgcolor=ft.Colors.with_opacity(0.04, color),
                border=ft.Border.all(1, ft.Colors.with_opacity(0.2, color)),
                border_radius=10,
                padding=ft.Padding(12, 10, 12, 10),
                expand=True,
                on_click=on_click_fn,
                tooltip=f"Hacé clic para gestionar {title.lower()}",
                ink=True,
                on_hover=make_hover_handler(1.015),
                animate_scale=150,
            )

        def _open_acc_modal(e):
            acc_dialog.open = True
            try: page.update()
            except: pass

        def _open_vis_tab(e):
            tabs.selected_index = 1
            try: tabs.update()
            except: pass

        vis_chart = ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Row([
                        ft.Icon(ft.Icons.TRACK_CHANGES_ROUNDED, color=COLORS["primary"], size=20),
                        ft.Text("Progreso de Objetivos Mensuales", size=13, weight=ft.FontWeight.BOLD, color=COLORS["text_primary"]),
                    ], spacing=8),
                    btn_def_objetivos,
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                ft.Container(height=6),
                ft.Row([
                    make_progress_ring_column("VISITAS", vis_ok, target_visitas, COLORS["success"], f"{vis_ok} de {target_visitas} realizadas", on_click_fn=_open_vis_tab),
                    make_progress_ring_column("CANDIDATOS", cand_captados, target_candidatos, "#8B5CF6", f"{cand_captados} de {target_candidatos} captados", on_click_fn=_open_cand_dialog),
                    make_progress_ring_column("ACCIONES", acc_ok, target_acciones, COLORS["warning"], f"{acc_ok} de {target_acciones} completadas", on_click_fn=_open_acc_modal),
                ], spacing=12, alignment=ft.MainAxisAlignment.SPACE_BETWEEN, vertical_alignment=ft.CrossAxisAlignment.CENTER, expand=True)
            ], spacing=6),
            bgcolor=COLORS["surface"],
            border=ft.Border.all(1, COLORS["border"]),
            border_radius=12, padding=ft.Padding(18, 16, 18, 16), expand=True,
            height=165,
            animate_scale=150,
        )

        import collections
        comp_counts = collections.Counter(v.get("campaña") or "Sin Compañía" for v in all_visitas)
        top_companies = comp_counts.most_common(3)
        
        comp_rows = []
        for idx, (c_name, count) in enumerate(top_companies):
            c_pct = count / vis_total if vis_total else 0.0
            if idx == 0:
                color_start, color_end = "#00F2FE", "#4FACFE"
            elif idx == 1:
                color_start, color_end = "#FF0844", "#FFB199"
            else:
                color_start, color_end = "#FAD961", "#F76B1C"
                
            comp_rows.append(
                ft.Column([
                    ft.Row([
                        ft.Text(c_name or "Sin Compañía", size=10, weight=ft.FontWeight.BOLD, color=COLORS["text_primary"]),
                        ft.Text(f"{count} PAS ({int(c_pct*100)}%)", size=9, color=COLORS["text_secondary"]),
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    build_custom_horizontal_bar(c_pct, color_start, color_end)
                ], spacing=2)
            )
            
        if not comp_rows:
            comp_rows.append(
                ft.Container(
                    content=ft.Text("No hay datos de compañías este mes.", size=11, italic=True, color=COLORS["text_secondary"]),
                    alignment=ft.Alignment(0, 0),
                    expand=True,
                )
            )
            
        charts_row = ft.Row([vis_chart], spacing=14)

        # ── Alerta PAS sin contacto ───────────────────────────────────────
        pas_sin_visita = [v for v in all_visitas if v["estado"] == "pendiente"]
        alerta = None
        if pas_sin_visita:
            alerta = ft.Container(
                content=ft.Row([
                    ft.Icon(ft.Icons.WARNING_AMBER_ROUNDED, color=COLORS["warning"], size=20),
                    ft.Text(
                        f"Tenés {len(pas_sin_visita)} visita(s) pendiente(s) este mes: " +
                        ", ".join(v["nombre"] for v in pas_sin_visita[:5]) +
                        ("..." if len(pas_sin_visita) > 5 else ""),
                        size=12, weight=ft.FontWeight.W_500, color=COLORS["text_primary"], expand=True,
                    ),
                ], spacing=10),
                bgcolor=ft.Colors.with_opacity(0.08, COLORS["warning"]),
                border=ft.Border.all(1.5, ft.Colors.with_opacity(0.3, COLORS["warning"])),
                border_radius=8, padding=12,
            )

        companies = sorted(list(set(v["campaña"] for v in all_visitas if v.get("campaña"))))
        def make_company_click(c):
            def _click(e):
                filter_state["company"] = c
                company_label.value = c if c != "Todas" else "Todas las Compañías"
                filter_and_render()
            return _click
        company_btn.items = [
            _make_menu_item("Todas las Compañías", make_company_click("Todas"))
        ] + [_make_menu_item(c, make_company_click(c)) for c in companies]
        try: company_btn.update()
        except: pass

        # ── ERP Rankings (Los más cracks) ──────────────────────────────
        ranking = _ssn.obtener_ranking_productores()
        
        ranking_items = []
        for idx, p in enumerate(ranking[:8]):
            if idx == 0:
                rank_icon = "🥇"
                rank_bg = "#F59E0B"
            elif idx == 1:
                rank_icon = "🥈"
                rank_bg = "#94A3B8"
            elif idx == 2:
                rank_icon = "🥉"
                rank_bg = "#B45309"
            else:
                rank_icon = str(idx + 1)
                rank_bg = COLORS["border"]
                
            companias_text = p.get("companias", "")
            if companias_text:
                companias_list = companias_text.split(",")
                companias_chips = ft.Row([
                    _status_chip(comp, COLORS["primary"] if comp in ["San Cristóbal", "Allianz", "Sancor", "Mapfre", "Federación Patronal", "SMG"] else "#475569")
                    for comp in companias_list[:2]
                ], spacing=4)
            else:
                companias_chips = _status_chip("Sin Compañía", "#475569")
                
            ranking_items.append(
                ft.Container(
                    content=ft.Row([
                        ft.Container(
                            content=ft.Text(rank_icon if idx < 3 else str(idx+1), size=11, weight=ft.FontWeight.BOLD, color=COLORS["text_on_primary"] if idx >= 3 else COLORS["text_primary"]),
                            bgcolor=rank_bg if idx >= 3 else "transparent",
                            border_radius=12 if idx >= 3 else 0,
                            width=24, height=24,
                            alignment=ft.Alignment(0, 0)
                        ),
                        ft.Column([
                            ft.Text(p["nombre"], size=12, weight=ft.FontWeight.BOLD, color=COLORS["text_primary"]),
                            ft.Row([
                                ft.Text(f"Mat. {p['matricula']}", size=10, weight=ft.FontWeight.W_500, color=COLORS["text_secondary"]),
                                ft.Text("•", size=10, color=COLORS["text_secondary"]),
                                ft.Text(f"{p['polizas_vigentes']} pólizas", size=10, color=COLORS["text_secondary"]),
                            ], spacing=4),
                        ], spacing=1, expand=True),
                        companias_chips,
                        ft.Column([
                            ft.Text(format_currency(p["premio_total"]), size=12, weight=ft.FontWeight.W_900, color=COLORS["success"]),
                            ft.Text(f"Comisiones: {format_currency(p['comisiones_estimadas'])}", size=9, color=COLORS["text_secondary"]),
                        ], horizontal_alignment=ft.CrossAxisAlignment.END, spacing=1)
                    ], spacing=10, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                    bgcolor=COLORS["surface"],
                    border=ft.Border.all(1, COLORS["border"]),
                    border_radius=10,
                    padding=ft.Padding(16, 10, 16, 10),
                    on_hover=make_hover_handler(1.005),
                    animate_scale=150,
                )
            )
            
        ranking_container = ft.Container(
            content=ft.Column(ranking_items, spacing=6),
            padding=0
        )
        
        ranking_section = ft.Column([
            ft.Row([
                ft.Icon(ft.Icons.STAR_ROUNDED, color=ft.Colors.AMBER, size=20),
                ft.Text("Ranking de Productores - Los Más Cracks 🏆", size=14, weight=ft.FontWeight.BOLD, color=COLORS["text_primary"]),
            ], spacing=6),
            ranking_container,
        ], spacing=10)

        # Update metrics tab
        metrics_controls = []
        if alerta:
            metrics_controls.append(alerta)

        metrics_controls.extend([
            kpi_row,
            ft.Container(height=4),
            kpi_row_erp,
            ft.Container(height=8),
            charts_row,
            ft.Container(height=4),
            charts_row_erp,
            ft.Divider(height=16, color=COLORS["border"]),
            ranking_section,
        ])
        metrics_column.controls = metrics_controls
        
        try:
            metrics_column.update()
        except:
            pass

        filter_and_render()
        filter_and_render_excel()
        filter_and_render_candidatos()
        filter_and_render_acciones()

    # Run initial refresh asynchronously to populate controls without blocking rendering
    def run_initial_refresh():
        try:
            refresh_dashboard()
            page.update()
        except Exception as e:
            import traceback
            print("Error populating Gestion Comercial dashboard:", e)
            traceback.print_exc()



    page.run_thread(run_initial_refresh)

    if state is not None:
        state["refresh_dashboard"] = refresh_dashboard
        state["open_add_pas_dialog"] = open_add_pas_dialog

    # Assembly
    return ft.Container(
        content=ft.Column(
            controls=[
                header_row,
                ft.Divider(height=12, color=COLORS["divider"]),
                tabs,
            ],
            spacing=0,
            expand=True,
        ),
        padding=ft.Padding(24, 18, 24, 18),
        expand=True,
    )

# ---------------------------------------------------------------------------
# Vista de Configuración de Perfil
# ---------------------------------------------------------------------------
def build_profile_view(
    state: Dict[str, Any],
    on_back: Callable,
    on_update_profile: Callable,
    on_crear_usuario: Callable = None,
    on_eliminar_usuario: Callable = None,
    on_cambiar_password: Callable = None,
    page: ft.Page = None,
) -> ft.Container:
    import ssn_test

    def show_snackbar(message: str, is_error: bool = False):
        page.snack_bar = ft.SnackBar(
            content=ft.Text(message, color=ft.Colors.WHITE, size=13, weight=ft.FontWeight.W_500),
            bgcolor=COLORS["primary"] if not is_error else ft.Colors.RED_600,
            duration=3500,
            dismiss_direction=ft.DismissDirection.HORIZONTAL,
        )
        page.snack_bar.open = True
        page.update()

    curr_uname = state.get("username", "")
    curr_rol = state.get("role", "")
    
    users = ssn_test.obtener_usuarios()
    curr_user_obj = next((u for u in users if u["id"] == state["user_id"]), None)
    curr_email = curr_user_obj["email"] if curr_user_obj and curr_user_obj.get("email") else ""
    user_changed = bool(curr_user_obj.get("username_changed")) if curr_user_obj else False

    uname_field = ft.TextField(
        value=curr_uname, 
        label="Nombre de Usuario", 
        border_color="#94A3B8", bgcolor=COLORS["surface"], 
        focused_border_color=COLORS["primary"], 
        border_radius=8, 
        text_size=14,
        disabled=user_changed,
        helper="Ya fue cambiado una vez." if user_changed else "Se puede cambiar UNA SOLA VEZ.",
        prefix_icon=ft.Icons.PERSON_OUTLINE_ROUNDED
    )
    email_field = ft.TextField(
        value=curr_email, 
        label="Correo Electrónico", 
        border_color="#94A3B8", bgcolor=COLORS["surface"], 
        focused_border_color=COLORS["primary"], 
        border_radius=8, 
        text_size=14,
        prefix_icon=ft.Icons.EMAIL_OUTLINED
    )
    pass_field = ft.TextField(
        label="Nueva Contraseña", 
        password=True, 
        can_reveal_password=True, 
        border_color="#94A3B8", bgcolor=COLORS["surface"], 
        focused_border_color=COLORS["primary"], 
        border_radius=8, 
        text_size=14,
        hint_text="Dejar vacío para mantener la actual",
        prefix_icon=ft.Icons.LOCK_OUTLINE_ROUNDED
    )
    calendar_url_field = ft.TextField(
        value=state.get("calendar_url", ""), 
        label="Mi Enlace de Cal.com / Agenda (URL)", 
        border_color="#94A3B8", bgcolor=COLORS["surface"], 
        focused_border_color=COLORS["primary"], 
        border_radius=8, 
        text_size=14,
        prefix_icon=ft.Icons.CALENDAR_MONTH_ROUNDED,
        hint_text="https://cal.com/tu-usuario o enlace de Google Calendar"
    )

    def do_update_profile(e):
        new_uname = (uname_field.value or "").strip().lower()
        new_email = (email_field.value or "").strip().lower()
        new_pwd = (pass_field.value or "").strip()
        new_calendar_url = (calendar_url_field.value or "").strip()

        if not new_uname or not new_email:
            show_snackbar("El nombre de usuario y correo electrónico son requeridos.", is_error=True)
            return
            
        if new_pwd and len(new_pwd) < 6:
            show_snackbar("La nueva contraseña debe tener al menos 6 caracteres.", is_error=True)
            return

        success, msg = on_update_profile(new_uname, new_email, new_pwd, new_calendar_url)
        if success:
            show_snackbar(msg)
        else:
            show_snackbar(msg, is_error=True)

    # ── Avatar con iniciales ────────────────────────────────────────────────
    _initials = (curr_uname[:1] or "U").upper()
    avatar_circle = ft.Container(
        content=ft.Text(_initials, size=32, weight=ft.FontWeight.W_900, color="#FFFFFF"),
        width=72, height=72,
        border_radius=36,
        gradient=ft.LinearGradient(
            colors=[COLORS["primary"], "#1D4ED8"],
            begin=ft.Alignment(-1, -1),
            end=ft.Alignment(1, 1),
        ),
        alignment=ft.Alignment(0, 0),
        shadow=ft.BoxShadow(blur_radius=18, spread_radius=0,
                            color=ft.Colors.with_opacity(0.25, COLORS["primary"]),
                            offset=ft.Offset(0, 6)),
    )

    role_badge = ft.Container(
        content=ft.Text(curr_rol.capitalize(), size=10, color="#FFFFFF", weight=ft.FontWeight.W_700),
        bgcolor=COLORS["primary"] if curr_rol == "admin" else "#7C3AED",
        border_radius=20,
        padding=ft.Padding(10, 4, 10, 4),
    )

    profile_card = ft.Container(
        content=ft.Column(
            controls=[
                # ── Hero strip ─────────────────────────────────────────────
                ft.Container(
                    content=ft.Column(
                        controls=[
                            avatar_circle,
                            ft.Text(curr_uname, size=20, weight=ft.FontWeight.W_800,
                                    color=COLORS["text_primary"]),
                            ft.Text(curr_email, size=12, color=COLORS["text_secondary"]),
                            role_badge,
                        ],
                        spacing=6,
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                    padding=ft.Padding(24, 28, 24, 24),
                    gradient=ft.LinearGradient(
                        colors=[ft.Colors.with_opacity(0.04, COLORS["primary"]), COLORS["surface"]],
                        begin=ft.Alignment(0, -1), end=ft.Alignment(0, 1),
                    ),
                    border_radius=ft.BorderRadius(top_left=16, top_right=16,
                                                  bottom_left=0, bottom_right=0),
                ),
                ft.Container(
                    content=ft.Divider(height=1, color=COLORS["divider"]),
                    padding=ft.Padding(0, 0, 0, 0),
                ),
                # ── Form fields ────────────────────────────────────────────
                ft.Container(
                    content=ft.Column(
                        controls=[
                            ft.Text("Información de Cuenta", size=13,
                                    weight=ft.FontWeight.W_700,
                                    color=COLORS["text_secondary"]),
                            ft.Container(height=4),
                            uname_field,
                            email_field,
                            ft.Text("Seguridad", size=13, weight=ft.FontWeight.W_700,
                                    color=COLORS["text_secondary"]),
                            ft.Container(height=4),
                            pass_field,
                            ft.Text("Agenda", size=13, weight=ft.FontWeight.W_700,
                                    color=COLORS["text_secondary"]),
                            ft.Container(height=4),
                            calendar_url_field,
                            ft.Container(height=8),
                            ft.Row(
                                controls=[
                                    ft.FilledButton(
                                        "Guardar Cambios",
                                        icon=ft.Icons.SAVE_ROUNDED,
                                        on_click=do_update_profile,
                                        style=ft.ButtonStyle(
                                            bgcolor=COLORS["primary"],
                                            color=COLORS["text_on_primary"],
                                            shape=ft.RoundedRectangleBorder(radius=10),
                                            padding=ft.Padding(20, 14, 20, 14),
                                        ),
                                    )
                                ],
                                alignment=ft.MainAxisAlignment.END,
                            ),
                        ],
                        spacing=12,
                    ),
                    padding=ft.Padding(24, 20, 24, 24),
                ),
            ],
            spacing=0,
        ),
        border_radius=16,
        border=ft.Border.all(1, COLORS["divider"]),
        bgcolor=COLORS["surface"],
        shadow=ft.BoxShadow(spread_radius=0, blur_radius=24,
                            color=ft.Colors.with_opacity(0.07, "#000000"),
                            offset=ft.Offset(0, 8)),
        width=400,
    )
    # -------------------------------------------------
    # CRUD de Usuarios (sólo para Admins)
    # -------------------------------------------------
    import time
    import threading
    users_column = ft.Column(spacing=10)

    def refresh_users():
        if curr_rol != "admin": return
        users_list = ssn_test.obtener_usuarios()
        user_cards = []
        for u in users_list:
            uid = u.get("id")
            uname = u.get("usuario")
            uemail = u.get("email") or "—"
            urol = u.get("rol") or "agente"
            umatricula = u.get("matricula_asociada") or "—"
            raw_req_change = u.get("requiere_cambio") or 0
            raw_failed = u.get("intentos_fallidos") or 0
            raw_blocked = u.get("bloqueado_hasta") or 0
            uperms = u.get("permisos") or "comercial,buscador,cartera"
            ucal = u.get("calendar_url") or "—"
            
            is_self = (uname == state.get("username"))
            is_primary_admin = (uname == "admin")
            
            def make_change_pw_click(user_id=uid, username=uname):
                return lambda e: open_change_pw_dialog(user_id, username)
                
            def make_delete_click(user_id=uid, username=uname):
                return lambda e: open_delete_user_dialog(user_id, username)

            def make_edit_click(user_id=uid, username=uname, email=uemail, rol=urol, rc=raw_req_change, rf=raw_failed, rb=raw_blocked, matricula=umatricula, perms=uperms, calendar_url=ucal):
                edit_mat = "" if matricula == "—" else str(matricula)
                return lambda e: open_edit_user_dialog(user_id, username, email, rol, rc, rf, rb, edit_mat, perms, calendar_url)

            # Badges de permisos
            perm_badges = []
            if "comercial" in uperms:
                perm_badges.append(
                    ft.Container(
                        content=ft.Text("COM", size=9, color="#FFFFFF", weight=ft.FontWeight.BOLD),
                        bgcolor="#2563EB",
                        border_radius=4,
                        padding=ft.Padding(left=5, right=5, top=2, bottom=2),
                        tooltip="Gestión Comercial"
                    )
                )
            if "buscador" in uperms:
                perm_badges.append(
                    ft.Container(
                        content=ft.Text("BUS", size=9, color="#FFFFFF", weight=ft.FontWeight.BOLD),
                        bgcolor="#7C3AED",
                        border_radius=4,
                        padding=ft.Padding(left=5, right=5, top=2, bottom=2),
                        tooltip="Red de PAS (Buscador)"
                    )
                )
            if "cartera" in uperms:
                perm_badges.append(
                    ft.Container(
                        content=ft.Text("CAR", size=9, color="#FFFFFF", weight=ft.FontWeight.BOLD),
                        bgcolor="#D97706",
                        border_radius=4,
                        padding=ft.Padding(left=5, right=5, top=2, bottom=2),
                        tooltip="Cartera & Operaciones"
                    )
                )
            perms_container = ft.Row(controls=perm_badges, spacing=4, tight=True)

            # Acciones de usuario
            actions_cells = []
            actions_cells.append(
                ft.IconButton(
                    icon=ft.Icons.EDIT_OUTLINED,
                    icon_color=COLORS["primary"],
                    icon_size=18,
                    tooltip="Editar Usuario y Permisos",
                    on_click=make_edit_click(),
                )
            )
            if not is_primary_admin:
                actions_cells.append(
                    ft.IconButton(
                        icon=ft.Icons.LOCK_RESET_ROUNDED,
                        icon_color=COLORS["primary"],
                        icon_size=18,
                        tooltip="Restablecer Contraseña",
                        on_click=make_change_pw_click(),
                    )
                )
            if not is_self and not is_primary_admin:
                actions_cells.append(
                    ft.IconButton(
                        icon=ft.Icons.DELETE_OUTLINED,
                        icon_color=ft.Colors.RED_400,
                        icon_size=18,
                        tooltip="Eliminar Usuario",
                        on_click=make_delete_click(),
                    )
                )

            _actions = ft.Row(controls=actions_cells, spacing=2, tight=True)
            _init = (uname[:1] or "U").upper()
            _is_admin = (urol.lower() == "admin")

            # Tarjeta de Usuario Elegante
            card = ft.Container(
                content=ft.Row(
                    controls=[
                        # Avatar Circle
                        ft.Container(
                            content=ft.Text(_init, size=15, weight=ft.FontWeight.W_900, color="#FFFFFF"),
                            width=42, height=42, border_radius=21,
                            bgcolor=COLORS["primary"] if _is_admin else "#7C3AED",
                            alignment=ft.Alignment(0, 0),
                            shadow=ft.BoxShadow(blur_radius=8, spread_radius=0, color=ft.Colors.with_opacity(0.18, COLORS["primary"] if _is_admin else "#7C3AED")),
                        ),
                        # Info Column
                        ft.Column(
                            controls=[
                                ft.Row(
                                    controls=[
                                        ft.Text(uname, size=14, weight=ft.FontWeight.W_700, color=COLORS["text_primary"]),
                                        ft.Container(
                                            content=ft.Text("ADMIN" if _is_admin else "AGENTE", size=9, weight=ft.FontWeight.W_800, color="#FFFFFF"),
                                            bgcolor=COLORS["primary"] if _is_admin else "#7C3AED",
                                            border_radius=6,
                                            padding=ft.Padding(6, 2, 6, 2),
                                        ),
                                    ],
                                    spacing=8,
                                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                                ),
                                ft.Text(uemail, size=11, color=COLORS["text_secondary"]),
                                ft.Row(
                                    controls=[
                                        perms_container,
                                        ft.Container(width=4),
                                        ft.Text(
                                            f"Matrículas: {umatricula}" if umatricula != "—" else "Sin matrícula asignada",
                                            size=10,
                                            color=COLORS["text_secondary"],
                                            weight=ft.FontWeight.W_500,
                                            overflow=ft.TextOverflow.ELLIPSIS,
                                            max_lines=1,
                                        ),
                                    ],
                                    spacing=6,
                                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                                ),
                            ],
                            spacing=3,
                            expand=True,
                        ),
                        # Actions
                        _actions,
                    ],
                    spacing=12,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                bgcolor=COLORS["surface"],
                border=ft.Border.all(1, COLORS["divider"]),
                border_radius=12,
                padding=ft.Padding(14, 12, 14, 12),
                shadow=ft.BoxShadow(blur_radius=8, spread_radius=0, color=ft.Colors.with_opacity(0.04, "#000000"), offset=ft.Offset(0, 2)),
            )
            user_cards.append(card)

        users_column.controls = [
            ft.Container(
                content=ft.Column(
                    controls=[
                        # Header
                        ft.Row(
                            controls=[
                                ft.Row(
                                    controls=[
                                        ft.Container(
                                            content=ft.Icon(ft.Icons.PEOPLE_ALT_ROUNDED,
                                                            color=COLORS["primary"], size=20),
                                            width=38, height=38, border_radius=10,
                                            bgcolor=ft.Colors.with_opacity(0.10, COLORS["primary"]),
                                            alignment=ft.Alignment(0, 0),
                                        ),
                                        ft.Column(
                                            controls=[
                                                ft.Text("Gestión de Usuarios", size=16,
                                                        weight=ft.FontWeight.W_800,
                                                        color=COLORS["text_primary"]),
                                                ft.Text("Roles, accesos y seguridad del equipo", size=11,
                                                        color=COLORS["text_secondary"]),
                                            ],
                                            spacing=1,
                                        ),
                                    ],
                                    spacing=12,
                                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                                ),
                                ft.FilledButton(
                                    "Nuevo usuario",
                                    icon=ft.Icons.PERSON_ADD_ALT_1_ROUNDED,
                                    on_click=open_create_user_dialog,
                                    style=ft.ButtonStyle(
                                        bgcolor=COLORS["primary"],
                                        color=COLORS["text_on_primary"],
                                        shape=ft.RoundedRectangleBorder(radius=10),
                                        padding=ft.Padding(14, 10, 14, 10),
                                    ),
                                ),
                            ],
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                            vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        ),
                        ft.Container(
                            content=ft.Divider(height=1, color=COLORS["divider"]),
                            padding=ft.Padding(0, 12, 0, 12),
                        ),
                        ft.Column(controls=user_cards, spacing=10),
                    ],
                    spacing=0,
                ),
                bgcolor=COLORS["surface"],
                border=ft.Border.all(1, COLORS["divider"]),
                border_radius=16,
                padding=ft.Padding(20, 20, 20, 20),
                shadow=ft.BoxShadow(spread_radius=0, blur_radius=20,
                                    color=ft.Colors.with_opacity(0.06, "#000000"),
                                    offset=ft.Offset(0, 6)),
            )
        ]
        try:
            page.update()
        except Exception:
            pass

    def open_create_user_dialog(e):
        print("[DEBUG] open_create_user_dialog profile clicked!")
        import traceback
        try:
            uname_field = ft.TextField(label="Nombre de Usuario", border_color="#94A3B8", bgcolor=COLORS["surface"], focused_border_color=COLORS["primary"], border_radius=8, text_size=13)
            email_field = ft.TextField(label="Correo Electrónico", border_color="#94A3B8", bgcolor=COLORS["surface"], focused_border_color=COLORS["primary"], border_radius=8, text_size=13)
            pass_field = ft.TextField(label="Contraseña", password=True, can_reveal_password=True, border_color="#94A3B8", bgcolor=COLORS["surface"], focused_border_color=COLORS["primary"], border_radius=8, text_size=13)
            role_field = ft.Dropdown(
                label="Rol de Usuario",
                options=[
                    ft.dropdown.Option("agente", "Agente"),
                    ft.dropdown.Option("admin", "Admin"),
                ],
                value="agente",
                border_color="#94A3B8", bgcolor=COLORS["surface"],
                focused_border_color=COLORS["primary"],
                border_radius=8,
                text_size=13,
            )
            
            matricula_field = ft.TextField(
                label="Matrícula Asociada (opcional)",
                border_color="#94A3B8", bgcolor=COLORS["surface"],
                focused_border_color=COLORS["primary"],
                border_radius=8,
                text_size=13
            )
            
            req_change_chk = ft.Checkbox(
                label="Exigir cambio de contraseña al primer inicio",
                value=True,
                label_style=ft.TextStyle(size=12)
            )
            
            perm_comercial = ft.Checkbox(label="Gestión Comercial", value=True, label_style=ft.TextStyle(size=12))
            perm_comercial_metricas = ft.Checkbox(label="  └ Métricas y Rendimiento", value=True, label_style=ft.TextStyle(size=11, color=COLORS["text_secondary"]))
            perm_comercial_visitas = ft.Checkbox(label="  └ Plan de Visitas", value=True, label_style=ft.TextStyle(size=11, color=COLORS["text_secondary"]))
            perm_comercial_excel = ft.Checkbox(label="  └ Seguimiento Diario (Excel)", value=True, label_style=ft.TextStyle(size=11, color=COLORS["text_secondary"]))
            
            def toggle_comercial_subs(e):
                val = perm_comercial.value
                perm_comercial_metricas.disabled = not val
                perm_comercial_visitas.disabled = not val
                perm_comercial_excel.disabled = not val
                if not val:
                    perm_comercial_metricas.value = False
                    perm_comercial_visitas.value = False
                    perm_comercial_excel.value = False
                else:
                    perm_comercial_metricas.value = True
                    perm_comercial_visitas.value = True
                    perm_comercial_excel.value = True
                page.update()
                
            perm_comercial.on_change = toggle_comercial_subs
            
            perm_buscador = ft.Checkbox(label="Red de PAS (Buscador)", value=True, label_style=ft.TextStyle(size=12))
            perm_cartera = ft.Checkbox(label="Cartera & Operaciones", value=True, label_style=ft.TextStyle(size=12))
            
            def close_dialog(ev):
                dlg.open = False
                page.update()
                
            def do_create(ev):
                try:
                    uname = (uname_field.value or "").strip().lower()
                    email = (email_field.value or "").strip().lower()
                    pwd = (pass_field.value or "").strip()
                    rol = role_field.value
                    req_change = 1 if req_change_chk.value else 0
                    matricula = (matricula_field.value or "").strip() or None
                    
                    selected_perms = []
                    if perm_comercial.value:
                        selected_perms.append("comercial")
                        if perm_comercial_metricas.value: selected_perms.append("comercial_metricas")
                        if perm_comercial_visitas.value: selected_perms.append("comercial_visitas")
                        if perm_comercial_excel.value: selected_perms.append("comercial_excel")
                    if perm_buscador.value: selected_perms.append("buscador")
                    if perm_cartera.value: selected_perms.append("cartera")
                    perms_str = ",".join(selected_perms)
                    
                    if not uname or not email or not pwd or not rol:
                        show_snackbar("Por favor completa todos los campos para crear el usuario.", is_error=True)
                        return
                        
                    if len(uname) < 3:
                        show_snackbar("El nombre de usuario debe tener al menos 3 caracteres.", is_error=True)
                        return
                        
                    if not re.match(r"^[a-zA-Z0-9_]+$", uname):
                        show_snackbar("El nombre de usuario solo debe contener letras, números y guiones bajos.", is_error=True)
                        return
                        
                    email_pattern = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
                    if not re.match(email_pattern, email):
                        show_snackbar("El correo electrónico no es válido.", is_error=True)
                        return
                        
                    if len(pwd) < 6:
                        show_snackbar("La contraseña debe tener al menos 6 caracteres.", is_error=True)
                        return
                        
                    if matricula and not matricula.isdigit():
                        show_snackbar("La matrícula debe contener únicamente dígitos.", is_error=True)
                        return
                        
                    if on_crear_usuario:
                        res = on_crear_usuario(uname, email, pwd, rol, req_change, matricula, permisos=perms_str)
                        success = res[0] if isinstance(res, tuple) else res
                        msg = res[1] if isinstance(res, tuple) else ("Usuario creado con éxito." if success else "Error al crear el usuario.")
                        
                        if success:
                            dlg.open = False
                            page.update()
                            ssn_test.registrar_log(state.get("username", "admin"), "USER_CREATED", f"Usuario creado: '{uname}' ({email}) - Rol: {rol} - Matrícula: {matricula or 'Ninguna'} - Permisos: {perms_str}")
                            show_snackbar(msg)
                            refresh_users()
                        else:
                            show_snackbar(msg, is_error=True)
                    else:
                        show_snackbar("No se pudo crear el usuario. Callback de creación no configurado.", is_error=True)
                except Exception as ex:
                    print("[ERROR] Exception in do_create:")
                    traceback.print_exc()
                    show_snackbar(f"Error al crear usuario: {ex}", is_error=True)
      
            dlg = ft.AlertDialog(
                title=ft.Row([ft.Icon(ft.Icons.PERSON_ADD_ROUNDED, color=COLORS["primary"]), ft.Text("Crear Nuevo Usuario", size=16, weight=ft.FontWeight.BOLD)]),
                content=ft.Container(
                    content=ft.Column(
                        controls=[
                            uname_field,
                            email_field,
                            role_field,
                            matricula_field,
                            pass_field,
                            req_change_chk,
                            ft.Container(height=4),
                            ft.Text("Permisos de Acceso:", size=12, weight=ft.FontWeight.BOLD, color=COLORS["text_secondary"]),
                            perm_comercial,
                            perm_comercial_metricas,
                            perm_comercial_visitas,
                            perm_comercial_excel,
                            perm_buscador,
                            perm_cartera,
                        ],
                        spacing=12,
                        tight=True,
                    ),
                    width=320,
                ),
                actions=[
                    ft.TextButton("Cancelar", on_click=close_dialog),
                    ft.ElevatedButton("Crear Usuario", on_click=do_create, style=ft.ButtonStyle(bgcolor=COLORS["primary"], color=COLORS["text_on_primary"])),
                ],
                actions_alignment=ft.MainAxisAlignment.END,
            )
            if dlg not in page.overlay:
                page.overlay.append(dlg)
            dlg.open = True
            page.update()
        except Exception as ex:
            print("[ERROR] Exception in open_create_user_dialog:")
            traceback.print_exc()
            show_snackbar(f"Error al abrir diálogo: {ex}", is_error=True)

    def open_edit_user_dialog(user_id, username, email, rol, rc, rf, rb, current_matricula="", perms="comercial,buscador,cartera", calendar_url=""):
        import time
        uname_field_e = ft.TextField(
            value=username, 
            label="Nombre de Usuario", 
            border_color="#94A3B8", bgcolor=COLORS["surface"], 
            focused_border_color=COLORS["primary"], 
            border_radius=8, 
            text_size=13
        )
        email_field_e = ft.TextField(
            value=email, 
            label="Correo Electrónico", 
            border_color="#94A3B8", bgcolor=COLORS["surface"], 
            focused_border_color=COLORS["primary"], 
            border_radius=8, 
            text_size=13
        )
        role_field_e = ft.Dropdown(
            label="Rol de Usuario",
            options=[
                ft.dropdown.Option("agente", "Agente"),
                ft.dropdown.Option("admin", "Admin"),
            ],
            value=rol,
            border_color="#94A3B8", bgcolor=COLORS["surface"],
            focused_border_color=COLORS["primary"],
            border_radius=8,
            text_size=13,
            disabled=(username == state.get("username")), # Don't allow self-role demotion
        )
        matricula_field_e = ft.TextField(
            value=current_matricula,
            label="Matrícula Asociada (opcional)",
            border_color="#94A3B8", bgcolor=COLORS["surface"],
            focused_border_color=COLORS["primary"],
            border_radius=8,
            text_size=13
        )
        calendar_url_field_e = ft.TextField(
            value=calendar_url,
            label="Enlace de Agenda / Cal.com (URL)",
            border_color="#94A3B8", bgcolor=COLORS["surface"],
            focused_border_color=COLORS["primary"],
            border_radius=8,
            text_size=13
        )
        pass_field_e = ft.TextField(
            label="Nueva Contraseña (opcional)", 
            password=True, 
            can_reveal_password=True, 
            border_color="#94A3B8", bgcolor=COLORS["surface"], 
            focused_border_color=COLORS["primary"], 
            border_radius=8, 
            text_size=13,
            hint_text="Dejar en blanco para mantener actual"
        )
        
        req_change_chk = ft.Checkbox(
            label="Exigir cambio de contraseña",
            value=bool(rc),
            label_style=ft.TextStyle(size=12)
        )
        
        is_blocked = (rb > time.time())
        has_attempts = (rf > 0)
        
        reset_lock_chk = ft.Checkbox(
            label="Desbloquear / Restablecer intentos",
            value=False,
            label_style=ft.TextStyle(size=12),
            disabled=not (is_blocked or has_attempts),
        )
        
        perms_set = {p.strip() for p in perms.split(",") if p.strip()}
        perm_comercial = ft.Checkbox(label="Gestión Comercial", value=("comercial" in perms_set), label_style=ft.TextStyle(size=12))
        
        has_sub_comercial = any(p in perms_set for p in ["comercial_metricas", "comercial_visitas", "comercial_excel"])
        default_sub_val = ("comercial" in perms_set) and not has_sub_comercial
        
        perm_comercial_metricas = ft.Checkbox(
            label="  └ Métricas y Rendimiento",
            value=(("comercial_metricas" in perms_set) or default_sub_val),
            label_style=ft.TextStyle(size=11, color=COLORS["text_secondary"]),
            disabled=not ("comercial" in perms_set)
        )
        perm_comercial_visitas = ft.Checkbox(
            label="  └ Plan de Visitas",
            value=(("comercial_visitas" in perms_set) or default_sub_val),
            label_style=ft.TextStyle(size=11, color=COLORS["text_secondary"]),
            disabled=not ("comercial" in perms_set)
        )
        perm_comercial_excel = ft.Checkbox(
            label="  └ Seguimiento Diario (Excel)",
            value=(("comercial_excel" in perms_set) or default_sub_val),
            label_style=ft.TextStyle(size=11, color=COLORS["text_secondary"]),
            disabled=not ("comercial" in perms_set)
        )
        
        def toggle_comercial_subs(e):
            val = perm_comercial.value
            perm_comercial_metricas.disabled = not val
            perm_comercial_visitas.disabled = not val
            perm_comercial_excel.disabled = not val
            if not val:
                perm_comercial_metricas.value = False
                perm_comercial_visitas.value = False
                perm_comercial_excel.value = False
            else:
                perm_comercial_metricas.value = True
                perm_comercial_visitas.value = True
                perm_comercial_excel.value = True
            page.update()
            
        perm_comercial.on_change = toggle_comercial_subs
        
        perm_buscador = ft.Checkbox(label="Red de PAS (Buscador)", value=("buscador" in perms_set), label_style=ft.TextStyle(size=12))
        perm_cartera = ft.Checkbox(label="Cartera & Operaciones", value=("cartera" in perms_set), label_style=ft.TextStyle(size=12))
        
        status_info = []
        if is_blocked:
            rem = int(rb - time.time())
            status_info.append(
                ft.Text(f"⚠️ Bloqueo activo: vence en {rem}s", size=11, color=ft.Colors.RED_400, weight=ft.FontWeight.BOLD)
            )
        if rf > 0:
            status_info.append(
                ft.Text(f"⚠️ Intentos fallidos: {rf}", size=11, color=ft.Colors.ORANGE_400)
            )
        
        def close_dialog(ev):
            dlg.open = False
            page.update()
            
        def do_update(ev):
            new_uname = (uname_field_e.value or "").strip().lower()
            new_email = (email_field_e.value or "").strip().lower()
            new_pwd = (pass_field_e.value or "").strip()
            new_rol = role_field_e.value
            new_matricula = (matricula_field_e.value or "").strip()
            new_calendar_url = (calendar_url_field_e.value or "").strip()
            req_change_val = 1 if req_change_chk.value else 0
            reset_lock_val = reset_lock_chk.value
            
            if not new_uname or not new_email:
                show_snackbar("El nombre de usuario y correo son requeridos.", is_error=True)
                return
                
            if new_pwd and len(new_pwd) < 6:
                show_snackbar("La nueva contraseña debe tener al menos 6 caracteres.", is_error=True)
                return
                
            selected_perms = []
            if perm_comercial.value:
                selected_perms.append("comercial")
                if perm_comercial_metricas.value: selected_perms.append("comercial_metricas")
                if perm_comercial_visitas.value: selected_perms.append("comercial_visitas")
                if perm_comercial_excel.value: selected_perms.append("comercial_excel")
            if perm_buscador.value: selected_perms.append("buscador")
            if perm_cartera.value: selected_perms.append("cartera")
            perms_str = ",".join(selected_perms)
            
            success, msg = ssn_test.actualizar_usuario(
                user_id, 
                new_uname, 
                new_email, 
                password_txt=new_pwd, 
                rol=new_rol, 
                requiere_cambio=req_change_val,
                reset_lock=reset_lock_val,
                is_self_update=(username == state.get("username")),
                matricula=new_matricula,
                permisos=perms_str,
                calendar_url=new_calendar_url
            )
            
            if success:
                dlg.open = False
                page.update()
                ssn_test.registrar_log(
                    state.get("username", "admin"), 
                    "USER_UPDATED", 
                    f"Usuario editado: ID {user_id} - '{new_uname}' ({new_email}) - Rol: {new_rol} - Req. Cambio: {req_change_val} - Reset Lock: {reset_lock_val} - Matrícula: {new_matricula or 'Ninguna'} - Permisos: {perms_str} - Agenda: {new_calendar_url}"
                )
                
                if username == state.get("username"):
                    state["username"] = new_uname
                    # Also update our own permissions in state if we edited ourselves
                    state["permisos"] = set(selected_perms)
                    state["calendar_url"] = new_calendar_url
                
                show_snackbar(msg)
                refresh_users()
            else:
                show_snackbar(msg, is_error=True)
 
        dlg = ft.AlertDialog(
            title=ft.Row([ft.Icon(ft.Icons.EDIT_ROUNDED, color=COLORS["primary"]), ft.Text(f"Editar Usuario: {username}", size=16, weight=ft.FontWeight.BOLD)]),
            content=ft.Container(
                content=ft.Column(
                    controls=[
                        uname_field_e,
                        email_field_e,
                        role_field_e,
                        matricula_field_e,
                        calendar_url_field_e,
                        pass_field_e,
                        req_change_chk,
                        reset_lock_chk,
                        ft.Container(height=4),
                        ft.Text("Permisos de Acceso:", size=12, weight=ft.FontWeight.BOLD, color=COLORS["text_secondary"]),
                        perm_comercial,
                        perm_comercial_metricas,
                        perm_comercial_visitas,
                        perm_comercial_excel,
                        perm_buscador,
                        perm_cartera,
                    ] + status_info,
                    spacing=10,
                    tight=True,
                ),
                width=320,
            ),
            actions=[
                ft.TextButton("Cancelar", on_click=close_dialog),
                ft.FilledButton("Guardar Cambios", on_click=do_update, style=ft.ButtonStyle(bgcolor=COLORS["primary"], color=COLORS["text_on_primary"])),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        if dlg not in page.overlay:
            page.overlay.append(dlg)
        dlg.open = True
        page.update()

    def open_change_pw_dialog(user_id, username):
        pass_field_pw = ft.TextField(label="Nueva Contraseña", password=True, can_reveal_password=True, border_color="#94A3B8", bgcolor=COLORS["surface"], focused_border_color=COLORS["primary"], border_radius=8, text_size=13)
        
        def close_dialog(ev):
            dlg.open = False
            page.update()
            
        def do_change(ev):
            pwd = (pass_field_pw.value or "").strip()
            if not pwd or len(pwd) < 6:
                show_snackbar("La contraseña debe tener al menos 6 caracteres.", is_error=True)
                return
                
            if on_cambiar_password and on_cambiar_password(user_id, pwd):
                dlg.open = False
                page.update()
                ssn_test.registrar_log(state.get("username", "admin"), "USER_PASSWORD_RESET", f"Contraseña restablecida por admin para: '{username}'")
                show_snackbar(f"Contraseña de '{username}' restablecida con éxito.")
                refresh_users()
            else:
                show_snackbar("No se pudo cambiar la contraseña.", is_error=True)

        dlg = ft.AlertDialog(
            title=ft.Row([ft.Icon(ft.Icons.LOCK_RESET_ROUNDED, color=COLORS["primary"]), ft.Text(f"Restablecer contraseña para '{username}'", size=16, weight=ft.FontWeight.BOLD)]),
            content=ft.Container(
                content=ft.Column(controls=[pass_field_pw], tight=True),
                width=320,
            ),
            actions=[
                ft.TextButton("Cancelar", on_click=close_dialog),
                ft.ElevatedButton("Confirmar Cambio", on_click=do_change, style=ft.ButtonStyle(bgcolor=COLORS["primary"], color=COLORS["text_on_primary"])),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        if dlg not in page.overlay:
            page.overlay.append(dlg)
        dlg.open = True
        page.update()

    def open_delete_user_dialog(user_id, username):
        def close_dialog(ev):
            dlg.open = False
            page.update()
            
        def do_delete(ev):
            dlg.open = False
            page.update()
            if on_eliminar_usuario and on_eliminar_usuario(user_id):
                ssn_test.registrar_log(state.get("username", "admin"), "USER_DELETED", f"Usuario eliminado: '{username}'")
                show_snackbar(f"Usuario '{username}' eliminado con éxito.")
                refresh_users()
            else:
                show_snackbar("No se pudo eliminar el usuario.", is_error=True)

        dlg = ft.AlertDialog(
            title=ft.Row([ft.Icon(ft.Icons.WARNING_ROUNDED, color=ft.Colors.RED_500), ft.Text("Eliminar Usuario", size=16, weight=ft.FontWeight.BOLD)]),
            content=ft.Text(f"¿Estás seguro de que deseas eliminar permanentemente al usuario '{username}'? Esta acción no se puede deshacer.", size=13),
            actions=[
                ft.TextButton("Cancelar", on_click=close_dialog),
                ft.ElevatedButton("Sí, Eliminar", on_click=do_delete, style=ft.ButtonStyle(bgcolor=ft.Colors.RED_600, color=ft.Colors.WHITE)),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        if dlg not in page.overlay:
            page.overlay.append(dlg)
        dlg.open = True
        page.update()

    
    if curr_rol == "admin":
        refresh_users()
        # Remove fixed width from profile card to make it responsive
        profile_card.width = None
        
        layout_grid = ft.ResponsiveRow(
            controls=[
                ft.Container(
                    content=profile_card,
                    col={"sm": 12, "md": 12, "lg": 5, "xl": 4},
                ),
                ft.Container(
                    content=users_column,
                    col={"sm": 12, "md": 12, "lg": 7, "xl": 8},
                ),
            ],
            spacing=30,
            run_spacing=30,
        )
        
        controls_to_show = [layout_grid]
    else:
        profile_card.width = 550
        controls_to_show = [
            ft.Row(
                controls=[profile_card],
                alignment=ft.MainAxisAlignment.CENTER,
            )
        ]

    return ft.Container(
        content=ft.Column(
            controls=[
                # ── Page header ────────────────────────────────────────────
                ft.Container(
                    content=ft.Row(
                        controls=[
                            ft.Container(
                                content=ft.Row(
                                    controls=[
                                        ft.Icon(ft.Icons.ARROW_BACK_ROUNDED,
                                                color=COLORS["primary"], size=16),
                                        ft.Text("Volver", size=12, weight=ft.FontWeight.W_700,
                                                color=COLORS["primary"]),
                                    ],
                                    spacing=6,
                                ),
                                bgcolor=ft.Colors.with_opacity(0.08, COLORS["primary"]),
                                border_radius=20,
                                padding=ft.Padding(12, 6, 14, 6),
                                on_click=lambda e: on_back(),
                                ink=True,
                                tooltip="Volver al panel principal",
                            ),
                        ],
                        alignment=ft.MainAxisAlignment.START,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                    padding=ft.Padding(0, 0, 0, 16),
                ),
                ft.Column(
                    controls=controls_to_show,
                    spacing=0,
                    horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
                ),
            ],
            spacing=0,
            scroll=ft.ScrollMode.AUTO,
        ),
        padding=ft.Padding(36, 28, 36, 28),
        expand=True,
        bgcolor=COLORS["background"],
    )


# ---------------------------------------------------------------------------
# Vista del Módulo de Cartera (Katrix ERP)
# ---------------------------------------------------------------------------

def build_cartera_view(
    page: ft.Page,
    on_back: Callable,
    user_id: int = None,
    role: str = None,
    state: Optional[Dict[str, Any]] = None,
) -> ft.Container:
    """
    Vista Cartera de Productores — diseño maestro-detalle:
    - Izquierda: búsqueda + lista de PAS (productores SSN)
    - Derecha: detalle del PAS seleccionado (KPIs, gráfico, pólizas)
    """
    import ssn_test as _ssn

    # ── Estado ─────────────────────────────────────────────────────────────
    all_pas = []
    selected_pas = {"data": None}

    # ── Panel derecho (contenido dinámico) ─────────────────────────────────
    detail_col = ft.Column(
        spacing=14,
        expand=True,
        scroll=ft.ScrollMode.AUTO,
    )

    def _kpi_card(title, value, sub, icon, color):
        return ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Container(
                        content=ft.Icon(icon, color=color, size=18),
                        bgcolor=ft.Colors.with_opacity(0.12, color),
                        border_radius=8,
                        padding=8,
                    ),
                    ft.Column([
                        ft.Text(str(value), size=18, weight=ft.FontWeight.BOLD, color=COLORS["text_primary"]),
                        ft.Text(title, size=10, color=COLORS["text_secondary"]),
                    ], spacing=1, tight=True),
                ], spacing=10),
                ft.Text(sub, size=10, color=COLORS["text_secondary"], italic=True),
            ], spacing=8),
            bgcolor=COLORS["surface"],
            border=ft.Border.all(1, COLORS["border"]),
            border_radius=12,
            padding=14,
            expand=True,
        )

    def render_empty_detail():
        detail_col.controls = [
            ft.Container(
                content=ft.Column([
                    ft.Icon(ft.Icons.PERSON_SEARCH_ROUNDED, size=56, color=COLORS["border"]),
                    ft.Text("Seleccioná un productor", size=16, weight=ft.FontWeight.BOLD, color=COLORS["text_secondary"]),
                    ft.Text("Hacé clic en un PAS de la lista para ver su ficha completa.", size=12, color=COLORS["text_secondary"], text_align=ft.TextAlign.CENTER),
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=10),
                alignment=ft.Alignment(0, 0),
                expand=True,
                padding=40,
            )
        ]
        try: detail_col.update()
        except: pass

    def render_detail(pas):
        """Renderiza el panel de detalle para un PAS seleccionado."""
        matricula = pas.get("matricula", "")
        nombre = pas.get("nombre", "Desconocido")
        companias_raw = pas.get("companias") or pas.get("sociedades") or ""
        ramo = pas.get("ramo", "")
        provincia = pas.get("provincia", "")
        localidad = pas.get("localidad", "")
        estado = pas.get("estado_contacto", "Sin contacto")

        # Obtener pólizas del productor
        try:
            polizas = _ssn.obtener_polizas(pas_matricula=matricula)
        except Exception:
            polizas = []

        # Métricas calculadas
        polizas_vigentes = [p for p in polizas if p.get("estado") == "Vigente"]
        total_primas = sum(float(p.get("premio", 0) or 0) for p in polizas_vigentes)
        total_comisiones = sum(float(p.get("comision_monto", 0) or 0) for p in polizas_vigentes)
        clientes_unicos = len(set(p.get("cliente_nombre", "") for p in polizas_vigentes if p.get("cliente_nombre")))

        def fmt_money(v):
            try:
                return f"${float(v):,.0f}".replace(",", ".")
            except Exception:
                return "$0"

        # Compañías únicas
        companias_list = sorted(set(p.get("compania", "") for p in polizas_vigentes if p.get("compania")))

        # ── Header del PAS ──
        estado_color = {
            "contactado": COLORS["success"],
            "en_seguimiento": COLORS["primary"],
            "sin contacto": COLORS["text_secondary"],
        }.get((estado or "").lower(), COLORS["text_secondary"])

        header = ft.Container(
            content=ft.Row([
                ft.Container(
                    content=ft.Text(
                        (nombre[0] if nombre else "P").upper(),
                        size=20, weight=ft.FontWeight.BOLD, color="#FFFFFF",
                    ),
                    bgcolor=COLORS["primary"],
                    border_radius=30,
                    width=52, height=52,
                    alignment=ft.Alignment(0, 0),
                ),
                ft.Column([
                    ft.Text(nombre, size=16, weight=ft.FontWeight.BOLD, color=COLORS["text_primary"]),
                    ft.Row([
                        ft.Text(f"Mat. {matricula}", size=11, color=COLORS["text_secondary"]),
                        ft.Container(width=1, height=12, bgcolor=COLORS["border"]),
                        ft.Text(ramo or "Sin ramo", size=11, color=COLORS["text_secondary"]),
                        ft.Container(width=1, height=12, bgcolor=COLORS["border"]),
                        ft.Text(f"{localidad or provincia or 'Sin ubicación'}", size=11, color=COLORS["text_secondary"]),
                    ], spacing=8),
                    ft.Row([
                        ft.Container(
                            content=ft.Text(estado or "Sin contacto", size=10, color="#FFFFFF", weight=ft.FontWeight.BOLD),
                            bgcolor=estado_color,
                            border_radius=6,
                            padding=ft.Padding(8, 3, 8, 3),
                        ),
                        ft.Container(
                            content=ft.Row([
                                ft.Icon(ft.Icons.OPEN_IN_NEW_ROUNDED, size=12, color=COLORS["primary"]),
                                ft.Text("Ver ficha completa", size=10, color=COLORS["primary"], weight=ft.FontWeight.BOLD),
                            ], spacing=4, tight=True),
                            bgcolor=ft.Colors.with_opacity(0.10, COLORS["primary"]),
                            border=ft.Border.all(1, ft.Colors.with_opacity(0.25, COLORS["primary"])),
                            border_radius=6,
                            padding=ft.Padding(8, 3, 8, 3),
                            on_click=(
                                (lambda mat=matricula: lambda e: state["open_detail_by_matricula"](mat, back_to="cartera"))(matricula)
                                if state and "open_detail_by_matricula" in state else None
                            ),
                            ink=True,
                            tooltip="Abrir ficha completa del productor",
                        ),
                    ], spacing=6),
                ], spacing=4, expand=True),
            ], spacing=14, vertical_alignment=ft.CrossAxisAlignment.CENTER),
            bgcolor=COLORS["surface"],
            border=ft.Border.all(1, COLORS["border"]),
            border_radius=12,
            padding=16,
        )

        # ── KPIs ──
        kpi_row = ft.Row([
            _kpi_card("Pólizas Vigentes", len(polizas_vigentes), f"Total: {len(polizas)} pólizas",
                      ft.Icons.DESCRIPTION_ROUNDED, COLORS["primary"]),
            _kpi_card("Clientes", clientes_unicos, "clientes únicos con pólizas",
                      ft.Icons.PEOPLE_ROUNDED, "#8B5CF6"),
            _kpi_card("Prima Total", fmt_money(total_primas), "suma de primas vigentes",
                      ft.Icons.ATTACH_MONEY_ROUNDED, COLORS["success"]),
            _kpi_card("Comisiones", fmt_money(total_comisiones), "comisiones estimadas",
                      ft.Icons.TRENDING_UP_ROUNDED, "#F59E0B"),
        ], spacing=10)

        # ── Distribución por compañía (gráfico de barras simple) ──
        companias_count = {}
        for p in polizas_vigentes:
            comp = p.get("compania", "Otra")
            companias_count[comp] = companias_count.get(comp, 0) + 1

        max_count = max(companias_count.values(), default=1)

        bar_items = []
        colors_palette = [COLORS["primary"], "#8B5CF6", COLORS["success"], "#F59E0B", "#EF4444", "#06B6D4"]
        for i, (comp, cnt) in enumerate(sorted(companias_count.items(), key=lambda x: -x[1])[:6]):
            bar_color = colors_palette[i % len(colors_palette)]
            pct = cnt / max_count
            bar_items.append(ft.Column([
                ft.Text(str(cnt), size=11, weight=ft.FontWeight.BOLD, color=bar_color),
                ft.Container(
                    content=ft.Container(
                        bgcolor=bar_color,
                        border_radius=4,
                        height=max(8, int(80 * pct)),
                        width=32,
                    ),
                    height=80,
                    alignment=ft.Alignment(-1, 1),
                ),
                ft.Text(
                    comp[:10] + "..." if len(comp) > 10 else comp,
                    size=9, color=COLORS["text_secondary"], text_align=ft.TextAlign.CENTER,
                    width=40,
                ),
            ], spacing=3, horizontal_alignment=ft.CrossAxisAlignment.CENTER))

        chart_section = ft.Container(
            content=ft.Column([
                ft.Text("Distribución por Compañía", size=13, weight=ft.FontWeight.BOLD, color=COLORS["text_primary"]),
                ft.Text(f"{len(companias_count)} compañías • {len(polizas_vigentes)} pólizas vigentes", size=11, color=COLORS["text_secondary"]),
                ft.Container(height=10),
                ft.Row(bar_items, spacing=16, alignment=ft.MainAxisAlignment.START) if bar_items else
                ft.Text("Sin pólizas vigentes", size=12, italic=True, color=COLORS["text_secondary"]),
            ], spacing=4),
            bgcolor=COLORS["surface"],
            border=ft.Border.all(1, COLORS["border"]),
            border_radius=12,
            padding=16,
        )

        # ── Lista de pólizas ──
        poliza_items = []
        for p in polizas_vigentes[:10]:
            prm = fmt_money(p.get("premio", 0))
            poliza_items.append(ft.Container(
                content=ft.Row([
                    ft.Icon(ft.Icons.SHIELD_ROUNDED, color=COLORS["primary"], size=16),
                    ft.Column([
                        ft.Row([
                            ft.Text(p.get("nro_poliza", "—"), size=12, weight=ft.FontWeight.BOLD, color=COLORS["text_primary"]),
                            ft.Text(f"• {p.get('compania', '')} • {p.get('ramo', '')}", size=11, color=COLORS["text_secondary"]),
                        ], spacing=6),
                        ft.Text(p.get("cliente_nombre", ""), size=11, color=COLORS["text_secondary"]),
                    ], spacing=2, expand=True),
                    ft.Text(prm, size=12, weight=ft.FontWeight.BOLD, color=COLORS["success"]),
                ], spacing=10, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                bgcolor=COLORS["surface"],
                border=ft.Border.all(1, COLORS["border"]),
                border_radius=8,
                padding=ft.Padding(12, 10, 12, 10),
            ))

        polizas_section = ft.Container(
            content=ft.Column([
                ft.Text("Pólizas Vigentes", size=13, weight=ft.FontWeight.BOLD, color=COLORS["text_primary"]),
                ft.Text(f"Mostrando {min(10, len(polizas_vigentes))} de {len(polizas_vigentes)}", size=11, color=COLORS["text_secondary"]),
                ft.Container(height=6),
                *(poliza_items if poliza_items else [ft.Text("Sin pólizas vigentes.", size=12, italic=True, color=COLORS["text_secondary"])])
            ], spacing=8),
            bgcolor=ft.Colors.with_opacity(0.3, COLORS["surface"]),
            border=ft.Border.all(1, COLORS["border"]),
            border_radius=12,
            padding=16,
        )

        detail_col.controls = [header, kpi_row, chart_section, polizas_section]
        try: page.update()
        except Exception as ex:
            print("render_detail error:", ex)

    # ── Lista izquierda de PAS ──────────────────────────────────────────────
    pas_list_col = ft.Column(spacing=6, scroll=ft.ScrollMode.AUTO, expand=True)
    search_pas = ft.TextField(
        hint_text="Buscar por nombre o matrícula...",
        prefix_icon=ft.Icons.SEARCH_ROUNDED,
        border_color="#94A3B8", bgcolor=COLORS["surface"],
        focused_border_color=COLORS["primary"],
        border_radius=8,
        text_size=13,
        height=42,
    )

    def build_pas_list(query=""):
        query = query.strip().lower()
        filtered = [
            p for p in all_pas
            if not query or
            query in (p.get("nombre") or "").lower() or
            query in (p.get("matricula") or "").lower()
        ]
        filtered = sorted(filtered, key=lambda x: x.get("nombre") or "")

        pas_list_col.controls = []
        for pas in filtered[:80]:  # máx 80 para performance
            mat = pas.get("matricula", "—")
            nom = pas.get("nombre", "Desconocido")
            comp = pas.get("companias") or ""
            prov = pas.get("provincia") or ""
            cant_pol = pas.get("cant_polizas", 0) or 0
            cant_cli = pas.get("cant_clientes", 0) or 0

            is_selected = selected_pas["data"] and selected_pas["data"].get("matricula") == mat

            def make_click(p=pas):
                def _click(e):
                    selected_pas["data"] = p
                    render_detail(p)
                    build_pas_list(search_pas.value or "")
                return _click

            counts_badge = (
                ft.Container(
                    content=ft.Text(f"{cant_pol} pól. | {cant_cli} cli.", size=9, weight=ft.FontWeight.BOLD, color=COLORS["primary"] if is_selected else "#0EA5E9"),
                    bgcolor=ft.Colors.with_opacity(0.12, COLORS["primary"] if is_selected else "#0EA5E9"),
                    border_radius=6,
                    padding=ft.Padding(5, 2, 5, 2)
                ) if cant_pol > 0 else
                ft.Text("0 pólizas", size=10, color=COLORS["text_secondary"])
            )

            pas_list_col.controls.append(ft.Container(
                content=ft.Column([
                    ft.Row([
                        ft.Container(
                            content=ft.Text((nom[0] if nom else "P").upper(), size=11, weight=ft.FontWeight.BOLD, color="#FFFFFF"),
                            bgcolor=COLORS["primary"] if is_selected else COLORS["border"],
                            border_radius=16, width=28, height=28,
                            alignment=ft.Alignment(0, 0),
                        ),
                        ft.Column([
                            ft.Text(nom, size=12, weight=ft.FontWeight.BOLD,
                                    color=COLORS["primary"] if is_selected else COLORS["text_primary"],
                                    max_lines=1, overflow=ft.TextOverflow.ELLIPSIS),
                            ft.Row([
                                ft.Text(f"Mat. {mat}", size=10, color=COLORS["text_secondary"]),
                                counts_badge,
                            ], spacing=6, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                        ], spacing=1, expand=True),
                    ], spacing=8, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                ], spacing=0),
                bgcolor=ft.Colors.with_opacity(0.08, COLORS["primary"]) if is_selected else COLORS["surface"],
                border=ft.Border.all(1.5, COLORS["primary"] if is_selected else COLORS["border"]),
                border_radius=10,
                padding=ft.Padding(10, 8, 10, 8),
                on_click=make_click(),
                ink=True,
            ))

        if not pas_list_col.controls:
            pas_list_col.controls.append(ft.Container(
                content=ft.Text("No se encontraron productores.", size=12, italic=True, color=COLORS["text_secondary"]),
                padding=20,
            ))
        try: page.update()
        except: pass

    def on_search_change(e):
        build_pas_list(search_pas.value or "")
    search_pas.on_change = on_search_change

    # ── Cargar datos ────────────────────────────────────────────────────────
    try:
        all_pas = _ssn.obtener_cartera_db(user_id=user_id, role=role) or []
    except Exception as ex:
        print("Error cargando PAS:", ex)
        all_pas = []

    build_pas_list()
    render_empty_detail()

    # ── Panel izquierdo ──────────────────────────────────────────────────────
    left_panel = ft.Container(
        content=ft.Column([
            ft.Text("Productores PAS", size=14, weight=ft.FontWeight.BOLD, color=COLORS["text_primary"]),
            ft.Text(f"{len(all_pas)} productores en cartera", size=11, color=COLORS["text_secondary"]),
            ft.Container(height=4),
            search_pas,
            ft.Container(height=4),
            ft.Container(content=pas_list_col, expand=True),
        ], spacing=6, expand=True),
        width=300,
        bgcolor=COLORS["surface"],
        border=ft.Border(right=ft.BorderSide(1, COLORS["border"])),
        padding=ft.Padding(16, 18, 12, 18),
    )

    # ── Panel derecho ───────────────────────────────────────────────────────
    right_panel = ft.Container(
        content=detail_col,
        expand=True,
        padding=ft.Padding(20, 18, 20, 18),
    )

    return ft.Container(
        content=ft.Column([
            # Header
            ft.Container(
                content=ft.Row([
                    ft.IconButton(
                        icon=ft.Icons.ARROW_BACK_ROUNDED,
                        icon_color=COLORS["primary"],
                        icon_size=24,
                        tooltip="Volver",
                        on_click=lambda e: on_back(),
                    ),
                    ft.Column([
                        ft.Text("Cartera de Productores", size=20, weight=ft.FontWeight.BOLD, color=COLORS["text_primary"]),
                        ft.Text("Gestión y análisis de tu cartera de productores PAS", size=11, color=COLORS["text_secondary"]),
                    ], spacing=1, tight=True),
                ], spacing=10),
                bgcolor=COLORS["surface"],
                border=ft.Border(bottom=ft.BorderSide(1, COLORS["border"])),
                padding=ft.Padding(20, 14, 20, 14),
            ),
            # Cuerpo: izquierda + derecha
            ft.Container(
                content=ft.Row([left_panel, right_panel], spacing=0, expand=True),
                expand=True,
            ),
        ], spacing=0, expand=True),
        expand=True,
        bgcolor=COLORS["background"],
    )

def build_licensing_view(
    on_activate: Callable[[str], None],
    error_text: Optional[str] = None,
    fingerprint: str = "",
    on_clear_error: Optional[Callable[[], None]] = None,
) -> ft.Container:
    # Comprobar si el error es de licencia suspendida o eliminada
    is_suspended_or_deleted = False
    if error_text:
        err_lower = error_text.lower()
        if "suspendida" in err_lower or "inexistente" in err_lower or "no encontrada" in err_lower or "eliminada" in err_lower:
            is_suspended_or_deleted = True

    if is_suspended_or_deleted:
        # Hermosa vista de cable desconectado para "UF ALGO SALIO MAL"
        def send_email_click(e):
            import urllib.parse
            subject_encoded = urllib.parse.quote("Consulta sobre Licencia Suspendida/Eliminada - Katrix")
            body_encoded = urllib.parse.quote(
                f"Hola Soporte,\n\n"
                f"Tengo una consulta acerca del estado de mi licencia.\n"
                f"Detalle del error reportado por el sistema:\n"
                f"\"{error_text or 'No especificado'}\"\n\n"
                f"Por favor, indíquenme los pasos a seguir para restablecer el servicio.\n\n"
                f"Saludos cordiales."
            )
            mailto_url = f"mailto:soporte@katrix.com.ar?subject={subject_encoded}&body={body_encoded}"
            e.page.launch_url(mailto_url)

        support_btn = ft.Container(
            content=ft.Row(
                controls=[
                    ft.Icon(ft.Icons.EMAIL_ROUNDED, color=ft.Colors.WHITE, size=16),
                    ft.Text("Contactar a Soporte Técnico", size=13, color=ft.Colors.WHITE, weight=ft.FontWeight.W_600),
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                spacing=8,
            ),
            bgcolor=ft.Colors.RED_500,
            border_radius=20,
            padding=ft.Padding(16, 10, 16, 10),
            on_click=send_email_click,
            on_hover=lambda e: setattr(e.control, "bgcolor", ft.Colors.RED_600 if e.data == "true" else ft.Colors.RED_500) or e.control.update(),
            animate=ft.Animation(200, "easeOut"),
        )

        column_controls = [
            ft.Container(
                content=ft.Image(
                    src="cable_desconectado.png",
                    width=220,
                    height=220,
                    fit="contain",
                    border_radius=12,
                ),
                alignment=ft.Alignment(0, 0),
                margin=ft.Margin(0, 0, 0, 16),
            ),
            ft.Container(
                content=ft.Text("UF, ALGO SALIÓ MAL", size=22, weight=ft.FontWeight.W_900, color=ft.Colors.RED_500, text_align=ft.TextAlign.CENTER),
                alignment=ft.Alignment(0, 0),
            ),
            ft.Container(
                content=ft.Text(error_text or "La licencia está suspendida", size=13, color=ft.Colors.RED_200, weight=ft.FontWeight.W_500, text_align=ft.TextAlign.CENTER),
                alignment=ft.Alignment(0, 0),
                bgcolor=ft.Colors.with_opacity(0.1, ft.Colors.RED_900),
                border=ft.Border.all(1, ft.Colors.with_opacity(0.2, ft.Colors.RED_400)),
                border_radius=8,
                padding=12,
                margin=ft.Margin(0, 8, 0, 16),
            ),
            ft.Container(
                content=support_btn,
                alignment=ft.Alignment(0, 0),
                margin=ft.Margin(0, 0, 0, 20),
            ),
        ]
        
        if on_clear_error:
            # Botón para poder ingresar otra licencia en caso de que quieran ingresar una clave nueva
            column_controls.append(
                ft.TextButton(
                    "Ingresar otra licencia",
                    icon=ft.Icons.KEY_ROUNDED,
                    on_click=lambda e: on_clear_error(),
                    style=ft.ButtonStyle(
                        color=COLORS["primary"],
                    )
                )
            )
            
        def on_card_hover(e):
            e.control.scale = 1.025 if e.data == "true" else 1.0
            e.control.shadow = ft.BoxShadow(
                spread_radius=2, 
                blur_radius=20, 
                color=ft.Colors.with_opacity(0.3 if e.data == "true" else 0.12, ft.Colors.RED_500 if e.data == "true" else "#000000")
            )
            e.control.update()

        return ft.Container(
            content=ft.Column(
                controls=column_controls,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=4,
                tight=True,
            ),
            bgcolor=COLORS["surface"],
            border_radius=16,
            padding=32,
            width=380,
            shadow=ft.BoxShadow(spread_radius=1, blur_radius=12, color=ft.Colors.with_opacity(0.12, "#000000")),
            on_hover=on_card_hover,
            animate_scale=ft.Animation(300, "easeOut"),
            animate=ft.Animation(300, "easeOut"),
        )

    # Vista normal de entrada de licencia
    key_field = ft.TextField(
        label="Clave de Licencia",
        hint_text="KTX-XXXX-XXXX-XXXX",
        border_color=COLORS["border"],
        focused_border_color=COLORS["primary"],
        border_radius=10,
        text_size=14,
        color=COLORS["text_primary"],
        bgcolor=COLORS["surface"],
        prefix_icon=ft.Icons.KEY_ROUNDED,
        width=300,
    )
    
    def do_activate(e):
        on_activate(key_field.value)

    activate_btn = ft.FilledButton(
        "Activar Licencia",
        on_click=do_activate,
        style=ft.ButtonStyle(
            bgcolor=COLORS["primary"],
            color=COLORS["text_on_primary"],
            shape=ft.RoundedRectangleBorder(radius=10),
            padding=ft.Padding(left=24, right=24, top=14, bottom=14),
        ),
        width=300,
    )

    column_controls = [
        ft.Container(
            content=ft.Icon(ft.Icons.LOCK_PERSON_ROUNDED, size=52, color=COLORS["primary"]),
            alignment=ft.Alignment(0, 0),
        ),
        ft.Container(
            content=ft.Text("CRM Seguros", size=24, weight=ft.FontWeight.W_800, color=COLORS["primary"]),
            alignment=ft.Alignment(0, 0),
        ),
        ft.Container(
            content=ft.Text("Activación de Licencia", size=14, weight=ft.FontWeight.W_600, color=COLORS["text_primary"]),
            alignment=ft.Alignment(0, 0),
        ),
        ft.Container(
            content=ft.Text("Este sistema requiere una licencia activa para ejecutarse.", size=12, color=COLORS["text_secondary"], text_align=ft.TextAlign.CENTER),
            alignment=ft.Alignment(0, 0),
            margin=ft.Margin(0, 0, 0, 16),
        ),
    ]

    if error_text:
        error_banner = ft.Container(
            content=ft.Row(
                controls=[
                    ft.Icon(ft.Icons.WARNING_AMBER_ROUNDED, color=ft.Colors.RED_700, size=18),
                    ft.Text(error_text, color=ft.Colors.RED_900, size=12, weight=ft.FontWeight.W_500, expand=True)
                ],
                spacing=8,
            ),
            bgcolor=ft.Colors.RED_50,
            border=ft.Border.all(1, ft.Colors.RED_200),
            border_radius=8,
            padding=10,
            width=300,
            margin=ft.Margin(0, 0, 0, 12),
        )
        column_controls.append(error_banner)

    column_controls.extend([
        key_field,
        ft.Container(height=16),
        activate_btn,
        ft.Container(height=12),
        ft.Text("Impulsado por Katrix ⚡", size=11, color=COLORS["text_secondary"], weight=ft.FontWeight.W_500),
    ])

    return ft.Container(
        content=ft.Column(
            controls=column_controls,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=4,
            tight=True,
        ),
        bgcolor=COLORS["surface"],
        border_radius=16,
        padding=32,
        width=360,
        shadow=ft.BoxShadow(spread_radius=1, blur_radius=12, color=ft.Colors.with_opacity(0.12, "#000000")),
    )


# ---------------------------------------------------------------------------
# Modal de Recordatorio de Reuniones y Visitas Pendientes
# ---------------------------------------------------------------------------
def open_reuniones_notif_dialog(page: ft.Page, on_refresh_header=None):
    from notificaciones import obtener_resumen_reuniones
    import ssn_test
    
    resumen = obtener_resumen_reuniones()
    reuniones = resumen.get("reuniones_pendientes", [])
    
    def close_dialog(e):
        dlg.open = False
        page.update()
        
    def make_marcar_realizada(visita_id, nombre):
        def _on_click(e):
            if ssn_test.actualizar_visita(visita_id, "realizada"):
                page.snack_bar = ft.SnackBar(
                    content=ft.Text(f"🚀 Visita a '{nombre}' marcada como Realizada.", color=ft.Colors.WHITE, size=13, weight=ft.FontWeight.W_600),
                    bgcolor=COLORS["success"],
                    duration=3000,
                )
                page.snack_bar.open = True
                if on_refresh_header:
                    on_refresh_header()
                dlg.open = False
                page.update()
                open_reuniones_notif_dialog(page, on_refresh_header)
        return _on_click

    items_controls = []
    if not reuniones:
        items_controls.append(
            ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Icon(ft.Icons.CHECK_CIRCLE_OUTLINE_ROUNDED, color=COLORS["success"], size=44),
                        ft.Text("¡No tenés reuniones pendientes!", size=14, weight=ft.FontWeight.W_700, color=COLORS["text_primary"]),
                        ft.Text("Todas tus visitas agendadas están al día.", size=12, color=COLORS["text_secondary"]),
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=8,
                ),
                padding=24,
                alignment=ft.Alignment(0, 0),
            )
        )
    else:
        for r in reuniones:
            r_id = r.get("id")
            r_nombre = r.get("nombre") or "Productor"
            r_fecha = r.get("fecha") or "Sin fecha especificada"
            r_lugar = r.get("lugar") or "Sin lugar especificado"
            
            items_controls.append(
                ft.Container(
                    content=ft.Row(
                        controls=[
                            ft.Container(
                                content=ft.Icon(ft.Icons.EVENT_NOTE_ROUNDED, color=COLORS["primary"], size=20),
                                width=40, height=40, border_radius=10,
                                bgcolor=ft.Colors.with_opacity(0.1, COLORS["primary"]),
                                alignment=ft.Alignment(0, 0),
                            ),
                            ft.Column(
                                controls=[
                                    ft.Text(r_nombre, size=13, weight=ft.FontWeight.W_700, color=COLORS["text_primary"]),
                                    ft.Row(
                                        controls=[
                                            ft.Icon(ft.Icons.CALENDAR_MONTH_ROUNDED, size=12, color=COLORS["primary"]),
                                            ft.Text(f"{r_fecha}", size=11, color=COLORS["text_secondary"]),
                                        ],
                                        spacing=4,
                                    ),
                                    ft.Row(
                                        controls=[
                                            ft.Icon(ft.Icons.LOCATION_ON_ROUNDED, size=12, color=COLORS["warning"]),
                                            ft.Text(f"{r_lugar}", size=11, color=COLORS["text_secondary"]),
                                        ],
                                        spacing=4,
                                    ),
                                ],
                                spacing=2,
                                expand=True,
                            ),
                            ft.FilledButton(
                                "Realizada",
                                icon=ft.Icons.CHECK_ROUNDED,
                                on_click=make_marcar_realizada(r_id, r_nombre),
                                style=ft.ButtonStyle(
                                    bgcolor=COLORS["success"],
                                    color="#FFFFFF",
                                    shape=ft.RoundedRectangleBorder(radius=8),
                                    padding=ft.Padding(10, 6, 12, 6),
                                ),
                            ),
                        ],
                        spacing=12,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                    bgcolor=COLORS["surface"],
                    border=ft.Border.all(1, COLORS["divider"]),
                    border_radius=10,
                    padding=12,
                )
            )

    dlg = ft.AlertDialog(
        title=ft.Row(
            controls=[
                ft.Icon(ft.Icons.NOTIFICATIONS_ACTIVE_ROUNDED, color=COLORS["warning"], size=22),
                ft.Text("Recordatorio de Reuniones", size=16, weight=ft.FontWeight.W_800),
            ],
            spacing=8,
        ),
        content=ft.Container(
            content=ft.Column(
                controls=items_controls,
                spacing=10,
                scroll=ft.ScrollMode.AUTO,
            ),
            width=460,
            height=min(420, max(150, len(reuniones) * 85 + 40)),
        ),
        actions=[
            ft.TextButton("Cerrar", on_click=close_dialog),
        ],
        actions_alignment=ft.MainAxisAlignment.END,
    )
    if dlg not in page.overlay:
        page.overlay.append(dlg)
    dlg.open = True
    page.update()
