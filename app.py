import base64
import html
import os
import re
from datetime import date, datetime
import pandas as pd
import streamlit as st
from supabase import create_client, Client

# ==============================================================================
# CONFIGURACIÓN DE PÁGINA (SIN SIDEBAR, LAYOUT AMPLIO, ESTILO FIGMA UCN)
# ==============================================================================
st.set_page_config(
    page_title="Gestión de Inasistencias · ECIEM UCN",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ==============================================================================
# CARGA DE LOGOS INSTITUCIONALES (CON FALLBACK SEGURO)
# ==============================================================================
def cargar_imagen_base64(rutas_posibles):
    for ruta in rutas_posibles:
        if os.path.exists(ruta):
            with open(ruta, "rb") as f:
                ext = os.path.splitext(ruta)[1].lower().lstrip(".")
                mime = "png" if ext == "png" else ("jpeg" if ext in ("jpg", "jpeg") else "svg+xml")
                b64 = base64.b64encode(f.read()).decode("utf-8")
                return f"data:image/{mime};base64,{b64}"
    return None

LOGO_UCN_B64 = cargar_imagen_base64(
    ["assets/logo_ucn.png", "logo_ucn.png", "assets/logo_ucn_70.png", "logo_ucn_70.png"]
)
LOGO_ECIEM_B64 = cargar_imagen_base64(
    ["assets/logo_eciem.png", "logo_eciem.png", "assets/ucn_ciencias_empresariales.png", "ucn_ciencias_empresariales.png"]
)

# ==============================================================================
# ESTILOS CSS EXACTOS AL PROTOTIPO DE FIGMA (PALETA UCN + COMPONENTES)
# ==============================================================================
CSS_FIGMA = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

:root {
    --ucn-navy-dark: #002D72;
    --ucn-navy: #003A70;
    --ucn-navy-light: #004D99;
    --ucn-gold: #E6B800;
    --ucn-text: #333333;
    --ucn-muted: #526172;
    --ucn-border: #DEE6ED;
    --ucn-soft-blue: #EAF1F8;
}

/* Ocultar chrome nativo de Streamlit y sidebar */
[data-testid="stSidebar"],
[data-testid="collapsedControl"],
#MainMenu,
footer,
header[data-testid="stHeader"] {
    display: none !important;
}

html, body, [class*="css"], .stApp {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif !important;
    color: var(--ucn-text) !important;
}

/* Fondo institucional degradado claro */
.stApp {
    background: linear-gradient(180deg, #EAF1F8 0%, #F8FAFC 100%) !important;
}

/* Contenedor principal centrado (artboard 1200px de Figma) */
.block-container {
    max-width: 1240px !important;
    padding-top: 1.2rem !important;
    padding-bottom: 3rem !important;
    padding-left: 1.5rem !important;
    padding-right: 1.5rem !important;
}

/* Botones globales estilo Figma */
div.stButton > button,
div.stDownloadButton > button,
div.stFormSubmitButton > button {
    border-radius: 8px !important;
    min-height: 44px !important;
    font-weight: 600 !important;
    font-size: 14px !important;
    transition: all 0.15s ease !important;
    box-shadow: none !important;
}

/* Botón primario azul UCN */
div.stButton > button[kind="primary"],
div.stDownloadButton > button[kind="primary"],
div.stFormSubmitButton > button[kind="primary"] {
    background-color: #003A70 !important;
    border: 1px solid #003A70 !important;
    color: #FFFFFF !important;
}
div.stButton > button[kind="primary"]:hover,
div.stDownloadButton > button[kind="primary"]:hover,
div.stFormSubmitButton > button[kind="primary"]:hover {
    background-color: #002D72 !important;
    border-color: #002D72 !important;
}

/* Botón secundario blanco borde #DEE6ED */
div.stButton > button[kind="secondary"],
div.stDownloadButton > button[kind="secondary"],
div.stFormSubmitButton > button[kind="secondary"] {
    background-color: #FFFFFF !important;
    border: 1px solid #DEE6ED !important;
    color: #003A70 !important;
}
div.stButton > button[kind="secondary"]:hover {
    background-color: #EAF1F8 !important;
    border-color: #003A70 !important;
}

/* Inputs, selectboxes y textareas claros */
div[data-baseweb="input"] > div,
div[data-baseweb="base-input"],
div[data-baseweb="select"] > div,
textarea {
    background-color: #FFFFFF !important;
    border: 1px solid #DEE6ED !important;
    border-radius: 8px !important;
    color: #333333 !important;
}
div[data-baseweb="input"] input,
textarea {
    color: #333333 !important;
    font-size: 14px !important;
}
div[data-baseweb="input"] > div:focus-within,
div[data-baseweb="select"] > div:focus-within,
textarea:focus {
    border-color: #003A70 !important;
    box-shadow: 0 0 0 1px #003A70 !important;
}

/* Etiquetas */
.stTextInput label, .stSelectbox label, .stDateInput label,
.stTextArea label, .stFileUploader label {
    color: #333333 !important;
    font-weight: 600 !important;
    font-size: 14px !important;
}

/* File uploader claro */
[data-testid="stFileUploader"] section {
    background-color: #F8FAFC !important;
    border: 1.5px dashed #B8CBE0 !important;
    border-radius: 10px !important;
}

/* Tarjetas blancas con borde Figma */
[data-testid="stVerticalBlockBorderWrapper"] {
    background-color: #FFFFFF !important;
    border: 1px solid #DEE6ED !important;
    border-radius: 12px !important;
    padding: 0.9rem 1.25rem !important;
    box-shadow: 0 2px 8px rgba(0, 45, 114, 0.04) !important;
}

/* Barra superior blanca del Login */
.ucn-topbar {
    background: #FFFFFF;
    border: 1px solid #DEE6ED;
    border-radius: 10px;
    padding: 12px 22px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 20px;
    min-height: 66px;
    box-shadow: 0 1px 4px rgba(0, 45, 114, 0.04);
}
.ucn-brand-group {
    display: flex;
    align-items: center;
    gap: 16px;
    flex-wrap: wrap;
}
.ucn-brand-logo {
    height: 40px;
    width: auto;
    object-fit: contain;
    display: block;
}
.ucn-brand-divider {
    width: 1px;
    height: 32px;
    background: #DEE6ED;
}
.ucn-brand-fallback {
    font-weight: 800;
    color: #003A70;
    font-size: 14px;
    line-height: 1.15;
}
.ucn-brand-fallback span {
    display: block;
    font-weight: 500;
    font-size: 11px;
    color: #526172;
}
.ucn-role-pill {
    font-size: 14px;
    font-weight: 600;
    color: #003A70;
    background: #EAF1F8;
    padding: 6px 14px;
    border-radius: 999px;
}
.ucn-campus-tag {
    font-size: 14px;
    font-weight: 600;
    color: #003A70;
}

/* Banner de encabezado con franja dorada UCN */
.ucn-banner {
    background: linear-gradient(90deg, #002D72 0%, #004D99 100%);
    border-left: 10px solid #E6B800;
    border-radius: 10px;
    padding: 18px 26px;
    margin-top: 12px;
    margin-bottom: 18px;
    color: #FFFFFF;
    box-shadow: 0 3px 10px rgba(0, 45, 114, 0.10);
}
.ucn-banner h1 {
    margin: 0 0 4px 0 !important;
    font-size: 28px !important;
    font-weight: 700 !important;
    color: #FFFFFF !important;
    line-height: 1.2 !important;
}
.ucn-banner p {
    margin: 0 !important;
    font-size: 14px !important;
    color: #EAF1F8 !important;
    font-weight: 400 !important;
}

/* Panel izquierdo del Login */
.ucn-login-hero {
    background: linear-gradient(160deg, #002D72 0%, #003A70 100%);
    border-right: 10px solid #E6B800;
    border-radius: 12px;
    padding: 56px 40px;
    min-height: 520px;
    display: flex;
    flex-direction: column;
    justify-content: center;
    color: #FFFFFF;
    box-shadow: 0 6px 20px rgba(0, 45, 114, 0.14);
}
.ucn-login-kicker {
    color: #E6B800;
    font-size: 13px;
    font-weight: 700;
    letter-spacing: 1.2px;
    text-transform: uppercase;
    margin-bottom: 14px;
}
.ucn-login-title {
    color: #FFFFFF;
    font-size: 38px;
    font-weight: 800;
    line-height: 1.15;
    margin: 0 0 18px 0;
}
.ucn-login-sub {
    color: #EAF1F8;
    font-size: 17px;
    line-height: 1.5;
    margin: 0 0 36px 0;
}
.ucn-login-foot {
    color: #B8CBE0;
    font-size: 12px;
    margin-top: auto;
    padding-top: 24px;
    border-top: 1px solid rgba(255, 255, 255, 0.15);
}

/* Tarjetas KPI azules grandes del Dashboard */
.ucn-kpi-card {
    background: linear-gradient(135deg, #003A70 0%, #004D99 100%);
    border: 2px solid #FFFFFF;
    border-radius: 12px;
    padding: 24px 20px;
    text-align: center;
    color: #FFFFFF;
    box-shadow: 0 4px 14px rgba(0, 45, 114, 0.12);
    margin-bottom: 16px;
}
.ucn-kpi-icon {
    font-size: 22px;
    color: #E6B800;
    margin-bottom: 4px;
}
.ucn-kpi-value {
    font-size: 38px;
    font-weight: 800;
    color: #E6B800;
    line-height: 1.1;
    margin: 2px 0 8px 0;
}
.ucn-kpi-label {
    font-size: 15px;
    font-weight: 600;
    color: #FFFFFF;
    margin-bottom: 4px;
}
.ucn-kpi-sub {
    font-size: 12px;
    color: #D2E1F0;
}

/* Títulos y ayudas */
.ucn-section-title {
    font-size: 18px;
    font-weight: 700;
    color: #003A70;
    margin: 18px 0 10px 0;
}
.ucn-helper {
    font-size: 12px;
    color: #526172;
    margin-top: -10px;
    margin-bottom: 10px;
}

/* Tablas limpias estilo Figma */
.ucn-table-wrap {
    background: #FFFFFF;
    border: 1px solid #DEE6ED;
    border-radius: 10px;
    overflow-x: auto;
    margin-bottom: 14px;
    box-shadow: 0 1px 4px rgba(0, 45, 114, 0.04);
}
table.ucn-table {
    width: 100%;
    border-collapse: collapse;
    font-size: 13px;
    color: #333333;
}
table.ucn-table thead tr {
    background-color: #EAF1F8;
    border-bottom: 1px solid #DEE6ED;
}
table.ucn-table th {
    text-align: left;
    padding: 12px 14px;
    font-size: 12px;
    font-weight: 700;
    color: #003A70;
    white-space: nowrap;
}
table.ucn-table td {
    padding: 13px 14px;
    border-bottom: 1px solid #EEF2F6;
    vertical-align: middle;
}
table.ucn-table tbody tr:last-child td {
    border-bottom: none;
}
table.ucn-table tbody tr:hover {
    background-color: #F8FAFC;
}
table.ucn-table tbody tr.ucn-row-selected {
    background-color: #EAF1F8 !important;
}

/* Badges de estado exactos del Figma */
.ucn-badge {
    display: inline-block;
    padding: 5px 14px;
    border-radius: 999px;
    font-size: 12px;
    font-weight: 600;
    text-align: center;
    min-width: 96px;
    white-space: nowrap;
}
.ucn-badge-proceso {
    background-color: #FBF4E3;
    color: #825F1A;
}
.ucn-badge-aceptado {
    background-color: #EAF5EE;
    color: #256747;
}
.ucn-badge-rechazado {
    background-color: #FCEEEE;
    color: #A73535;
}

/* Franjas informativas / alertas */
.ucn-strip-ok {
    background: #EAF5EE;
    border: 1px solid #CBE6D5;
    color: #256747;
    border-radius: 8px;
    padding: 12px 16px;
    font-size: 14px;
    font-weight: 600;
    margin-bottom: 14px;
}
.ucn-strip-err {
    background: #FCEEEE;
    border: 1px solid #F3CACA;
    color: #A73535;
    border-radius: 8px;
    padding: 11px 16px;
    font-size: 13px;
    font-weight: 600;
    margin: 6px 0 12px 0;
}
.ucn-strip-warn {
    background: #FBF4E3;
    border: 1px solid #EFE0B8;
    color: #825F1A;
    border-radius: 8px;
    padding: 11px 16px;
    font-size: 13px;
    font-weight: 500;
    margin: 10px 0 14px 0;
}
.ucn-strip-info {
    background: #EAF1F8;
    border: 1px solid #D3E2F2;
    color: #003A70;
    border-radius: 8px;
    padding: 11px 16px;
    font-size: 13px;
    font-weight: 500;
    margin: 10px 0 14px 0;
}

/* Cajas suaves de detalle */
.ucn-soft-box {
    background: #F8FAFC;
    border: 1px solid #DEE6ED;
    border-radius: 10px;
    padding: 14px 16px;
    margin-bottom: 12px;
}
.ucn-soft-box-title {
    font-size: 16px;
    font-weight: 700;
    color: #003A70;
    margin-bottom: 4px;
}
.ucn-soft-box-sub {
    font-size: 13px;
    color: #526172;
    line-height: 1.45;
}
.ucn-summary-bar {
    display: flex;
    flex-wrap: wrap;
    gap: 20px;
    background: #FFFFFF;
    border: 1px solid #DEE6ED;
    border-radius: 8px;
    padding: 11px 16px;
    font-size: 13px;
    font-weight: 600;
    color: #003A70;
    margin-bottom: 10px;
}
</style>
"""
st.markdown(CSS_FIGMA, unsafe_allow_html=True)

# ==============================================================================
# CONEXIÓN A SUPABASE
# ==============================================================================
@st.cache_resource
def get_supabase_client() -> Client:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

supabase: Client = get_supabase_client()

# ==============================================================================
# UTILIDADES DE VALIDACIÓN, FORMATO HTML Y BASE DE DATOS
# ==============================================================================
def esc(val) -> str:
    return html.escape("" if val is None else str(val))

def badge_estado_html(estado: str) -> str:
    e = (estado or "").strip()
    low = e.lower()
    if low == "aceptado":
        cls = "ucn-badge-aceptado"
    elif low == "rechazado":
        cls = "ucn-badge-rechazado"
    else:
        cls = "ucn-badge-proceso"
    return f'<span class="ucn-badge {cls}">{esc(e)}</span>'

def badge_validacion_html(texto: str) -> str:
    if texto == "Válida":
        return '<span class="ucn-badge ucn-badge-aceptado">Válida</span>'
    return f'<span class="ucn-badge ucn-badge-rechazado" style="min-width:auto;white-space:normal;text-align:left;">{esc(texto)}</span>'

def formatear_rango_inasistencia(f_ini: date, f_ter: date) -> str:
    if f_ini == f_ter:
        return f_ini.strftime("%d/%m/%Y")
    if f_ini.month == f_ter.month and f_ini.year == f_ter.year:
        return f"{f_ini.day:02d} al {f_ter.strftime('%d/%m/%Y')}"
    return f"{f_ini.strftime('%d/%m/%Y')} al {f_ter.strftime('%d/%m/%Y')}"

def normalizar_rut(rut_str: str) -> str:
    limpio = str(rut_str).strip().upper().replace(".", "").replace(" ", "")
    if "-" not in limpio and len(limpio) >= 2:
        limpio = f"{limpio[:-1]}-{limpio[-1]}"
    return limpio

def validar_rut_chileno(rut_str: str) -> bool:
    rut = normalizar_rut(rut_str)
    if "-" not in rut:
        return False
    cuerpo, dv = rut.split("-", 1)
    if not cuerpo.isdigit() or len(dv) != 1:
        return False
    suma = 0
    multiplicador = 2
    for digito in reversed(cuerpo):
        suma += int(digito) * multiplicador
        multiplicador = 2 if multiplicador == 7 else multiplicador + 1
    resto = 11 - (suma % 11)
    dv_esperado = "0" if resto == 11 else ("K" if resto == 10 else str(resto))
    return dv == dv_esperado

def validar_email(correo: str) -> bool:
    return bool(re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", correo.strip()))

def asegurar_fecha_en_dim_tiempo(fecha_obj: date) -> int:
    id_fecha = int(fecha_obj.strftime("%Y%m%d"))
    supabase.table("dim_tiempo").upsert(
        {
            "id_fecha": id_fecha,
            "fecha_completa": fecha_obj.isoformat(),
            "dia": fecha_obj.day,
            "mes": fecha_obj.month,
            "anio": fecha_obj.year,
        },
        on_conflict="id_fecha",
    ).execute()
    return id_fecha

def obtener_siguiente_numero_solicitud() -> int:
    res = (
        supabase.table("hechos_justificacion")
        .select("numero_solicitud")
        .order("numero_solicitud", desc=True)
        .limit(1)
        .execute()
    )
    if res.data:
        return int(res.data[0]["numero_solicitud"]) + 1
    return 1001

def cargar_catalogos():
    estados = supabase.table("dim_estado").select("*").order("id_estado").execute().data
    periodos = supabase.table("dim_periodo").select("*").order("id_periodo", desc=True).execute().data
    asignaturas = supabase.table("dim_asignatura").select("*").order("codigo_asignatura").execute().data
    estudiantes = supabase.table("dim_estudiante").select("*").execute().data
    return estados, periodos, asignaturas, estudiantes

def cargar_hechos_detallados() -> pd.DataFrame:
    res = (
        supabase.table("hechos_justificacion")
        .select(
            "id_hecho, numero_solicitud, id_fecha_ingreso, id_fecha_resolucion, "
            "fecha_inicio_ausencia, fecha_termino_ausencia, rut_estudiante, "
            "id_paralelo, id_estado, id_funcionario, id_periodo, "
            "dias_tramitacion, cantidad_documentos_adjuntos, tipo_documento, "
            "nombre_archivo, observacion_revision, "
            "dim_estudiante(rut, nombre_estudiante, nombre_carrera, anio_ingreso, estado_matricula), "
            "dim_asignatura(id_paralelo, codigo_asignatura, nombre_asignatura, nombre_docente), "
            "dim_estado(id_estado, nombre_estado), "
            "dim_periodo(id_periodo, nombre_periodo), "
            "dim_funcionario(id_funcionario, nombre_funcionario, rol)"
        )
        .order("numero_solicitud", desc=True)
        .execute()
    )
    if not res.data:
        return pd.DataFrame()

    filas = []
    for r in res.data:
        est = r.get("dim_estudiante") or {}
        asig = r.get("dim_asignatura") or {}
        estado = r.get("dim_estado") or {}
        per = r.get("dim_periodo") or {}
        func = r.get("dim_funcionario") or {}

        f_ing_str = str(r["id_fecha_ingreso"])
        fecha_ingreso = datetime.strptime(f_ing_str, "%Y%m%d").date() if len(f_ing_str) == 8 else None

        f_res_val = r.get("id_fecha_resolucion")
        fecha_resolucion = (
            datetime.strptime(str(f_res_val), "%Y%m%d").date()
            if f_res_val and len(str(f_res_val)) == 8
            else None
        )

        f_ini = datetime.strptime(r["fecha_inicio_ausencia"], "%Y-%m-%d").date()
        f_ter = datetime.strptime(r["fecha_termino_ausencia"], "%Y-%m-%d").date()
        dias_ausencia = (f_ter - f_ini).days + 1

        filas.append(
            {
                "id_hecho": r["id_hecho"],
                "numero_solicitud": r["numero_solicitud"],
                "fecha_ingreso": fecha_ingreso,
                "fecha_resolucion": fecha_resolucion,
                "fecha_inicio_ausencia": f_ini,
                "fecha_termino_ausencia": f_ter,
                "dias_ausencia": dias_ausencia,
                "rut_estudiante": r["rut_estudiante"],
                "nombre_estudiante": est.get("nombre_estudiante", ""),
                "nombre_carrera": est.get("nombre_carrera", ""),
                "id_paralelo": r["id_paralelo"],
                "codigo_asignatura": asig.get("codigo_asignatura", ""),
                "nombre_asignatura": asig.get("nombre_asignatura", ""),
                "nombre_docente": asig.get("nombre_docente", ""),
                "id_estado": r["id_estado"],
                "nombre_estado": estado.get("nombre_estado", ""),
                "id_periodo": r["id_periodo"],
                "nombre_periodo": per.get("nombre_periodo", ""),
                "id_funcionario": r["id_funcionario"],
                "nombre_funcionario": func.get("nombre_funcionario", ""),
                "rol_funcionario": func.get("rol", ""),
                "dias_tramitacion": r.get("dias_tramitacion"),
                "cantidad_documentos_adjuntos": r.get("cantidad_documentos_adjuntos", 0),
                "tipo_documento": r.get("tipo_documento") or "",
                "nombre_archivo": r.get("nombre_archivo") or "",
                "observacion_revision": r.get("observacion_revision") or "",
            }
        )
    return pd.DataFrame(filas)

def parsear_fecha_flexible(valor):
    if pd.isna(valor) or str(valor).strip() == "":
        return None
    texto = str(valor).strip()
    for fmt in ("%d/%m/%Y", "%Y-%m-%d", "%d-%m-%Y", "%Y/%m/%d"):
        try:
            return datetime.strptime(texto, fmt).date()
        except ValueError:
            continue
    return None

# ==============================================================================
# COMPONENTES DE LAYOUT REUTILIZABLES (TOPBAR UNIFICADA + BANNER FIGMA)
# ==============================================================================
def brand_logos_html() -> str:
    partes = []
    if LOGO_UCN_B64:
        partes.append(f'<img src="{LOGO_UCN_B64}" class="ucn-brand-logo" alt="Universidad Católica del Norte" />')
    else:
        partes.append('<div class="ucn-brand-fallback">Universidad Católica del Norte<span>1956 · 2026</span></div>')

    partes.append('<div class="ucn-brand-divider"></div>')

    if LOGO_ECIEM_B64:
        partes.append(f'<img src="{LOGO_ECIEM_B64}" class="ucn-brand-logo" alt="UCN Ciencias Empresariales" />')
    else:
        partes.append('<div class="ucn-brand-fallback">UCN CIENCIAS EMPRESARIALES<span>Escuela de Ciencias Empresariales</span></div>')

    return "".join(partes)

def render_topbar(boton_izq_texto="Inicio"):
    user = st.session_state.usuario
    rol_corto = "Secretaría" if user["rol"] == "Secretaría" else "Jefatura"

    with st.container(border=True):
        col_brand, col_nav1, col_nav2 = st.columns([6.7, 1.5, 1.8], vertical_alignment="center")
        with col_brand:
            st.markdown(
                f"""
                <div class="ucn-brand-group">
                    {brand_logos_html()}
                    <div class="ucn-brand-divider"></div>
                    <span class="ucn-role-pill">{esc(rol_corto)}</span>
                </div>
                """,
                unsafe_allow_html=True,
            )
        with col_nav1:
            if st.button(boton_izq_texto, key=f"nav_top_{boton_izq_texto}", use_container_width=True):
                st.session_state.ultima_solicitud_guardada = None
                st.session_state.ultima_carga_confirmada = None
                st.session_state.reporte_listo = False
                st.session_state.pagina = "Inicio"
                st.rerun()
        with col_nav2:
            if st.button("Cerrar sesión", key="nav_top_logout", use_container_width=True):
                st.session_state.usuario = None
                st.session_state.detalles_pendientes = []
                st.session_state.ultima_solicitud_guardada = None
                st.session_state.ultima_carga_confirmada = None
                st.session_state.reporte_listo = False
                st.session_state.pagina = "Inicio"
                st.rerun()

def render_banner(titulo: str, subtitulo: str):
    st.markdown(
        f"""
        <div class="ucn-banner">
            <h1>{esc(titulo)}</h1>
            <p>{esc(subtitulo)}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

# ==============================================================================
# ESTADO DE SESIÓN
# ==============================================================================
defaults = {
    "usuario": None,
    "pagina": "Inicio",
    "perfil_login": "Secretaría",
    "detalles_pendientes": [],
    "ultima_solicitud_guardada": None,
    "ultima_carga_confirmada": None,
    "reporte_listo": False,
    "rep_filtros": {"periodo": "2026-2", "paralelo": "Todos", "estado": "Aceptado"},
    "filtro_consulta_rut": "",
    "filtro_consulta_estado": "Todos",
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ==============================================================================
# PANTALLA 01: INICIAR SESIÓN (FIGMA PÁGINAS 1–3)
# ==============================================================================
def render_login():
    st.markdown(
        f"""
        <div class="ucn-topbar">
            <div class="ucn-brand-group">
                {brand_logos_html()}
            </div>
            <div class="ucn-campus-tag">Gestión de Inasistencias · Campus Guayacán</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    col_hero, col_card = st.columns([4.3, 5.7], gap="large")

    with col_hero:
        st.markdown(
            """
            <div class="ucn-login-hero">
                <div class="ucn-login-kicker">GESTIÓN ACADÉMICA</div>
                <div class="ucn-login-title">Gestión de<br>inasistencias</div>
                <div class="ucn-login-sub">Recepción, revisión y seguimiento de solicitudes.</div>
                <div class="ucn-login-foot">Escuela de Ciencias Empresariales · Universidad Católica del Norte</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col_card:
        with st.container(border=True):
            st.markdown(
                """
                <div style="font-size:28px;font-weight:700;color:#003A70;margin-bottom:4px;">Iniciar sesión</div>
                <div style="font-size:14px;color:#526172;margin-bottom:18px;">Selecciona tu perfil para continuar.</div>
                """,
                unsafe_allow_html=True,
            )

            p1, p2 = st.columns(2)
            es_sec = st.session_state.perfil_login == "Secretaría"
            with p1:
                if st.button(
                    "Secretaría",
                    type="primary" if es_sec else "secondary",
                    use_container_width=True,
                    key="btn_perfil_sec",
                ):
                    st.session_state.perfil_login = "Secretaría"
                    st.rerun()
            with p2:
                if st.button(
                    "Jefatura",
                    type="primary" if not es_sec else "secondary",
                    use_container_width=True,
                    key="btn_perfil_jef",
                ):
                    st.session_state.perfil_login = "Jefatura de Carrera"
                    st.rerun()

            st.markdown("<div style='height:8px;'></div>", unsafe_allow_html=True)

            placeholder_correo = (
                "secretaria.iicg@ucn.cl"
                if st.session_state.perfil_login == "Secretaría"
                else "jc.iicg.cqbo@ucn.cl"
            )

            with st.form("form_login_ucn", border=False):
                correo = st.text_input(
                    "01 · Correo institucional",
                    placeholder=placeholder_correo,
                )
                st.markdown('<div class="ucn-helper">Ej.: nombre@dominio institucional.</div>', unsafe_allow_html=True)

                contrasena = st.text_input(
                    "02 · Contraseña",
                    type="password",
                    placeholder="••••••••",
                )
                st.markdown('<div class="ucn-helper">Tu contraseña se muestra oculta.</div>', unsafe_allow_html=True)

                st.markdown("<div style='height:6px;'></div>", unsafe_allow_html=True)
                ingresar = st.form_submit_button("Ingresar", type="primary", use_container_width=True)

            if ingresar:
                if not correo.strip() or not validar_email(correo):
                    st.markdown('<div class="ucn-strip-err">Ingresa un correo válido.</div>', unsafe_allow_html=True)
                    return

                res = (
                    supabase.table("dim_funcionario")
                    .select("id_funcionario, nombre_funcionario, rol, email, contrasena")
                    .eq("email", correo.strip().lower())
                    .eq("rol", st.session_state.perfil_login)
                    .execute()
                )
                if not res.data or res.data[0]["contrasena"] != contrasena:
                    st.markdown('<div class="ucn-strip-err">Usuario o contraseña incorrectos.</div>', unsafe_allow_html=True)
                    return

                user = res.data[0]
                st.session_state.usuario = {
                    "id_funcionario": user["id_funcionario"],
                    "nombre_funcionario": user["nombre_funcionario"],
                    "rol": user["rol"],
                    "email": user["email"],
                }
                st.session_state.pagina = "Inicio"
                st.rerun()

# ==============================================================================
# PANTALLA 02: INICIO (DASHBOARD SECRETARÍA / JEFATURA — FIGMA PÁGINAS 5–6)
# ==============================================================================
def render_inicio():
    user = st.session_state.usuario
    es_secretaria = user["rol"] == "Secretaría"

    render_topbar("Inicio")
    render_banner(
        "Inicio",
        "Recibe solicitudes y organiza los antecedentes."
        if es_secretaria
        else "Consulta antecedentes y registra una decisión.",
    )

    df = cargar_hechos_detallados()
    _, periodos, _, _ = cargar_catalogos()
    periodo_actual = periodos[0]["nombre_periodo"] if periodos else "2026-2"

    total_solicitudes = df["numero_solicitud"].nunique() if not df.empty else 0
    en_proceso = (
        df[df["nombre_estado"] == "En proceso"]["numero_solicitud"].nunique()
        if not df.empty
        else 0
    )

    k1, k2 = st.columns(2, gap="medium")
    with k1:
        st.markdown(
            f"""
            <div class="ucn-kpi-card">
                <div class="ucn-kpi-icon">📋</div>
                <div class="ucn-kpi-value">{total_solicitudes}</div>
                <div class="ucn-kpi-label">Solicitudes del período</div>
                <div class="ucn-kpi-sub">{esc(periodo_actual)}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with k2:
        st.markdown(
            f"""
            <div class="ucn-kpi-card">
                <div class="ucn-kpi-icon">🕒</div>
                <div class="ucn-kpi-value">{en_proceso}</div>
                <div class="ucn-kpi-label">En proceso</div>
                <div class="ucn-kpi-sub">Pendientes de completar o revisar</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    if es_secretaria:
        b1, b2, b3, b4 = st.columns(4, gap="small")
        if b1.button("Registrar solicitud", type="primary", use_container_width=True):
            st.session_state.ultima_solicitud_guardada = None
            st.session_state.pagina = "Registrar solicitud"
            st.rerun()
        if b2.button("Consultar solicitudes", type="secondary", use_container_width=True):
            st.session_state.pagina = "Consultar solicitudes"
            st.rerun()
        if b3.button("Cargar planilla", type="secondary", use_container_width=True):
            st.session_state.ultima_carga_confirmada = None
            st.session_state.pagina = "Cargar planilla"
            st.rerun()
        if b4.button("Generar reporte", type="secondary", use_container_width=True):
            st.session_state.reporte_listo = False
            st.session_state.pagina = "Generar reporte"
            st.rerun()
    else:
        b1, b2, _ = st.columns([2.3, 2.0, 5.7], gap="small")
        if b1.button("Consultar y revisar", type="primary", use_container_width=True):
            st.session_state.pagina = "Consultar y revisar"
            st.rerun()
        if b2.button("Generar reporte", type="secondary", use_container_width=True):
            st.session_state.reporte_listo = False
            st.session_state.pagina = "Generar reporte"
            st.rerun()

    st.markdown('<div class="ucn-section-title">Solicitudes recientes</div>', unsafe_allow_html=True)

    if df.empty:
        st.markdown('<div class="ucn-strip-info">Aún no existen solicitudes registradas en Supabase.</div>', unsafe_allow_html=True)
        return

    resumen = (
        df.groupby("numero_solicitud", as_index=False)
        .agg(
            Estudiante=("nombre_estudiante", "first"),
            Entrega=("fecha_ingreso", "first"),
            Estado=("nombre_estado", "first"),
            Respaldo=("nombre_archivo", "first"),
        )
        .sort_values("numero_solicitud", ascending=False)
    )

    filas_html = []
    for _, r in resumen.iterrows():
        fecha_txt = r["Entrega"].strftime("%d/%m/%Y") if r["Entrega"] else ""
        respaldo_txt = r["Respaldo"] or "—"
        filas_html.append(
            f"<tr>"
            f"<td><strong>{esc(r['numero_solicitud'])}</strong></td>"
            f"<td>{esc(r['Estudiante'])}</td>"
            f"<td>{esc(fecha_txt)}</td>"
            f"<td>{badge_estado_html(r['Estado'])}</td>"
            f"<td>{esc(respaldo_txt)}</td>"
            f"</tr>"
        )

    st.markdown(
        f"""
        <div class="ucn-table-wrap">
            <table class="ucn-table">
                <thead>
                    <tr>
                        <th>Solicitud</th>
                        <th>Estudiante</th>
                        <th>Entrega</th>
                        <th>Estado actual</th>
                        <th>Respaldo</th>
                    </tr>
                </thead>
                <tbody>
                    {''.join(filas_html)}
                </tbody>
            </table>
        </div>
        """,
        unsafe_allow_html=True,
    )

# ==============================================================================
# PANTALLA 03: REGISTRAR SOLICITUD + SOLICITUD REGISTRADA (FIGMA PÁGINAS 8–11)
# ==============================================================================
def render_registrar_solicitud():
    if st.session_state.usuario["rol"] != "Secretaría":
        st.session_state.pagina = "Inicio"
        st.rerun()

    render_topbar("Inicio")

    if st.session_state.ultima_solicitud_guardada is not None:
        info = st.session_state.ultima_solicitud_guardada
        render_banner("Solicitud registrada", "Los antecedentes quedan disponibles para Jefatura.")
        st.markdown(
            f'<div class="ucn-strip-ok">Solicitud {esc(info["numero_solicitud"])} registrada correctamente.</div>',
            unsafe_allow_html=True,
        )

        filas_det = "".join(
            f"<tr><td>{esc(d['codigo_asignatura'])}</td>"
            f"<td>{esc(d['fecha_inicio'].strftime('%d/%m/%Y'))}</td>"
            f"<td>{esc(d['fecha_termino'].strftime('%d/%m/%Y'))}</td></tr>"
            for d in info["detalles"]
        )

        with st.container(border=True):
            st.markdown(
                f"""
                <div style="margin-bottom:10px;">{badge_estado_html('En proceso')}</div>
                <div style="font-size:22px;font-weight:700;color:#003A70;margin-bottom:6px;">{esc(info['nombre_estudiante'])}</div>
                <div style="font-size:14px;color:#526172;margin-bottom:16px;">
                    Entrega y recepción: {esc(info['fecha_entrega'].strftime('%d/%m/%Y'))} ·
                    {esc(info['nombre_archivo'])} · {len(info['detalles'])} detalle(s)
                </div>
                <div class="ucn-table-wrap" style="margin-bottom:0;">
                    <table class="ucn-table">
                        <thead><tr><th>Paralelo</th><th>Desde</th><th>Hasta</th></tr></thead>
                        <tbody>{filas_det}</tbody>
                    </table>
                </div>
                """,
                unsafe_allow_html=True,
            )

        st.markdown("<div style='height:12px;'></div>", unsafe_allow_html=True)
        c1, c2, _ = st.columns([2.2, 2.0, 5.8])
        if c1.button("Consultar solicitudes", type="primary", use_container_width=True):
            st.session_state.ultima_solicitud_guardada = None
            st.session_state.pagina = "Consultar solicitudes"
            st.rerun()
        if c2.button("Nueva solicitud", type="secondary", use_container_width=True):
            st.session_state.ultima_solicitud_guardada = None
            st.rerun()
        return

    render_banner(
        "Registrar solicitud",
        "Una solicitud puede incluir varios paralelos y períodos de inasistencia.",
    )

    estados, periodos, asignaturas, estudiantes = cargar_catalogos()
    mapa_estudiantes = {normalizar_rut(e["rut"]): e for e in estudiantes}
    estado_en_proceso = next((e["id_estado"] for e in estados if e["nombre_estado"] == "En proceso"), None)

    if not periodos or not asignaturas or estado_en_proceso is None:
        st.markdown(
            '<div class="ucn-strip-err">Faltan datos maestros en Supabase (dim_periodo, dim_asignatura o dim_estado).</div>',
            unsafe_allow_html=True,
        )
        return

    with st.container(border=True):
        r1_c1, r1_c2 = st.columns([1.05, 1.95], gap="large")
        estudiante_actual = None

        with r1_c1:
            rut_input = st.text_input("01 · RUT del estudiante", placeholder="Ej.: 12.345.678-5")
            if rut_input.strip():
                if not validar_rut_chileno(rut_input):
                    st.markdown('<div class="ucn-strip-err">El RUT no es válido. Revisa el dígito verificador.</div>', unsafe_allow_html=True)
                else:
                    estudiante_actual = mapa_estudiantes.get(normalizar_rut(rut_input))
                    if not estudiante_actual:
                        st.markdown('<div class="ucn-strip-err">Estudiante no registrado.</div>', unsafe_allow_html=True)
                    else:
                        st.markdown('<div class="ucn-helper">Estudiante validado en base de datos.</div>', unsafe_allow_html=True)
            else:
                st.markdown('<div class="ucn-helper">Busca un estudiante registrado.</div>', unsafe_allow_html=True)

        with r1_c2:
            if estudiante_actual:
                st.markdown(
                    f"""
                    <div class="ucn-soft-box" style="margin-top:24px;">
                        <div class="ucn-soft-box-title">{esc(estudiante_actual['nombre_estudiante'])}</div>
                        <div class="ucn-soft-box-sub">
                            RUT: {esc(estudiante_actual['rut'])} · {esc(estudiante_actual['nombre_carrera'])}<br>
                            Ingreso {esc(estudiante_actual['anio_ingreso'])} · {esc(estudiante_actual['estado_matricula'])}
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
            else:
                st.markdown(
                    """
                    <div class="ucn-soft-box" style="margin-top:24px;">
                        <div class="ucn-soft-box-title">Estudiante por seleccionar</div>
                        <div class="ucn-soft-box-sub">Nombre, carrera y estado de matrícula se mostrarán aquí al ingresar un RUT válido.</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

        r2_c1, r2_c2, r2_c3 = st.columns(3, gap="medium")
        with r2_c1:
            fecha_entrega = st.date_input("02 · Fecha de entrega", value=date.today(), format="DD/MM/YYYY")
            st.markdown('<div class="ucn-helper">Fecha de entrega de la solicitud.</div>', unsafe_allow_html=True)
        with r2_c2:
            fecha_recepcion = st.date_input("06 · Fecha de recepción", value=date.today(), format="DD/MM/YYYY")
            st.markdown('<div class="ucn-helper">Fecha en que se recibe el respaldo.</div>', unsafe_allow_html=True)
        with r2_c3:
            tipo_doc = st.text_input("07 · Tipo de documento", placeholder="Ej.: Certificado")
            st.markdown('<div class="ucn-helper">Describe el tipo de respaldo.</div>', unsafe_allow_html=True)

        mapa_asig = {
            f"{a['codigo_asignatura']} · {a['nombre_asignatura']} ({a['nombre_docente']})": a
            for a in asignaturas
        }
        r3_c1, r3_c2, r3_c3 = st.columns(3, gap="medium")
        with r3_c1:
            asig_label = st.selectbox("03 · Paralelo", list(mapa_asig.keys()))
            st.markdown('<div class="ucn-helper">Selecciona un paralelo existente.</div>', unsafe_allow_html=True)
        with r3_c2:
            f_inicio = st.date_input("04 · Fecha de inicio", value=date.today(), format="DD/MM/YYYY")
            st.markdown('<div class="ucn-helper">Primer día de inasistencia.</div>', unsafe_allow_html=True)
        with r3_c3:
            f_termino = st.date_input("05 · Fecha de término", value=date.today(), format="DD/MM/YYYY")
            if f_termino < f_inicio:
                st.markdown(
                    '<div class="ucn-strip-err">La fecha de término no puede ser anterior al inicio.</div>',
                    unsafe_allow_html=True,
                )
            else:
                st.markdown('<div class="ucn-helper">Igual o posterior a la fecha de inicio.</div>', unsafe_allow_html=True)

        a1, a2 = st.columns([3.2, 1.3], vertical_alignment="center")
        with a1:
            st.markdown(
                '<div style="font-size:13px;color:#526172;">Agrega otro detalle si la solicitud abarca más de un paralelo.</div>',
                unsafe_allow_html=True,
            )
        with a2:
            if st.button("+ Agregar inasistencia", type="secondary", use_container_width=True):
                if f_termino < f_inicio:
                    st.markdown(
                        '<div class="ucn-strip-err">La fecha de término no puede ser anterior al inicio.</div>',
                        unsafe_allow_html=True,
                    )
                else:
                    asig_obj = mapa_asig[asig_label]
                    if any(d["id_paralelo"] == asig_obj["id_paralelo"] for d in st.session_state.detalles_pendientes):
                        st.markdown('<div class="ucn-strip-warn">Ese paralelo ya fue agregado a esta solicitud.</div>', unsafe_allow_html=True)
                    else:
                        st.session_state.detalles_pendientes.append(
                            {
                                "id_paralelo": asig_obj["id_paralelo"],
                                "codigo_asignatura": asig_obj["codigo_asignatura"],
                                "nombre_asignatura": asig_obj["nombre_asignatura"],
                                "fecha_inicio": f_inicio,
                                "fecha_termino": f_termino,
                            }
                        )
                        st.rerun()

        if st.session_state.detalles_pendientes:
            filas_p = "".join(
                f"<tr><td><strong>Detalle {i+1}</strong></td>"
                f"<td>{esc(d['codigo_asignatura'])} — {esc(d['nombre_asignatura'])}</td>"
                f"<td>{esc(d['fecha_inicio'].strftime('%d/%m/%Y'))}</td>"
                f"<td>{esc(d['fecha_termino'].strftime('%d/%m/%Y'))}</td></tr>"
                for i, d in enumerate(st.session_state.detalles_pendientes)
            )
            st.markdown(
                f"""
                <div class="ucn-table-wrap" style="margin-top:10px;">
                    <table class="ucn-table">
                        <thead><tr><th>#</th><th>Paralelo</th><th>Desde</th><th>Hasta</th></tr></thead>
                        <tbody>{filas_p}</tbody>
                    </table>
                </div>
                """,
                unsafe_allow_html=True,
            )
            if st.button("Quitar detalles agregados", type="secondary"):
                st.session_state.detalles_pendientes = []
                st.rerun()

        st.markdown("<hr style='border:none;border-top:1px solid #EEF2F6;margin:14px 0;'>", unsafe_allow_html=True)
        r4_c1, r4_c2 = st.columns([2.1, 1.0], gap="large")
        with r4_c1:
            archivo_respaldo = st.file_uploader(
                "08 · Respaldo recibido",
                type=["pdf", "png", "jpg", "jpeg"],
            )
            if archivo_respaldo is not None:
                st.markdown(
                    f'<div class="ucn-strip-ok">✓ Respaldo recibido ({esc(archivo_respaldo.name)}) y revisado por Secretaría.</div>',
                    unsafe_allow_html=True,
                )
            else:
                st.markdown('<div class="ucn-helper">La revisión del respaldo la realiza Secretaría.</div>', unsafe_allow_html=True)
        with r4_c2:
            periodo_opciones = {p["nombre_periodo"]: p["id_periodo"] for p in periodos}
            periodo_sel = st.selectbox("Período académico", list(periodo_opciones.keys()))
            st.markdown('<div class="ucn-helper">Período vigente para el registro.</div>', unsafe_allow_html=True)

    st.markdown("<div style='height:10px;'></div>", unsafe_allow_html=True)
    bt1, bt2, _ = st.columns([2.2, 1.6, 6.2], gap="small")
    guardar_clic = bt1.button("Guardar solicitud", type="primary", use_container_width=True)
    cancelar_clic = bt2.button("Cancelar", type="secondary", use_container_width=True)

    if cancelar_clic:
        st.session_state.detalles_pendientes = []
        st.session_state.pagina = "Inicio"
        st.rerun()

    if guardar_clic:
        detalles_a_guardar = list(st.session_state.detalles_pendientes)
        if not detalles_a_guardar and f_termino >= f_inicio:
            asig_obj = mapa_asig[asig_label]
            detalles_a_guardar.append(
                {
                    "id_paralelo": asig_obj["id_paralelo"],
                    "codigo_asignatura": asig_obj["codigo_asignatura"],
                    "nombre_asignatura": asig_obj["nombre_asignatura"],
                    "fecha_inicio": f_inicio,
                    "fecha_termino": f_termino,
                }
            )

        errores = []
        if not rut_input.strip() or not validar_rut_chileno(rut_input):
            errores.append("El RUT no es válido. Revisa el dígito verificador.")
        elif estudiante_actual is None:
            errores.append("Estudiante no registrado.")
        if f_termino < f_inicio and not st.session_state.detalles_pendientes:
            errores.append("La fecha de término no puede ser anterior al inicio.")
        if not detalles_a_guardar:
            errores.append("Selecciona un paralelo válido.")
        if not tipo_doc.strip() or archivo_respaldo is None:
            errores.append("Completa el tipo de documento y selecciona un respaldo.")

        if errores:
            for e_msg in errores:
                st.markdown(f'<div class="ucn-strip-err">{esc(e_msg)}</div>', unsafe_allow_html=True)
            return

        id_fecha_ingreso = asegurar_fecha_en_dim_tiempo(fecha_entrega)
        num_solicitud = obtener_siguiente_numero_solicitud()
        id_periodo = periodo_opciones[periodo_sel]
        id_funcionario = st.session_state.usuario["id_funcionario"]

        registros = []
        for det in detalles_a_guardar:
            registros.append(
                {
                    "numero_solicitud": num_solicitud,
                    "id_fecha_ingreso": id_fecha_ingreso,
                    "id_fecha_resolucion": None,
                    "fecha_inicio_ausencia": det["fecha_inicio"].isoformat(),
                    "fecha_termino_ausencia": det["fecha_termino"].isoformat(),
                    "rut_estudiante": estudiante_actual["rut"],
                    "id_paralelo": det["id_paralelo"],
                    "id_estado": estado_en_proceso,
                    "id_funcionario": id_funcionario,
                    "id_periodo": id_periodo,
                    "dias_tramitacion": None,
                    "cantidad_documentos_adjuntos": 1,
                    "tipo_documento": tipo_doc.strip(),
                    "nombre_archivo": archivo_respaldo.name,
                    "observacion_revision": f"Solicitud recibida por Secretaría ({fecha_recepcion.strftime('%d/%m/%Y')}).",
                }
            )

        supabase.table("hechos_justificacion").insert(registros).execute()
        st.session_state.detalles_pendientes = []
        st.session_state.ultima_solicitud_guardada = {
            "numero_solicitud": num_solicitud,
            "nombre_estudiante": estudiante_actual["nombre_estudiante"],
            "fecha_entrega": fecha_entrega,
            "nombre_archivo": archivo_respaldo.name,
            "detalles": detalles_a_guardar,
        }
        st.rerun()

# ==============================================================================
# PANTALLA 04: CONSULTAR SOLICITUDES / CONSULTAR Y REVISAR (FIGMA PÁGINAS 13–15)
# ==============================================================================
def render_consultar_revisar():
    es_jefatura = st.session_state.usuario["rol"] != "Secretaría"

    render_topbar("Inicio")
    render_banner(
        "Consultar y revisar" if es_jefatura else "Consultar solicitudes",
        "Revisa el respaldo y deja registro de la decisión."
        if es_jefatura
        else "Busca por estudiante o estado actual.",
    )

    df = cargar_hechos_detallados()
    estados, _, _, _ = cargar_catalogos()
    mapa_estados = {e["nombre_estado"]: e["id_estado"] for e in estados}
    lista_estados = ["Todos"] + list(mapa_estados.keys())

    # ---- VERSIÓN SECRETARÍA (SOLO LECTURA) ----
    if not es_jefatura:
        f1, f2, f3 = st.columns([2.2, 2.2, 1.1], vertical_alignment="bottom")
        with f1:
            rut_q = st.text_input(
                "RUT del estudiante",
                value=st.session_state.filtro_consulta_rut,
                placeholder="Ej.: 12.345.678-5",
            )
            st.markdown('<div class="ucn-helper">Deja vacío para ver todos.</div>', unsafe_allow_html=True)
        with f2:
            idx_e = lista_estados.index(st.session_state.filtro_consulta_estado) if st.session_state.filtro_consulta_estado in lista_estados else 0
            est_q = st.selectbox("Estado actual", lista_estados, index=idx_e)
            st.markdown('<div class="ucn-helper">En proceso / Aceptado / Rechazado.</div>', unsafe_allow_html=True)
        with f3:
            if st.button("Buscar", type="primary", use_container_width=True):
                st.session_state.filtro_consulta_rut = rut_q
                st.session_state.filtro_consulta_estado = est_q
                st.rerun()
            st.markdown("<div style='height:18px;'></div>", unsafe_allow_html=True)

        df_fil = df.copy()
        if not df_fil.empty:
            if rut_q.strip():
                q_low = rut_q.strip().lower()
                q_rut = normalizar_rut(rut_q).lower()
                df_fil = df_fil[
                    df_fil["rut_estudiante"].str.lower().str.contains(q_rut, na=False)
                    | df_fil["nombre_estudiante"].str.lower().str.contains(q_low, na=False)
                ]
            if est_q != "Todos":
                df_fil = df_fil[df_fil["nombre_estado"] == est_q]

        if df_fil.empty:
            with st.container(border=True):
                st.markdown(
                    """
                    <div style="font-size:18px;font-weight:700;color:#003A70;margin-bottom:4px;">Sin resultados</div>
                    <div style="font-size:14px;color:#526172;margin-bottom:12px;">
                        Revisa el RUT o limpia los filtros para volver al listado.
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
                if st.button("Limpiar filtros", type="secondary"):
                    st.session_state.filtro_consulta_rut = ""
                    st.session_state.filtro_consulta_estado = "Todos"
                    st.rerun()
            return

        filas_html = []
        for _, r in df_fil.iterrows():
            f_ent = r["fecha_ingreso"].strftime("%d/%m/%Y") if r["fecha_ingreso"] else ""
            rango = formatear_rango_inasistencia(r["fecha_inicio_ausencia"], r["fecha_termino_ausencia"])
            filas_html.append(
                f"<tr>"
                f"<td><strong>{esc(r['numero_solicitud'])}</strong></td>"
                f"<td>{esc(r['nombre_estudiante'])}</td>"
                f"<td>{esc(f_ent)}</td>"
                f"<td>{esc(r['codigo_asignatura'])}</td>"
                f"<td>{esc(rango)}</td>"
                f"<td>{badge_estado_html(r['nombre_estado'])}</td>"
                f"</tr>"
            )

        st.markdown(
            f"""
            <div class="ucn-table-wrap">
                <table class="ucn-table">
                    <thead>
                        <tr>
                            <th>Solicitud</th>
                            <th>Estudiante</th>
                            <th>Entrega</th>
                            <th>Paralelo</th>
                            <th>Inasistencia</th>
                            <th>Estado actual</th>
                        </tr>
                    </thead>
                    <tbody>{''.join(filas_html)}</tbody>
                </table>
            </div>
            <div class="ucn-strip-info">La revisión y la decisión corresponden a Jefatura.</div>
            """,
            unsafe_allow_html=True,
        )
        return

    # ---- VERSIÓN JEFATURA (PANEL DIVIDIDO MAESTRO-DETALLE) ----
    col_izq, col_der = st.columns([5.3, 4.7], gap="large")

    with col_izq:
        f1, f2 = st.columns(2, gap="small")
        with f1:
            rut_q = st.text_input(
                "RUT / estudiante",
                value=st.session_state.filtro_consulta_rut,
                placeholder="Ej.: 12.345.678-5",
            )
            st.markdown('<div class="ucn-helper">Buscar en solicitudes.</div>', unsafe_allow_html=True)
        with f2:
            idx_e = lista_estados.index(st.session_state.filtro_consulta_estado) if st.session_state.filtro_consulta_estado in lista_estados else 0
            est_q = st.selectbox("Estado actual", lista_estados, index=idx_e)
            st.markdown('<div class="ucn-helper">Filtra por estado del registro.</div>', unsafe_allow_html=True)

        if st.button("Buscar", type="primary", use_container_width=True):
            st.session_state.filtro_consulta_rut = rut_q
            st.session_state.filtro_consulta_estado = est_q
            st.rerun()

        df_fil = df.copy()
        if not df_fil.empty:
            if rut_q.strip():
                q_low = rut_q.strip().lower()
                q_rut = normalizar_rut(rut_q).lower()
                df_fil = df_fil[
                    df_fil["rut_estudiante"].str.lower().str.contains(q_rut, na=False)
                    | df_fil["nombre_estudiante"].str.lower().str.contains(q_low, na=False)
                ]
            if est_q != "Todos":
                df_fil = df_fil[df_fil["nombre_estado"] == est_q]

        if df_fil.empty:
            with st.container(border=True):
                st.markdown(
                    '<div style="font-size:16px;font-weight:700;color:#003A70;">Sin resultados</div>'
                    '<div style="font-size:13px;color:#526172;margin:4px 0 10px 0;">Revisa el RUT o limpia los filtros.</div>',
                    unsafe_allow_html=True,
                )
                if st.button("Limpiar filtros", type="secondary"):
                    st.session_state.filtro_consulta_rut = ""
                    st.session_state.filtro_consulta_estado = "Todos"
                    st.rerun()
            return

        resumen_sol = (
            df_fil.groupby("numero_solicitud", as_index=False)
            .agg(
                Estudiante=("nombre_estudiante", "first"),
                Entrega=("fecha_ingreso", "first"),
                Estado=("nombre_estado", "first"),
            )
            .sort_values("numero_solicitud", ascending=False)
        )

        opciones_sol = resumen_sol["numero_solicitud"].tolist()
        sol_sel = st.selectbox(
            "Seleccionar solicitud para revisar",
            opciones_sol,
            format_func=lambda s: f"Solicitud {s} — {resumen_sol[resumen_sol['numero_solicitud'] == s]['Estudiante'].iloc[0]}",
        )

        filas_html = []
        for _, r in resumen_sol.iterrows():
            f_ent = r["Entrega"].strftime("%d/%m/%Y") if r["Entrega"] else ""
            row_cls = ' class="ucn-row-selected"' if r["numero_solicitud"] == sol_sel else ""
            filas_html.append(
                f"<tr{row_cls}>"
                f"<td><strong>{esc(r['numero_solicitud'])}</strong></td>"
                f"<td>{esc(r['Estudiante'])}</td>"
                f"<td>{esc(f_ent)}</td>"
                f"<td>{badge_estado_html(r['Estado'])}</td>"
                f"</tr>"
            )

        st.markdown(
            f"""
            <div class="ucn-table-wrap">
                <table class="ucn-table">
                    <thead>
                        <tr><th>Solicitud</th><th>Estudiante</th><th>Entrega</th><th>Estado</th></tr>
                    </thead>
                    <tbody>{''.join(filas_html)}</tbody>
                </table>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col_der:
        filas_sol = df[df["numero_solicitud"] == sol_sel]
        primera = filas_sol.iloc[0]

        detalles_txt = "<br>".join(
            f"<strong>{esc(r['codigo_asignatura'])}</strong> · "
            f"{esc(formatear_rango_inasistencia(r['fecha_inicio_ausencia'], r['fecha_termino_ausencia']))}"
            for _, r in filas_sol.iterrows()
        )
        f_ing_txt = primera["fecha_ingreso"].strftime("%d/%m/%Y") if primera["fecha_ingreso"] else "—"
        f_res_txt = primera["fecha_resolucion"].strftime("%d/%m/%Y") if primera["fecha_resolucion"] else f_ing_txt

        with st.container(border=True):
            st.markdown(
                f"""
                <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:10px;">
                    <div style="font-size:22px;font-weight:700;color:#003A70;">Solicitud {esc(sol_sel)}</div>
                    <div>{badge_estado_html(primera['nombre_estado'])}</div>
                </div>
                <div style="font-size:14px;color:#333333;margin-bottom:8px;">
                    <strong>{esc(primera['nombre_estudiante'])}</strong> · {esc(primera['rut_estudiante'])}
                </div>
                <div style="font-size:13px;color:#526172;margin-bottom:12px;">
                    {detalles_txt}
                </div>
                <div class="ucn-soft-box">
                    <div class="ucn-soft-box-title" style="font-size:14px;">
                        📄 {esc(primera['nombre_archivo'] or 'Sin archivo')} · {esc(primera['tipo_documento'] or 'Certificado')}
                    </div>
                    <div class="ucn-soft-box-sub">
                        Recibido el {esc(f_ing_txt)}<br>
                        Revisión del contenido a cargo de Jefatura.
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            observacion = st.text_area(
                "09 · Observación de la revisión",
                value=primera["observacion_revision"],
                placeholder="Deja un motivo al rechazar o pedir antecedentes.",
                height=90,
                key=f"obs_rev_{sol_sel}",
            )
            st.markdown(
                '<div class="ucn-helper">Deja un motivo al rechazar o pedir antecedentes.</div>',
                unsafe_allow_html=True,
            )

            b1, b2, b3 = st.columns([1.0, 1.0, 1.45], gap="small")
            accion = None
            if b1.button("Aceptar", type="primary", use_container_width=True, key=f"ac_{sol_sel}"):
                accion = "Aceptado"
            if b2.button("Rechazar", type="secondary", use_container_width=True, key=f"re_{sol_sel}"):
                accion = "Rechazado"
            if b3.button("Solicitar antecedentes", type="secondary", use_container_width=True, key=f"an_{sol_sel}"):
                accion = "En proceso"

            if accion:
                if accion in ("Rechazado", "En proceso") and not observacion.strip():
                    st.markdown('<div class="ucn-strip-err">Describe el motivo de la decisión.</div>', unsafe_allow_html=True)
                else:
                    id_nuevo_estado = mapa_estados[accion]
                    hoy = date.today()
                    id_fecha_res = None
                    dias_tram = None

                    if accion in ("Aceptado", "Rechazado"):
                        id_fecha_res = asegurar_fecha_en_dim_tiempo(hoy)
                        f_ing = primera["fecha_ingreso"]
                        dias_tram = max(0, (hoy - f_ing).days) if f_ing else 0

                    obs_final = observacion.strip() or "Antecedentes revisados: justifican el período solicitado."

                    supabase.table("hechos_justificacion").update(
                        {
                            "id_estado": id_nuevo_estado,
                            "id_funcionario": st.session_state.usuario["id_funcionario"],
                            "id_fecha_resolucion": id_fecha_res,
                            "dias_tramitacion": dias_tram,
                            "observacion_revision": obs_final,
                        }
                    ).eq("numero_solicitud", int(sol_sel)).execute()
                    st.rerun()

            st.markdown(
                f"""
                <div style="margin-top:14px;padding-top:12px;border-top:1px solid #EEF2F6;">
                    <div style="font-size:13px;font-weight:700;color:#003A70;margin-bottom:6px;">
                        Historial de la solicitud {esc(sol_sel)}
                    </div>
                    <div style="font-size:12px;color:#526172;line-height:1.5;">
                        <strong>{esc(f_res_txt)}</strong> · {esc(primera['nombre_funcionario'])} ({esc(primera['rol_funcionario'])}) ·
                        <strong>{esc(primera['nombre_estado'])}</strong><br>
                        {esc(primera['observacion_revision'] or 'Solicitud recibida.')}
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

# ==============================================================================
# PANTALLA 05: CARGAR PLANILLA + CARGA CONFIRMADA (FIGMA PÁGINAS 17–18)
# ==============================================================================
def render_cargar_planilla():
    if st.session_state.usuario["rol"] != "Secretaría":
        st.session_state.pagina = "Inicio"
        st.rerun()

    render_topbar("Inicio")

    if st.session_state.ultima_carga_confirmada is not None:
        res = st.session_state.ultima_carga_confirmada
        render_banner("Carga confirmada", "Resultado de la incorporación desde planilla.")
        st.markdown(
            f'<div class="ucn-strip-ok">{res["validas"]} registro(s) cargado(s). {res["errores"]} fila(s) omitida(s) por error.</div>',
            unsafe_allow_html=True,
        )
        with st.container(border=True):
            st.markdown(
                f"""
                <div style="font-size:20px;font-weight:700;color:#003A70;margin-bottom:8px;">{esc(res['archivo'])}</div>
                <div style="font-size:14px;color:#333333;line-height:1.6;">
                    Las filas válidas quedaron incorporadas en <strong>Supabase</strong> (omitiendo Mail y Diagnóstico por privacidad).<br>
                    {f"Corrige las {res['errores']} fila(s) con observaciones antes de volver a cargarlas." if res["errores"] > 0 else "No se detectaron errores en la planilla."}
                </div>
                """,
                unsafe_allow_html=True,
            )
        st.markdown("<div style='height:12px;'></div>", unsafe_allow_html=True)
        b1, b2, _ = st.columns([2.0, 2.0, 6.0])
        if b1.button("Nueva carga", type="primary", use_container_width=True):
            st.session_state.ultima_carga_confirmada = None
            st.rerun()
        if b2.button("Volver al inicio", type="secondary", use_container_width=True):
            st.session_state.ultima_carga_confirmada = None
            st.session_state.pagina = "Inicio"
            st.rerun()
        return

    render_banner("Cargar planilla", "Vista previa y validación antes de incorporar los registros a Supabase.")

    estados, periodos, asignaturas, estudiantes = cargar_catalogos()
    periodo_opciones = {p["nombre_periodo"]: p["id_periodo"] for p in periodos}

    with st.container(border=True):
        c1, c2 = st.columns([2.2, 1.0], gap="large")
        with c1:
            archivo = st.file_uploader(
                "Archivo de entrada (.csv o .xlsx — formato Entrada Ejemplo)",
                type=["csv", "xlsx"],
            )
        with c2:
            periodo_sel = st.selectbox("Período académico", list(periodo_opciones.keys()))
            st.markdown('<div class="ucn-helper">Período asignado a la carga.</div>', unsafe_allow_html=True)

        st.markdown(
            '<div class="ucn-strip-info" style="margin-bottom:0;">'
            'Política de gobernanza: las columnas <strong>Mail</strong> y <strong>Diagnostico</strong> '
            'se omiten automáticamente para resguardar privacidad médica y evitar redundancia.</div>',
            unsafe_allow_html=True,
        )

    if not archivo:
        return

    try:
        df_raw = pd.read_csv(archivo) if archivo.name.endswith(".csv") else pd.read_excel(archivo)
    except Exception as exc:
        st.markdown(f'<div class="ucn-strip-err">No se pudo leer el archivo: {esc(exc)}</div>', unsafe_allow_html=True)
        return

    df_raw.columns = [str(c).strip() for c in df_raw.columns]
    columnas_requeridas = [
        "Rut", "Nombre", "Asignatura", "Docente",
        "Fecha Entrega", "Fecha inicio", "Fecha Termino",
        "Validación JC", "Fecha Validación",
    ]
    faltantes = [c for c in columnas_requeridas if c not in df_raw.columns]
    if faltantes:
        st.markdown(
            f'<div class="ucn-strip-err">Faltan columnas obligatorias: {esc(", ".join(faltantes))}</div>',
            unsafe_allow_html=True,
        )
        return

    if df_raw.empty:
        st.markdown(
            '<div class="ucn-strip-warn">La planilla seleccionada solo contiene encabezados (0 filas de datos).</div>',
            unsafe_allow_html=True,
        )
        return

    mapa_est = {normalizar_rut(e["rut"]): e for e in estudiantes}
    mapa_estados = {e["nombre_estado"].lower(): e["id_estado"] for e in estados}

    def buscar_paralelo(asig_txt: str, doc_txt: str):
        a_clean = str(asig_txt).strip().lower()
        d_clean = str(doc_txt).strip().lower()
        for a in asignaturas:
            if a["codigo_asignatura"].strip().lower() == a_clean or a["nombre_asignatura"].strip().lower() == a_clean:
                if not d_clean or a["nombre_docente"].strip().lower() == d_clean:
                    return a
        return None

    def mapear_estado(texto_val):
        if pd.isna(texto_val) or str(texto_val).strip() == "":
            return mapa_estados.get("en proceso")
        t = str(texto_val).strip().lower()
        if t in ("aprobado", "aceptado", "si", "sí"):
            return mapa_estados.get("aceptado")
        if t in ("rechazado", "no"):
            return mapa_estados.get("rechazado")
        if t in ("en proceso", "pendiente"):
            return mapa_estados.get("en proceso")
        return None

    vista_previa = []
    filas_validas = []
    claves_vistas = set()

    for idx, row in df_raw.iterrows():
        fila_excel = idx + 2
        errores_fila = []

        rut_raw = "" if pd.isna(row["Rut"]) else str(row["Rut"]).strip()
        rut_norm = normalizar_rut(rut_raw)
        est_obj = mapa_est.get(rut_norm)
        if not rut_raw or not validar_rut_chileno(rut_raw):
            errores_fila.append("RUT inválido")
        elif est_obj is None:
            errores_fila.append(f"RUT {rut_norm} no existe en dim_estudiante")

        asig_raw = "" if pd.isna(row["Asignatura"]) else str(row["Asignatura"]).strip()
        doc_raw = "" if pd.isna(row["Docente"]) else str(row["Docente"]).strip()
        asig_obj = buscar_paralelo(asig_raw, doc_raw)
        if asig_obj is None:
            errores_fila.append(f"Paralelo/Docente '{asig_raw}' inexistente")

        f_entrega = parsear_fecha_flexible(row["Fecha Entrega"])
        f_ini = parsear_fecha_flexible(row["Fecha inicio"])
        f_ter = parsear_fecha_flexible(row["Fecha Termino"])
        f_val = parsear_fecha_flexible(row["Fecha Validación"])

        if f_entrega is None:
            errores_fila.append("Fecha Entrega inválida")
        if f_ini is None or f_ter is None:
            errores_fila.append("Fechas de inasistencia inválidas")
        elif f_ter < f_ini:
            errores_fila.append("Término anterior a inicio")

        id_estado = mapear_estado(row["Validación JC"])
        if id_estado is None:
            errores_fila.append(f"Estado '{row['Validación JC']}' no reconocido")
        if f_val is not None and f_entrega is not None and f_val < f_entrega:
            errores_fila.append("Fecha Validación anterior a Entrega")

        if not errores_fila:
            clave_u = (est_obj["rut"], f_entrega.isoformat(), asig_obj["id_paralelo"])
            if clave_u in claves_vistas:
                errores_fila.append("Fila duplicada en el archivo")
            else:
                claves_vistas.add(clave_u)

        val_txt = "Válida" if not errores_fila else "Error: " + "; ".join(errores_fila)
        vista_previa.append(
            (fila_excel, rut_raw, row["Nombre"], asig_raw, doc_raw, row["Fecha inicio"], row["Fecha Termino"], val_txt)
        )
        if not errores_fila:
            filas_validas.append(
                {
                    "rut_estudiante": est_obj["rut"],
                    "id_paralelo": asig_obj["id_paralelo"],
                    "fecha_entrega": f_entrega,
                    "fecha_inicio": f_ini,
                    "fecha_termino": f_ter,
                    "id_estado": id_estado,
                    "fecha_validacion": f_val,
                }
            )

    filas_html = "".join(
        f"<tr><td>{esc(f[0])}</td><td>{esc(f[1])}</td><td>{esc(f[2])}</td>"
        f"<td>{esc(f[3])}</td><td>{esc(f[4])}</td><td>{esc(f[5])}</td>"
        f"<td>{esc(f[6])}</td><td>{badge_validacion_html(f[7])}</td></tr>"
        for f in vista_previa
    )

    st.markdown(
        f"""
        <div class="ucn-section-title">Vista previa: {esc(archivo.name)}</div>
        <div class="ucn-table-wrap">
            <table class="ucn-table">
                <thead>
                    <tr>
                        <th>Fila</th><th>RUT</th><th>Nombre</th><th>Asignatura</th>
                        <th>Docente</th><th>Inicio</th><th>Término</th><th>Validación</th>
                    </tr>
                </thead>
                <tbody>{filas_html}</tbody>
            </table>
        </div>
        """,
        unsafe_allow_html=True,
    )

    n_val = len(filas_validas)
    n_err = len(vista_previa) - n_val
    b1, b2, _ = st.columns([2.6, 1.5, 5.9], gap="small")

    if n_val > 0 and b1.button(f"Cargar {n_val} fila(s) válida(s)", type="primary", use_container_width=True):
        siguiente_num = obtener_siguiente_numero_solicitud()
        mapa_sol = {}
        registros_insert = []
        id_func = st.session_state.usuario["id_funcionario"]
        id_periodo_sel = periodo_opciones[periodo_sel]

        for item in filas_validas:
            clave_g = (item["rut_estudiante"], item["fecha_entrega"].isoformat())
            if clave_g not in mapa_sol:
                mapa_sol[clave_g] = siguiente_num
                siguiente_num += 1
            num_sol = mapa_sol[clave_g]

            id_f_ing = asegurar_fecha_en_dim_tiempo(item["fecha_entrega"])
            id_f_res = asegurar_fecha_en_dim_tiempo(item["fecha_validacion"]) if item["fecha_validacion"] else None
            dias_tram = max(0, (item["fecha_validacion"] - item["fecha_entrega"]).days) if item["fecha_validacion"] else None

            registros_insert.append(
                {
                    "numero_solicitud": num_sol,
                    "id_fecha_ingreso": id_f_ing,
                    "id_fecha_resolucion": id_f_res,
                    "fecha_inicio_ausencia": item["fecha_inicio"].isoformat(),
                    "fecha_termino_ausencia": item["fecha_termino"].isoformat(),
                    "rut_estudiante": item["rut_estudiante"],
                    "id_paralelo": item["id_paralelo"],
                    "id_estado": item["id_estado"],
                    "id_funcionario": id_func,
                    "id_periodo": id_periodo_sel,
                    "dias_tramitacion": dias_tram,
                    "cantidad_documentos_adjuntos": 1,
                    "tipo_documento": "Carga masiva",
                    "nombre_archivo": archivo.name,
                    "observacion_revision": "Importado desde planilla operativa.",
                }
            )

        supabase.table("hechos_justificacion").insert(registros_insert).execute()
        st.session_state.ultima_carga_confirmada = {
            "archivo": archivo.name,
            "validas": n_val,
            "errores": n_err,
        }
        st.rerun()

    if b2.button("Cancelar", type="secondary", use_container_width=True):
        st.session_state.pagina = "Inicio"
        st.rerun()

# ==============================================================================
# PANTALLA 06: GENERAR REPORTE / REPORTE LISTO (FIGMA PÁGINAS 20–21)
# ==============================================================================
def render_generar_reporte():
    render_topbar("Volver")

    df = cargar_hechos_detallados()
    estados, periodos, asignaturas, _ = cargar_catalogos()
    nombres_periodos = [p["nombre_periodo"] for p in periodos]
    paralelos_opc = ["Todos"] + [a["codigo_asignatura"] for a in asignaturas]
    estados_opc = [e["nombre_estado"] for e in estados]

    filtros_guardados = st.session_state.rep_filtros
    idx_per = nombres_periodos.index(filtros_guardados["periodo"]) if filtros_guardados["periodo"] in nombres_periodos else 0
    idx_par = paralelos_opc.index(filtros_guardados["paralelo"]) if filtros_guardados["paralelo"] in paralelos_opc else 0
    idx_est = estados_opc.index(filtros_guardados["estado"]) if filtros_guardados["estado"] in estados_opc else (
        estados_opc.index("Aceptado") if "Aceptado" in estados_opc else 0
    )

    if not st.session_state.reporte_listo:
        render_banner("Generar reporte", "Inasistencias aceptadas del período seleccionado.")
        c1, c2, c3 = st.columns(3, gap="medium")
        with c1:
            periodo_sel = st.selectbox("Período académico", nombres_periodos, index=idx_per)
            st.markdown('<div class="ucn-helper">Selecciona un período existente.</div>', unsafe_allow_html=True)
        with c2:
            paralelo_sel = st.selectbox("Paralelo", paralelos_opc, index=idx_par)
            st.markdown('<div class="ucn-helper">Opcional: limita a un paralelo.</div>', unsafe_allow_html=True)
        with c3:
            estado_sel = st.selectbox("Estado actual", estados_opc, index=idx_est)
            st.markdown('<div class="ucn-helper">Estado incluido en esta salida.</div>', unsafe_allow_html=True)
    else:
        periodo_sel = filtros_guardados["periodo"]
        paralelo_sel = filtros_guardados["paralelo"]
        estado_sel = filtros_guardados["estado"]
        render_banner("Reporte listo", "Inasistencias aceptadas del período seleccionado.")
        st.markdown(
            f'<div class="ucn-strip-ok">inasistencias_{esc(periodo_sel)}.csv · Reporte listo</div>',
            unsafe_allow_html=True,
        )

    if df.empty:
        st.markdown('<div class="ucn-strip-info">No hay registros disponibles para generar reportes.</div>', unsafe_allow_html=True)
        return

    df_rep = df[(df["nombre_periodo"] == periodo_sel) & (df["nombre_estado"] == estado_sel)].copy()
    if paralelo_sel != "Todos":
        df_rep = df_rep[df_rep["codigo_asignatura"] == paralelo_sel]

    if df_rep.empty:
        st.markdown('<div class="ucn-strip-warn">No existen registros para los filtros seleccionados.</div>', unsafe_allow_html=True)
        if st.session_state.reporte_listo and st.button("Cambiar filtros", type="secondary"):
            st.session_state.reporte_listo = False
            st.rerun()
        return

    df_rep = df_rep.sort_values(["numero_solicitud", "codigo_asignatura"])

    filas_html = []
    for _, r in df_rep.iterrows():
        filas_html.append(
            f"<tr>"
            f"<td><strong>{esc(r['numero_solicitud'])}</strong></td>"
            f"<td>{esc(r['nombre_estudiante'])}</td>"
            f"<td>{esc(r['codigo_asignatura'])}</td>"
            f"<td>{esc(r['fecha_inicio_ausencia'].strftime('%d/%m/%Y'))}</td>"
            f"<td>{esc(r['fecha_termino_ausencia'].strftime('%d/%m/%Y'))}</td>"
            f"<td>{esc(r['dias_ausencia'])}</td>"
            f"<td>{badge_estado_html(r['nombre_estado'])}</td>"
            f"</tr>"
        )

    st.markdown(
        f"""
        <div class="ucn-table-wrap">
            <table class="ucn-table">
                <thead>
                    <tr>
                        <th>Solicitud</th><th>Estudiante</th><th>Paralelo</th>
                        <th>Desde</th><th>Hasta</th><th>Días</th><th>Estado</th>
                    </tr>
                </thead>
                <tbody>{''.join(filas_html)}</tbody>
            </table>
        </div>
        <div class="ucn-summary-bar">
            <span>{len(df_rep)} detalles</span>
            <span>{df_rep['numero_solicitud'].nunique()} solicitudes</span>
            <span>{df_rep['rut_estudiante'].nunique()} estudiantes</span>
            <span>{int(df_rep['dias_ausencia'].sum())} días por detalle</span>
        </div>
        <div class="ucn-strip-warn">
            Salida depurada para notificación docente: omite diagnósticos médicos y respaldos adjuntos. Comparte el reporte solo con personal autorizado.
        </div>
        """,
        unsafe_allow_html=True,
    )

    df_csv = pd.DataFrame(
        {
            "Solicitud": df_rep["numero_solicitud"],
            "Estudiante": df_rep["nombre_estudiante"],
            "Paralelo": df_rep["codigo_asignatura"],
            "Desde": df_rep["fecha_inicio_ausencia"].apply(lambda d: d.strftime("%d/%m/%Y")),
            "Hasta": df_rep["fecha_termino_ausencia"].apply(lambda d: d.strftime("%d/%m/%Y")),
        }
    )
    csv_bytes = df_csv.to_csv(index=False).encode("utf-8-sig")

    if not st.session_state.reporte_listo:
        b1, _ = st.columns([2.2, 7.8])
        if b1.button("Preparar reporte", type="primary", use_container_width=True):
            st.session_state.rep_filtros = {
                "periodo": periodo_sel,
                "paralelo": paralelo_sel,
                "estado": estado_sel,
            }
            st.session_state.reporte_listo = True
            st.rerun()
    else:
        b1, b2, _ = st.columns([2.4, 2.0, 5.6], gap="small")
        b1.download_button(
            label="Descargar .csv",
            data=csv_bytes,
            file_name=f"inasistencias_{periodo_sel}.csv",
            mime="text/csv",
            type="primary",
            use_container_width=True,
        )
        if b2.button("Cambiar filtros", type="secondary", use_container_width=True):
            st.session_state.reporte_listo = False
            st.rerun()

# ==============================================================================
# ENRUTADOR PRINCIPAL
# ==============================================================================
if st.session_state.usuario is None:
    render_login()
else:
    pagina = st.session_state.pagina
    if pagina == "Inicio":
        render_inicio()
    elif pagina == "Registrar solicitud":
        render_registrar_solicitud()
    elif pagina in ("Consultar solicitudes", "Consultar y revisar"):
        render_consultar_revisar()
    elif pagina == "Cargar planilla":
        render_cargar_planilla()
    elif pagina == "Generar reporte":
        render_generar_reporte()
