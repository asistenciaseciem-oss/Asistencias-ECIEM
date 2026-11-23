import base64
import html
import os
import re
from datetime import date, datetime
import pandas as pd
import streamlit as st
from supabase import create_client, Client

# ==============================================================================
# CONFIGURACIÓN DE PÁGINA (ESTILO OFICIAL ECIEM · UCN)
# ==============================================================================
st.set_page_config(
    page_title="Gestión de Inasistencias · ECIEM UCN",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ==============================================================================
# CARGA DE IMÁGENES DESDE assets/ (LOGO UCN + FONDO CAMPUS)
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
    ["assets/logo_ucn.png", "assets/logo_ucn.jpg", "logo_ucn.png"]
)
FONDO_CAMPUS_B64 = cargar_imagen_base64(
    ["assets/fondo_campus.jpg", "assets/fondo_campus.png", "assets/fondo_campus.jpeg", "fondo_campus.jpg", "fondo_campus.png"]
)

CARRERAS_OFICIALES = [
    "Ingeniería Comercial",
    "Ingeniería en Información y Control de Gestión",
]

# ==============================================================================
# ESTILOS CSS (ESTÉTICA OFICIAL ECIEM UCN: PÍLDORAS, TARJETAS Y TABLA LIMPIA)
# ==============================================================================
CSS_BASE = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

:root {
    color-scheme: light !important;
    --ucn-navy-dark: #002D72;
    --ucn-navy: #003A70;
    --eciem-slate: #4E73A3;
    --eciem-pill-bg: #EEF3F8;
    --ucn-gold: #E6B800;
    --ucn-text: #1E293B;
    --ucn-muted: #64748B;
    --ucn-border: #E2E8F0;
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
    color: #1E293B !important;
}

/* Fondo general limpio estilo portal ECIEM */
.stApp {
    background: #F5F8FC !important;
}

.block-container {
    max-width: 1180px !important;
    padding-top: 0.9rem !important;
    padding-bottom: 3rem !important;
    padding-left: 1.5rem !important;
    padding-right: 1.5rem !important;
}

/* ==========================================================================
   ENCABEZADO SUPERIOR LIMPIO (SIN CAJAS ANIDADAS)
   ========================================================================== */
.ucn-header-bar {
    background: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-radius: 14px;
    padding: 12px 22px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    box-shadow: 0 2px 10px rgba(15, 23, 42, 0.03);
    min-height: 62px;
}
.ucn-brand-group {
    display: flex;
    align-items: center;
    gap: 14px;
}
.ucn-logo-box {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    height: 40px;
}
.ucn-brand-logo {
    max-height: 38px;
    width: auto;
    object-fit: contain;
    display: block;
}
.ucn-brand-divider {
    width: 1px;
    height: 28px;
    background: #E2E8F0;
    flex-shrink: 0;
}
.ucn-unit-title {
    font-size: 13.5px;
    font-weight: 700;
    color: #003A70;
    line-height: 1.2;
}
.ucn-unit-sub {
    font-size: 11.5px;
    font-weight: 500;
    color: #64748B;
    line-height: 1.2;
}
.ucn-role-pill {
    display: inline-flex;
    align-items: center;
    height: 28px;
    font-size: 12.5px;
    font-weight: 600;
    color: #003A70;
    background: #EEF3F8;
    padding: 0 13px;
    border-radius: 999px;
    white-space: nowrap;
}
.ucn-campus-tag {
    font-size: 13.5px;
    font-weight: 600;
    color: #003A70;
}

/* ==========================================================================
   BANNER INSTITUCIONAL ESTILIZADO
   ========================================================================== */
.ucn-banner {
    background: linear-gradient(100deg, #002D72 0%, #004488 65%, #1E5A99 100%);
    border-left: 6px solid #E6B800;
    border-radius: 14px;
    padding: 18px 26px;
    margin-top: 10px;
    margin-bottom: 16px;
    color: #FFFFFF;
    box-shadow: 0 4px 14px rgba(0, 45, 114, 0.08);
    display: flex;
    align-items: center;
    justify-content: space-between;
}
.ucn-banner h1 {
    margin: 0 0 3px 0 !important;
    font-size: 24px !important;
    font-weight: 700 !important;
    color: #FFFFFF !important;
    line-height: 1.2 !important;
}
.ucn-banner p {
    margin: 0 !important;
    font-size: 13.5px !important;
    color: #E2ECF7 !important;
    font-weight: 400 !important;
}
.ucn-banner-tag {
    background: rgba(255, 255, 255, 0.14);
    border: 1px solid rgba(255, 255, 255, 0.22);
    color: #FFFFFF;
    font-size: 12px;
    font-weight: 600;
    padding: 6px 14px;
    border-radius: 999px;
    white-space: nowrap;
}

/* ==========================================================================
   BOTONES TIPO PÍLDORA ECIEM (COMO EN EL PORTAL OFICIAL)
   ========================================================================== */
div.stButton > button,
div.stDownloadButton > button,
div.stFormSubmitButton > button {
    border-radius: 999px !important;
    min-height: 40px !important;
    height: 40px !important;
    font-weight: 600 !important;
    font-size: 13.5px !important;
    padding: 0 20px !important;
    transition: all 0.16s ease !important;
    box-shadow: none !important;
    margin: 0 !important;
}

/* Botón primario (estado activo ECIEM / acción principal) */
div.stButton > button[kind="primary"],
div.stDownloadButton > button[kind="primary"],
div.stFormSubmitButton > button[kind="primary"] {
    background-color: #4E73A3 !important;
    border: 1px solid #4E73A3 !important;
    color: #FFFFFF !important;
}
div.stButton > button[kind="primary"]:hover,
div.stDownloadButton > button[kind="primary"]:hover,
div.stFormSubmitButton > button[kind="primary"]:hover {
    background-color: #003A70 !important;
    border-color: #003A70 !important;
    color: #FFFFFF !important;
}

/* Botón secundario (píldora suave ECIEM #EEF3F8) */
div.stButton > button[kind="secondary"],
div.stDownloadButton > button[kind="secondary"],
div.stFormSubmitButton > button[kind="secondary"] {
    background-color: #EEF3F8 !important;
    border: 1px solid #DCE5F0 !important;
    color: #1E293B !important;
}
div.stButton > button[kind="secondary"]:hover {
    background-color: #E1EAF4 !important;
    border-color: #B8CBE0 !important;
    color: #003A70 !important;
}

/* ==========================================================================
   TARJETAS BLANCAS SÓLIDAS (SIN BORDES DOBLES)
   ========================================================================== */
[data-testid="stVerticalBlockBorderWrapper"] {
    background-color: #FFFFFF !important;
    border: 1px solid #E2E8F0 !important;
    border-radius: 14px !important;
    padding: 1.35rem 1.55rem !important;
    box-shadow: 0 3px 12px rgba(15, 23, 42, 0.04) !important;
}

/* ==========================================================================
   CONTRASTE NÍTIDO EN INPUTS, SELECTS Y DATEPICKERS
   ========================================================================== */
.stTextInput > div > div,
.stDateInput > div > div,
.stSelectbox > div > div,
.stTextArea > div > div,
div[data-baseweb="input"],
div[data-baseweb="input"] > div,
div[data-baseweb="base-input"],
div[data-baseweb="select"],
div[data-baseweb="select"] > div {
    background-color: #FFFFFF !important;
    border-color: #CBD5E1 !important;
}

div[data-baseweb="input"] > div,
div[data-baseweb="select"] > div,
textarea {
    border: 1px solid #CBD5E1 !important;
    border-radius: 10px !important;
    min-height: 41px !important;
}

div[data-baseweb="input"] input,
div[data-baseweb="select"] span,
div[data-baseweb="select"] div[value],
div[data-baseweb="select"] div,
[data-testid="stDateInput"] input,
[data-testid="stTextInput"] input,
textarea {
    color: #1E293B !important;
    -webkit-text-fill-color: #1E293B !important;
    opacity: 1 !important;
    font-size: 13.5px !important;
    font-weight: 500 !important;
}

div[data-baseweb="input"] input::placeholder,
textarea::placeholder {
    color: #64748B !important;
    -webkit-text-fill-color: #64748B !important;
    opacity: 1 !important;
    font-weight: 400 !important;
}

div[data-baseweb="select"] svg,
div[data-baseweb="input"] svg {
    fill: #475569 !important;
    color: #475569 !important;
}

div[data-baseweb="popover"],
div[data-baseweb="popover"] > div,
ul[role="listbox"],
ul[role="listbox"] li {
    background-color: #FFFFFF !important;
    color: #1E293B !important;
}
ul[role="listbox"] li:hover,
ul[role="listbox"] li[aria-selected="true"] {
    background-color: #EEF3F8 !important;
    color: #003A70 !important;
    font-weight: 600 !important;
}

div[data-baseweb="input"] > div:focus-within,
div[data-baseweb="select"] > div:focus-within,
textarea:focus {
    border-color: #4E73A3 !important;
    box-shadow: 0 0 0 1.5px #4E73A3 !important;
}

.stTextInput label, .stSelectbox label, .stDateInput label,
.stTextArea label, .stFileUploader label,
.stTextInput label p, .stSelectbox label p, .stDateInput label p,
.stTextArea label p, .stFileUploader label p {
    color: #334155 !important;
    font-weight: 600 !important;
    font-size: 13px !important;
    margin-bottom: 4px !important;
}

[data-testid="stFileUploader"] section,
[data-testid="stFileUploaderDropzone"] {
    background-color: #F8FAFC !important;
    border: 1.5px dashed #CBD5E1 !important;
    border-radius: 12px !important;
    color: #1E293B !important;
}
[data-testid="stFileUploaderDropzone"] small,
[data-testid="stFileUploaderDropzone"] span,
[data-testid="stFileUploaderDropzone"] div {
    color: #475569 !important;
}
[data-testid="stFileUploaderDropzone"] button {
    background-color: #FFFFFF !important;
    color: #003A70 !important;
    border: 1px solid #CBD5E1 !important;
    border-radius: 999px !important;
}

/* ==========================================================================
   TARJETAS KPI (ESTILO MODERNO ECIEM)
   ========================================================================== */
.ucn-kpi-card {
    background: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-top: 4px solid #4E73A3;
    border-radius: 14px;
    padding: 18px 22px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    box-shadow: 0 2px 10px rgba(15, 23, 42, 0.03);
    margin-bottom: 14px;
}
.ucn-kpi-card.gold-accent {
    border-top-color: #E6B800;
}
.ucn-kpi-info-title {
    font-size: 13.5px;
    font-weight: 600;
    color: #475569;
    margin-bottom: 2px;
}
.ucn-kpi-info-sub {
    font-size: 12px;
    color: #64748B;
}
.ucn-kpi-number {
    font-size: 34px;
    font-weight: 800;
    color: #003A70;
    line-height: 1;
    background: #EEF3F8;
    padding: 10px 18px;
    border-radius: 12px;
}
.ucn-kpi-card.gold-accent .ucn-kpi-number {
    background: #FBF4E3;
    color: #825F1A;
}

/* ==========================================================================
   TABLAS MODERNAS SIN BORDES VERTICALES (ESTILO ECIEM)
   ========================================================================== */
.ucn-section-title {
    font-size: 16.5px;
    font-weight: 700;
    color: #1E293B;
    margin: 18px 0 10px 0;
    display: flex;
    align-items: center;
    gap: 8px;
}
.ucn-table-wrap {
    background: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-radius: 14px;
    overflow-x: auto;
    margin-bottom: 14px;
    box-shadow: 0 2px 10px rgba(15, 23, 42, 0.03);
}
table.ucn-table {
    width: 100%;
    border-collapse: collapse;
    font-size: 13.5px;
    color: #334155;
    border: none;
}
table.ucn-table thead tr {
    background-color: #F8FAFC;
    border-bottom: 1px solid #E2E8F0;
}
table.ucn-table th {
    text-align: left;
    padding: 13px 18px;
    font-size: 12px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.4px;
    color: #64748B;
    white-space: nowrap;
    border: none !important;
}
table.ucn-table td {
    padding: 14px 18px;
    border-bottom: 1px solid #F1F5F9;
    border-left: none !important;
    border-right: none !important;
    vertical-align: middle;
}
table.ucn-table tbody tr:last-child td {
    border-bottom: none;
}
table.ucn-table tbody tr {
    transition: background-color 0.14s ease;
}
table.ucn-table tbody tr:hover {
    background-color: #F8FAFC;
}
table.ucn-table tbody tr.ucn-row-selected {
    background-color: #EEF3F8 !important;
}
.ucn-sol-id {
    font-weight: 700;
    color: #4E73A3;
    font-size: 14px;
}
.ucn-file-link {
    color: #B4691E;
    font-weight: 500;
    font-size: 13px;
}

/* Badges de estado suaves */
.ucn-badge {
    display: inline-block;
    padding: 5px 14px;
    border-radius: 999px;
    font-size: 12px;
    font-weight: 600;
    text-align: center;
    min-width: 94px;
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

/* Encabezado de pasos numerados en formularios (1, 2, 3) */
.ucn-step-header {
    display: flex;
    align-items: center;
    gap: 10px;
    margin: 0 0 14px 0;
    padding-bottom: 10px;
    border-bottom: 1px solid #F1F5F9;
}
.ucn-step-num {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 24px;
    height: 24px;
    border-radius: 999px;
    background: #4E73A3;
    color: #FFFFFF;
    font-size: 12px;
    font-weight: 700;
    flex-shrink: 0;
}
.ucn-step-title {
    font-size: 15px;
    font-weight: 700;
    color: #1E293B;
}
.ucn-step-sub {
    font-size: 12.5px;
    color: #64748B;
    margin-left: auto;
}

/* Franjas de feedback */
.ucn-strip-ok {
    background: #EAF5EE;
    border: 1px solid #CBE6D5;
    color: #256747;
    border-radius: 10px;
    padding: 11px 16px;
    font-size: 13.5px;
    font-weight: 600;
    margin: 8px 0 12px 0;
}
.ucn-strip-err {
    background: #FCEEEE;
    border: 1px solid #F3CACA;
    color: #A73535;
    border-radius: 10px;
    padding: 11px 16px;
    font-size: 13px;
    font-weight: 600;
    margin: 8px 0 12px 0;
}
.ucn-strip-warn {
    background: #FBF4E3;
    border: 1px solid #EFE0B8;
    color: #825F1A;
    border-radius: 10px;
    padding: 11px 16px;
    font-size: 13px;
    font-weight: 500;
    margin: 8px 0 12px 0;
}
.ucn-strip-info {
    background: #EEF3F8;
    border: 1px solid #DCE5F0;
    color: #334155;
    border-radius: 10px;
    padding: 11px 16px;
    font-size: 13px;
    font-weight: 500;
    margin: 8px 0 12px 0;
}

/* Cajas suaves de detalle */
.ucn-soft-box {
    background: #F8FAFC;
    border: 1px solid #E2E8F0;
    border-radius: 12px;
    padding: 13px 16px;
    margin: 0;
}
.ucn-soft-box-title {
    font-size: 15px;
    font-weight: 700;
    color: #4E73A3;
    margin-bottom: 3px;
}
.ucn-soft-box-sub {
    font-size: 13px;
    color: #475569;
    line-height: 1.45;
}
.ucn-summary-bar {
    display: flex;
    flex-wrap: wrap;
    gap: 22px;
    background: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-radius: 12px;
    padding: 12px 18px;
    font-size: 13px;
    font-weight: 600;
    color: #003A70;
    margin-bottom: 12px;
}
</style>
"""
st.markdown(CSS_BASE, unsafe_allow_html=True)

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
    asignaturas = (
        supabase.table("dim_asignatura")
        .select("*")
        .order("carrera")
        .order("semestre")
        .order("id_paralelo")
        .execute()
        .data
    )
    estudiantes = supabase.table("dim_estudiante").select("*").execute().data
    return estados, periodos, asignaturas, estudiantes

def cargar_hechos_detallados() -> pd.DataFrame:
    res = (
        supabase.table("hechos_justificacion")
        .select(
            "id_hecho, numero_solicitud, id_fecha_ingreso, id_fecha_resolucion, "
            "fecha_inicio_ausencia, fecha_termino_ausencia, rut_estudiante, "
            "id_paralelo, paralelo, id_estado, id_funcionario, id_periodo, "
            "dias_tramitacion, cantidad_documentos_adjuntos, tipo_documento, "
            "nombre_archivo, observacion_revision, "
            "dim_estudiante(rut, nombre_estudiante, nombre_carrera, anio_ingreso, estado_matricula), "
            "dim_asignatura(id_paralelo, carrera, semestre, codigo_asignatura, nombre_asignatura, nombre_docente), "
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
        par_txt = (r.get("paralelo") or "A").strip()
        nom_asig = asig.get("nombre_asignatura", "")
        asig_con_par = f"{nom_asig} (Par. {par_txt})" if nom_asig else par_txt

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
                "carrera_asignatura": asig.get("carrera", ""),
                "semestre": asig.get("semestre", 1),
                "codigo_asignatura": asig.get("codigo_asignatura", ""),
                "nombre_asignatura": nom_asig,
                "paralelo": par_txt,
                "asignatura_paralelo": asig_con_par,
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
# COMPONENTES DE LAYOUT REUTILIZABLES (ENCABEZADO LIMPIO + PÍLDORAS ECIEM)
# ==============================================================================
def brand_logos_html() -> str:
    logo_img = (
        f'<div class="ucn-logo-box"><img src="{LOGO_UCN_B64}" class="ucn-brand-logo" alt="Universidad Católica del Norte" /></div>'
        if LOGO_UCN_B64
        else '<div class="ucn-unit-title">Universidad Católica del Norte</div>'
    )
    return (
        f"{logo_img}"
        '<div class="ucn-brand-divider"></div>'
        '<div>'
        '<div class="ucn-unit-title">Escuela de Ciencias Empresariales</div>'
        '<div class="ucn-unit-sub">Campus Guayacán · Coquimbo</div>'
        '</div>'
    )

def render_topbar(boton_izq_texto="Inicio"):
    user = st.session_state.usuario
    rol_corto = "Secretaría" if user["rol"] == "Secretaría" else "Jefatura de Carrera"

    col_brand, col_nav1, col_nav2 = st.columns([7.2, 1.3, 1.5], vertical_alignment="center")
    with col_brand:
        st.markdown(
            f"""
            <div class="ucn-header-bar">
                <div class="ucn-brand-group">
                    {brand_logos_html()}
                </div>
                <span class="ucn-role-pill">{esc(rol_corto)}</span>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with col_nav1:
        if st.button(boton_izq_texto, key=f"nav_top_{boton_izq_texto}", type="secondary", use_container_width=True):
            st.session_state.ultima_solicitud_guardada = None
            st.session_state.ultima_carga_confirmada = None
            st.session_state.reporte_listo = False
            st.session_state.pagina = "Inicio"
            st.rerun()
    with col_nav2:
        if st.button("Cerrar sesión", key="nav_top_logout", type="secondary", use_container_width=True):
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
            <div>
                <h1>{esc(titulo)}</h1>
                <p>{esc(subtitulo)}</p>
            </div>
            <span class="ucn-banner-tag">Gestión de Inasistencias</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

def render_eciem_nav_pills(total_sol: int = 0, en_proc: int = 0):
    """Barra de navegación tipo píldora inspirada en el portal oficial ECIEM."""
    es_secretaria = st.session_state.usuario["rol"] == "Secretaría"
    pag = st.session_state.pagina

    if es_secretaria:
        c1, c2, c3, c4, c5 = st.columns([1.15, 1.75, 2.05, 1.65, 1.70], gap="small")
        if c1.button("🏠 Inicio", type="primary" if pag == "Inicio" else "secondary", use_container_width=True, key="pill_ini"):
            st.session_state.pagina = "Inicio"
            st.rerun()
        if c2.button("📝 Registrar solicitud", type="primary" if pag == "Registrar solicitud" else "secondary", use_container_width=True, key="pill_reg"):
            st.session_state.ultima_solicitud_guardada = None
            st.session_state.pagina = "Registrar solicitud"
            st.rerun()
        if c3.button(f"🔍 Consultar ({total_sol})", type="primary" if pag == "Consultar solicitudes" else "secondary", use_container_width=True, key="pill_con"):
            st.session_state.pagina = "Consultar solicitudes"
            st.rerun()
        if c4.button("📤 Cargar planilla", type="primary" if pag == "Cargar planilla" else "secondary", use_container_width=True, key="pill_car"):
            st.session_state.ultima_carga_confirmada = None
            st.session_state.pagina = "Cargar planilla"
            st.rerun()
        if c5.button("📊 Generar reporte", type="primary" if pag == "Generar reporte" else "secondary", use_container_width=True, key="pill_rep"):
            st.session_state.reporte_listo = False
            st.session_state.pagina = "Generar reporte"
            st.rerun()
    else:
        c1, c2, c3, _ = st.columns([1.2, 2.2, 1.8, 4.8], gap="small")
        if c1.button("🏠 Inicio", type="primary" if pag == "Inicio" else "secondary", use_container_width=True, key="pill_j_ini"):
            st.session_state.pagina = "Inicio"
            st.rerun()
        if c2.button(f"⚖️ Consultar y revisar ({en_proc})", type="primary" if pag == "Consultar y revisar" else "secondary", use_container_width=True, key="pill_j_rev"):
            st.session_state.pagina = "Consultar y revisar"
            st.rerun()
        if c3.button("📊 Generar reporte", type="primary" if pag == "Generar reporte" else "secondary", use_container_width=True, key="pill_j_rep"):
            st.session_state.reporte_listo = False
            st.session_state.pagina = "Generar reporte"
            st.rerun()

    st.markdown("<div style='height:8px;'></div>", unsafe_allow_html=True)

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
    "rep_filtros": {"periodo": "2026-2", "carrera": "Todas", "estado": "Aceptado"},
    "filtro_consulta_rut": "",
    "filtro_consulta_estado": "Todos",
    "ultimo_rut_autodetectado": "",
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ==============================================================================
# PANTALLA 01: INICIAR SESIÓN
# ==============================================================================
def render_login():
    fondo_css = (
        f"linear-gradient(90deg, rgba(0, 45, 114, 0.88) 0%, rgba(0, 58, 112, 0.76) 52%, rgba(0, 58, 112, 0.62) 100%), url('{FONDO_CAMPUS_B64}')"
        if FONDO_CAMPUS_B64
        else "linear-gradient(135deg, #002D72 0%, #003A70 55%, #004D99 100%)"
    )

    st.markdown(
        f"""
        <style>
        .stApp {{
            background: {fondo_css} !important;
            background-size: cover !important;
            background-position: center center !important;
            background-attachment: fixed !important;
        }}
        .block-container {{
            max-width: 100% !important;
            padding-top: 0 !important;
            padding-bottom: 1.5rem !important;
            padding-left: 0 !important;
            padding-right: 0 !important;
        }}
        .ucn-login-fullbar {{
            background: #FFFFFF;
            border-bottom: 1px solid #E2E8F0;
            padding: 12px 48px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            width: 100%;
            box-shadow: 0 2px 8px rgba(0, 25, 65, 0.08);
            margin-bottom: 36px;
        }}
        .ucn-login-left-col {{
            min-height: 450px;
            border-right: 4px solid #E6B800;
            padding-right: 36px;
            padding-left: 16px;
            display: flex;
            flex-direction: column;
            justify-content: center;
        }}
        .ucn-hero-kicker {{
            color: #E6B800;
            font-size: 13px;
            font-weight: 700;
            letter-spacing: 1.4px;
            text-transform: uppercase;
            margin-bottom: 12px;
        }}
        .ucn-hero-h1 {{
            color: #FFFFFF;
            font-size: 40px;
            font-weight: 800;
            line-height: 1.12;
            margin: 0 0 16px 0;
        }}
        .ucn-hero-p {{
            color: #FFFFFF;
            font-size: 17px;
            font-weight: 500;
            line-height: 1.45;
            margin: 0 0 32px 0;
            max-width: 380px;
        }}
        .ucn-hero-caption {{
            color: #D2E1F0;
            font-size: 12px;
        }}
        </style>

        <div class="ucn-login-fullbar">
            <div class="ucn-brand-group">
                {brand_logos_html()}
            </div>
            <div class="ucn-campus-tag">Gestión de Inasistencias · Campus Guayacán</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    _, col_left, col_right, _ = st.columns([0.5, 3.8, 5.2, 0.5], gap="large", vertical_alignment="center")

    with col_left:
        st.markdown(
            """
            <div class="ucn-login-left-col">
                <div class="ucn-hero-kicker">GESTIÓN ACADÉMICA</div>
                <div class="ucn-hero-h1">Gestión de<br>inasistencias</div>
                <div class="ucn-hero-p">Recepción, revisión y seguimiento de solicitudes.</div>
                <div class="ucn-hero-caption">Escuela de Ciencias Empresariales · Coquimbo</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col_right:
        with st.container(border=True):
            st.markdown(
                """
                <div style="font-size:26px;font-weight:700;color:#1E293B;margin-bottom:4px;">Iniciar sesión</div>
                <div style="font-size:14px;color:#64748B;margin-bottom:18px;">Selecciona tu perfil para continuar.</div>
                """,
                unsafe_allow_html=True,
            )

            p1, p2 = st.columns(2, gap="medium")
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
                    "Correo institucional",
                    placeholder=placeholder_correo,
                )
                contrasena = st.text_input(
                    "Contraseña",
                    type="password",
                    placeholder="Ingresa tu contraseña",
                )
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
# PANTALLA 02: INICIO (DASHBOARD SECRETARÍA / JEFATURA)
# ==============================================================================
def render_inicio():
    user = st.session_state.usuario
    es_secretaria = user["rol"] == "Secretaría"

    df = cargar_hechos_detallados()
    _, periodos, _, _ = cargar_catalogos()
    periodo_actual = periodos[0]["nombre_periodo"] if periodos else "2026-2"

    total_solicitudes = df["numero_solicitud"].nunique() if not df.empty else 0
    en_proceso = (
        df[df["nombre_estado"] == "En proceso"]["numero_solicitud"].nunique()
        if not df.empty
        else 0
    )

    render_topbar("Inicio")
    render_banner(
        "Inicio",
        "Recibe solicitudes y organiza los antecedentes."
        if es_secretaria
        else "Consulta antecedentes y registra una decisión.",
    )
    render_eciem_nav_pills(total_solicitudes, en_proceso)

    k1, k2 = st.columns(2, gap="medium")
    with k1:
        st.markdown(
            f"""
            <div class="ucn-kpi-card">
                <div>
                    <div class="ucn-kpi-info-title">Solicitudes del período</div>
                    <div class="ucn-kpi-info-sub">Período académico {esc(periodo_actual)}</div>
                </div>
                <div class="ucn-kpi-number">{total_solicitudes}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with k2:
        st.markdown(
            f"""
            <div class="ucn-kpi-card gold-accent">
                <div>
                    <div class="ucn-kpi-info-title">Solicitudes en proceso</div>
                    <div class="ucn-kpi-info-sub">Pendientes de revisión o antecedentes</div>
                </div>
                <div class="ucn-kpi-number">{en_proceso}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown('<div class="ucn-section-title">Solicitudes recientes</div>', unsafe_allow_html=True)

    if df.empty:
        st.markdown('<div class="ucn-strip-info">Aún no existen solicitudes registradas en el sistema.</div>', unsafe_allow_html=True)
        return

    resumen = (
        df.groupby("numero_solicitud", as_index=False)
        .agg(
            Estudiante=("nombre_estudiante", "first"),
            Carrera=("nombre_carrera", "first"),
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
            f"<td><span class='ucn-sol-id'>#{esc(r['numero_solicitud'])}</span></td>"
            f"<td><strong>{esc(r['Estudiante'])}</strong></td>"
            f"<td>{esc(r['Carrera'])}</td>"
            f"<td>📅 {esc(fecha_txt)}</td>"
            f"<td>{badge_estado_html(r['Estado'])}</td>"
            f"<td><span class='ucn-file-link'>📄 {esc(respaldo_txt)}</span></td>"
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
                        <th>Carrera</th>
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
# PANTALLA 03: REGISTRAR SOLICITUD (3 PASOS LIMPIOS)
# ==============================================================================
def render_registrar_solicitud():
    if st.session_state.usuario["rol"] != "Secretaría":
        st.session_state.pagina = "Inicio"
        st.rerun()

    df_all = cargar_hechos_detallados()
    total_sol = df_all["numero_solicitud"].nunique() if not df_all.empty else 0
    en_proc = df_all[df_all["nombre_estado"] == "En proceso"]["numero_solicitud"].nunique() if not df_all.empty else 0

    render_topbar("Inicio")

    if st.session_state.ultima_solicitud_guardada is not None:
        info = st.session_state.ultima_solicitud_guardada
        render_banner("Solicitud registrada", "Los antecedentes quedan disponibles para Jefatura.")
        render_eciem_nav_pills(total_sol, en_proc)
        st.markdown(
            f'<div class="ucn-strip-ok">Solicitud #{esc(info["numero_solicitud"])} registrada correctamente.</div>',
            unsafe_allow_html=True,
        )

        filas_det = "".join(
            f"<tr><td>{esc(d['carrera'])}</td>"
            f"<td>{esc(d['nombre_asignatura'])}</td>"
            f"<td><strong>{esc(d['paralelo'])}</strong></td>"
            f"<td>{esc(d['fecha_inicio'].strftime('%d/%m/%Y'))}</td>"
            f"<td>{esc(d['fecha_termino'].strftime('%d/%m/%Y'))}</td></tr>"
            for d in info["detalles"]
        )

        with st.container(border=True):
            st.markdown(
                f"""
                <div style="margin-bottom:10px;">{badge_estado_html('En proceso')}</div>
                <div style="font-size:19px;font-weight:700;color:#1E293B;margin-bottom:4px;">{esc(info['nombre_estudiante'])}</div>
                <div style="font-size:13.5px;color:#64748B;margin-bottom:14px;">
                    Entrega y recepción: {esc(info['fecha_entrega'].strftime('%d/%m/%Y'))} ·
                    {esc(info['nombre_archivo'])} · {len(info['detalles'])} detalle(s)
                </div>
                <div class="ucn-table-wrap" style="margin-bottom:0;">
                    <table class="ucn-table">
                        <thead><tr><th>Carrera</th><th>Asignatura</th><th>Paralelo</th><th>Desde</th><th>Hasta</th></tr></thead>
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
        "Completa los 3 pasos para ingresar la justificación al sistema.",
    )
    render_eciem_nav_pills(total_sol, en_proc)

    estados, periodos, asignaturas, estudiantes = cargar_catalogos()
    mapa_estudiantes = {normalizar_rut(e["rut"]): e for e in estudiantes}
    estado_en_proceso = next((e["id_estado"] for e in estados if e["nombre_estado"] == "En proceso"), None)

    if not periodos or not asignaturas or estado_en_proceso is None:
        st.markdown(
            '<div class="ucn-strip-err">Faltan datos maestros en la base de datos.</div>',
            unsafe_allow_html=True,
        )
        return

    # PASO 1: IDENTIFICACIÓN DEL ESTUDIANTE
    with st.container(border=True):
        st.markdown(
            """
            <div class="ucn-step-header">
                <span class="ucn-step-num">1</span>
                <span class="ucn-step-title">Identificación del estudiante</span>
                <span class="ucn-step-sub">Valida el RUT registrado</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

        c_rut, c_ficha = st.columns([1.1, 1.9], gap="large", vertical_alignment="center")
        estudiante_actual = None

        with c_rut:
            rut_input = st.text_input("RUT del estudiante", placeholder="Ej.: 12.345.678-5")
            if rut_input.strip():
                if not validar_rut_chileno(rut_input):
                    st.markdown('<div class="ucn-strip-err">RUT inválido. Revisa el dígito verificador.</div>', unsafe_allow_html=True)
                else:
                    rut_norm_act = normalizar_rut(rut_input)
                    estudiante_actual = mapa_estudiantes.get(rut_norm_act)
                    if not estudiante_actual:
                        st.markdown('<div class="ucn-strip-err">Estudiante no registrado.</div>', unsafe_allow_html=True)
                    else:
                        if st.session_state.ultimo_rut_autodetectado != rut_norm_act:
                            if estudiante_actual["nombre_carrera"] in CARRERAS_OFICIALES:
                                st.session_state["reg_carrera_sel"] = estudiante_actual["nombre_carrera"]
                            st.session_state.ultimo_rut_autodetectado = rut_norm_act

        with c_ficha:
            if estudiante_actual:
                st.markdown(
                    f"""
                    <div class="ucn-soft-box">
                        <div class="ucn-soft-box-title">{esc(estudiante_actual['nombre_estudiante'])}</div>
                        <div class="ucn-soft-box-sub">
                            RUT {esc(estudiante_actual['rut'])} · <strong>{esc(estudiante_actual['nombre_carrera'])}</strong> ·
                            Ingreso {esc(estudiante_actual['anio_ingreso'])} ({esc(estudiante_actual['estado_matricula'])})
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
            else:
                st.markdown(
                    """
                    <div class="ucn-soft-box">
                        <div class="ucn-soft-box-title">Estudiante por seleccionar</div>
                        <div class="ucn-soft-box-sub">Ingresa un RUT válido para cargar su nombre, carrera y estado académico.</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

    st.markdown("<div style='height:10px;'></div>", unsafe_allow_html=True)

    # PASO 2: ASIGNATURAS Y FECHAS DE INASISTENCIA
    with st.container(border=True):
        st.markdown(
            """
            <div class="ucn-step-header">
                <span class="ucn-step-num">2</span>
                <span class="ucn-step-title">Asignaturas y fechas de inasistencia</span>
                <span class="ucn-step-sub">Filtra por carrera · Paralelo libre</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

        s1, s2, s3 = st.columns([1.25, 1.50, 0.65], gap="medium")
        with s1:
            carrera_sel = st.selectbox("Carrera", CARRERAS_OFICIALES, key="reg_carrera_sel")

        asig_filtradas = [a for a in asignaturas if a.get("carrera") == carrera_sel] or asignaturas
        mapa_asig = {
            f"Sem. {a.get('semestre', 1)} · {a['nombre_asignatura']}": a
            for a in asig_filtradas
        }
        with s2:
            asig_label = st.selectbox("Asignatura (1° a 3° año)", list(mapa_asig.keys()))

        with s3:
            paralelo_input = st.text_input("Paralelo", placeholder="Ej.: A, B, 1")

        d1, d2, d3 = st.columns([1.0, 1.0, 1.0], gap="medium", vertical_alignment="bottom")
        with d1:
            f_inicio = st.date_input("Fecha de inicio", value=date.today(), format="DD/MM/YYYY")
        with d2:
            f_termino = st.date_input("Fecha de término", value=date.today(), format="DD/MM/YYYY")
        with d3:
            agregar_clic = st.button("+ Agregar otra asignatura", type="secondary", use_container_width=True)

        if f_termino < f_inicio:
            st.markdown(
                '<div class="ucn-strip-err">La fecha de término no puede ser anterior a la fecha de inicio.</div>',
                unsafe_allow_html=True,
            )

        if agregar_clic:
            par_limpio = paralelo_input.strip().upper()
            if f_termino < f_inicio:
                st.markdown(
                    '<div class="ucn-strip-err">Corrige las fechas antes de agregar el detalle.</div>',
                    unsafe_allow_html=True,
                )
            elif not par_limpio:
                st.markdown(
                    '<div class="ucn-strip-err">Escribe el paralelo antes de agregar (Ej.: A, B, 1).</div>',
                    unsafe_allow_html=True,
                )
            else:
                asig_obj = mapa_asig[asig_label]
                if any(
                    d["id_paralelo"] == asig_obj["id_paralelo"] and d["paralelo"] == par_limpio
                    for d in st.session_state.detalles_pendientes
                ):
                    st.markdown('<div class="ucn-strip-warn">Esa asignatura y paralelo ya están en la lista.</div>', unsafe_allow_html=True)
                else:
                    st.session_state.detalles_pendientes.append(
                        {
                            "id_paralelo": asig_obj["id_paralelo"],
                            "carrera": carrera_sel,
                            "codigo_asignatura": asig_obj["codigo_asignatura"],
                            "nombre_asignatura": asig_obj["nombre_asignatura"],
                            "paralelo": par_limpio,
                            "fecha_inicio": f_inicio,
                            "fecha_termino": f_termino,
                        }
                    )
                    st.rerun()

        if st.session_state.detalles_pendientes:
            filas_p = "".join(
                f"<tr><td><strong>{i+1}</strong></td>"
                f"<td>{esc(d['carrera'])}</td>"
                f"<td>{esc(d['nombre_asignatura'])}</td>"
                f"<td><strong>{esc(d['paralelo'])}</strong></td>"
                f"<td>{esc(d['fecha_inicio'].strftime('%d/%m/%Y'))}</td>"
                f"<td>{esc(d['fecha_termino'].strftime('%d/%m/%Y'))}</td></tr>"
                for i, d in enumerate(st.session_state.detalles_pendientes)
            )
            st.markdown(
                f"""
                <div class="ucn-table-wrap" style="margin-top:12px;">
                    <table class="ucn-table">
                        <thead><tr><th>#</th><th>Carrera</th><th>Asignatura</th><th>Paralelo</th><th>Desde</th><th>Hasta</th></tr></thead>
                        <tbody>{filas_p}</tbody>
                    </table>
                </div>
                """,
                unsafe_allow_html=True,
            )
            if st.button("Limpiar lista de asignaturas", type="secondary"):
                st.session_state.detalles_pendientes = []
                st.rerun()

    st.markdown("<div style='height:10px;'></div>", unsafe_allow_html=True)

    # PASO 3: RECEPCIÓN Y RESPALDO DOCUMENTAL
    with st.container(border=True):
        st.markdown(
            """
            <div class="ucn-step-header">
                <span class="ucn-step-num">3</span>
                <span class="ucn-step-title">Recepción y respaldo documental</span>
                <span class="ucn-step-sub">Antecedentes adjuntos</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

        m1, m2, m3, m4 = st.columns([1.0, 1.0, 1.2, 0.9], gap="medium")
        with m1:
            fecha_entrega = st.date_input("Fecha de entrega", value=date.today(), format="DD/MM/YYYY")
        with m2:
            fecha_recepcion = st.date_input("Fecha de recepción", value=date.today(), format="DD/MM/YYYY")
        with m3:
            tipo_doc = st.text_input("Tipo de documento", placeholder="Ej.: Certificado médico")
        with m4:
            periodo_opciones = {p["nombre_periodo"]: p["id_periodo"] for p in periodos}
            periodo_sel = st.selectbox("Período", list(periodo_opciones.keys()))

        archivo_respaldo = st.file_uploader(
            "Respaldo recibido (PDF o imagen)",
            type=["pdf", "png", "jpg", "jpeg"],
        )
        if archivo_respaldo is not None:
            st.markdown(
                f'<div class="ucn-strip-ok">✓ Respaldo adjuntado ({esc(archivo_respaldo.name)}).</div>',
                unsafe_allow_html=True,
            )

    st.markdown("<div style='height:12px;'></div>", unsafe_allow_html=True)
    bt1, bt2, _ = st.columns([2.2, 1.6, 6.2], gap="small")
    guardar_clic = bt1.button("Guardar solicitud", type="primary", use_container_width=True)
    cancelar_clic = bt2.button("Cancelar", type="secondary", use_container_width=True)

    if cancelar_clic:
        st.session_state.detalles_pendientes = []
        st.session_state.pagina = "Inicio"
        st.rerun()

    if guardar_clic:
        detalles_a_guardar = list(st.session_state.detalles_pendientes)
        par_limpio = paralelo_input.strip().upper()
        if not detalles_a_guardar and f_termino >= f_inicio and par_limpio:
            asig_obj = mapa_asig[asig_label]
            detalles_a_guardar.append(
                {
                    "id_paralelo": asig_obj["id_paralelo"],
                    "carrera": carrera_sel,
                    "codigo_asignatura": asig_obj["codigo_asignatura"],
                    "nombre_asignatura": asig_obj["nombre_asignatura"],
                    "paralelo": par_limpio,
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
            errores.append("Completa la asignatura e ingresa el paralelo (Ej.: A, B, 1).")
        if not tipo_doc.strip() or archivo_respaldo is None:
            errores.append("Completa el tipo de documento y adjunta un respaldo.")

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
                    "paralelo": det["paralelo"],
                    "id_estado": estado_en_proceso,
                    "id_funcionario": id_funcionario,
                    "id_periodo": id_periodo,
                    "dias_tramitacion": None,
                    "cantidad_documentos_adjuntos": 1,
                    "tipo_documento": tipo_doc.strip(),
                    "nombre_archivo": archivo_respaldo.name,
                    "observacion_revision": f"Solicitud recibida ({fecha_recepcion.strftime('%d/%m/%Y')}).",
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
# PANTALLA 04: CONSULTAR SOLICITUDES / CONSULTAR Y REVISAR
# ==============================================================================
def render_consultar_revisar():
    es_jefatura = st.session_state.usuario["rol"] != "Secretaría"

    df = cargar_hechos_detallados()
    total_sol = df["numero_solicitud"].nunique() if not df.empty else 0
    en_proc = df[df["nombre_estado"] == "En proceso"]["numero_solicitud"].nunique() if not df.empty else 0

    render_topbar("Inicio")
    render_banner(
        "Consultar y revisar" if es_jefatura else "Consultar solicitudes",
        "Revisa los antecedentes y registra una resolución."
        if es_jefatura
        else "Filtra por estudiante o estado de la solicitud.",
    )
    render_eciem_nav_pills(total_sol, en_proc)

    estados, _, _, _ = cargar_catalogos()
    mapa_estados = {e["nombre_estado"]: e["id_estado"] for e in estados}
    lista_estados = ["Todos"] + list(mapa_estados.keys())

    if not es_jefatura:
        f1, f2, f3 = st.columns([2.4, 2.0, 1.1], vertical_alignment="bottom")
        with f1:
            rut_q = st.text_input(
                "RUT o nombre del estudiante",
                value=st.session_state.filtro_consulta_rut,
                placeholder="Ej.: 12.345.678-5",
            )
        with f2:
            idx_e = lista_estados.index(st.session_state.filtro_consulta_estado) if st.session_state.filtro_consulta_estado in lista_estados else 0
            est_q = st.selectbox("Estado actual", lista_estados, index=idx_e)
        with f3:
            if st.button("Buscar", type="primary", use_container_width=True):
                st.session_state.filtro_consulta_rut = rut_q
                st.session_state.filtro_consulta_estado = est_q
                st.rerun()

        st.markdown("<div style='height:10px;'></div>", unsafe_allow_html=True)

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
                    <div style="font-size:17px;font-weight:700;color:#1E293B;margin-bottom:4px;">Sin resultados</div>
                    <div style="font-size:13.5px;color:#64748B;margin-bottom:12px;">
                        No se encontraron solicitudes con los filtros aplicados.
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
                f"<td><span class='ucn-sol-id'>#{esc(r['numero_solicitud'])}</span></td>"
                f"<td><strong>{esc(r['nombre_estudiante'])}</strong></td>"
                f"<td>📅 {esc(f_ent)}</td>"
                f"<td>{esc(r['nombre_asignatura'])}</td>"
                f"<td><strong>{esc(r['paralelo'])}</strong></td>"
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
                            <th>Asignatura</th>
                            <th>Paralelo</th>
                            <th>Inasistencia</th>
                            <th>Estado actual</th>
                        </tr>
                    </thead>
                    <tbody>{''.join(filas_html)}</tbody>
                </table>
            </div>
            """,
            unsafe_allow_html=True,
        )
        return

    # ---- VERSIÓN JEFATURA ----
    col_izq, col_der = st.columns([5.3, 4.7], gap="large")

    with col_izq:
        f1, f2 = st.columns(2, gap="small")
        with f1:
            rut_q = st.text_input(
                "RUT o estudiante",
                value=st.session_state.filtro_consulta_rut,
                placeholder="Ej.: 12.345.678-5",
            )
        with f2:
            idx_e = lista_estados.index(st.session_state.filtro_consulta_estado) if st.session_state.filtro_consulta_estado in lista_estados else 0
            est_q = st.selectbox("Estado actual", lista_estados, index=idx_e)

        if st.button("Buscar", type="primary", use_container_width=True):
            st.session_state.filtro_consulta_rut = rut_q
            st.session_state.filtro_consulta_estado = est_q
            st.rerun()

        st.markdown("<div style='height:8px;'></div>", unsafe_allow_html=True)

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
                    '<div style="font-size:16px;font-weight:700;color:#1E293B;">Sin resultados</div>'
                    '<div style="font-size:13px;color:#64748B;margin:4px 0 10px 0;">No se encontraron coincidencias.</div>',
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
            "Solicitud a revisar",
            opciones_sol,
            format_func=lambda s: f"Solicitud #{s} — {resumen_sol[resumen_sol['numero_solicitud'] == s]['Estudiante'].iloc[0]}",
        )

        filas_html = []
        for _, r in resumen_sol.iterrows():
            f_ent = r["Entrega"].strftime("%d/%m/%Y") if r["Entrega"] else ""
            row_cls = ' class="ucn-row-selected"' if r["numero_solicitud"] == sol_sel else ""
            filas_html.append(
                f"<tr{row_cls}>"
                f"<td><span class='ucn-sol-id'>#{esc(r['numero_solicitud'])}</span></td>"
                f"<td><strong>{esc(r['Estudiante'])}</strong></td>"
                f"<td>📅 {esc(f_ent)}</td>"
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
            f"<strong>{esc(r['nombre_asignatura'])} (Par. {esc(r['paralelo'])})</strong> · "
            f"{esc(formatear_rango_inasistencia(r['fecha_inicio_ausencia'], r['fecha_termino_ausencia']))}"
            for _, r in filas_sol.iterrows()
        )
        f_ing_txt = primera["fecha_ingreso"].strftime("%d/%m/%Y") if primera["fecha_ingreso"] else "—"
        f_res_txt = primera["fecha_resolucion"].strftime("%d/%m/%Y") if primera["fecha_resolucion"] else f_ing_txt

        with st.container(border=True):
            st.markdown(
                f"""
                <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:8px;">
                    <div style="font-size:20px;font-weight:700;color:#4E73A3;">Solicitud #{esc(sol_sel)}</div>
                    <div>{badge_estado_html(primera['nombre_estado'])}</div>
                </div>
                <div style="font-size:14px;color:#1E293B;margin-bottom:8px;">
                    <strong>{esc(primera['nombre_estudiante'])}</strong> · {esc(primera['rut_estudiante'])}<br>
                    <span style="font-size:12.5px;color:#64748B;">{esc(primera['nombre_carrera'])}</span>
                </div>
                <div style="font-size:13px;color:#334155;margin-bottom:12px;">
                    {detalles_txt}
                </div>
                <div class="ucn-soft-box" style="margin-bottom:12px;">
                    <div class="ucn-soft-box-title" style="font-size:14px;">
                        📄 {esc(primera['nombre_archivo'] or 'Sin archivo')} · {esc(primera['tipo_documento'] or 'Certificado')}
                    </div>
                    <div class="ucn-soft-box-sub">
                        Recibido el {esc(f_ing_txt)}
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            observacion = st.text_area(
                "Observación de la revisión",
                value=primera["observacion_revision"],
                placeholder="Obligatoria al rechazar o solicitar nuevos antecedentes.",
                height=85,
                key=f"obs_rev_{sol_sel}",
            )

            b1, b2, b3 = st.columns([1.0, 1.0, 1.55], gap="small")
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
                <div style="margin-top:12px;padding-top:10px;border-top:1px solid #F1F5F9;">
                    <div style="font-size:12.5px;font-weight:700;color:#4E73A3;margin-bottom:4px;">
                        Historial de la solicitud #{esc(sol_sel)}
                    </div>
                    <div style="font-size:12px;color:#64748B;line-height:1.45;">
                        <strong>{esc(f_res_txt)}</strong> · {esc(primera['nombre_funcionario'])} ({esc(primera['rol_funcionario'])}) ·
                        <strong>{esc(primera['nombre_estado'])}</strong><br>
                        {esc(primera['observacion_revision'] or 'Solicitud recibida.')}
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

# ==============================================================================
# PANTALLA 05: CARGAR PLANILLA + CARGA CONFIRMADA
# ==============================================================================
def render_cargar_planilla():
    if st.session_state.usuario["rol"] != "Secretaría":
        st.session_state.pagina = "Inicio"
        st.rerun()

    df_all = cargar_hechos_detallados()
    total_sol = df_all["numero_solicitud"].nunique() if not df_all.empty else 0
    en_proc = df_all[df_all["nombre_estado"] == "En proceso"]["numero_solicitud"].nunique() if not df_all.empty else 0

    render_topbar("Inicio")

    if st.session_state.ultima_carga_confirmada is not None:
        res = st.session_state.ultima_carga_confirmada
        render_banner("Carga confirmada", "Resultado de la incorporación desde planilla.")
        render_eciem_nav_pills(total_sol, en_proc)
        st.markdown(
            f'<div class="ucn-strip-ok">{res["validas"]} registro(s) cargado(s). {res["errores"]} fila(s) omitida(s) por error.</div>',
            unsafe_allow_html=True,
        )
        with st.container(border=True):
            st.markdown(
                f"""
                <div style="font-size:18px;font-weight:700;color:#4E73A3;margin-bottom:6px;">📄 {esc(res['archivo'])}</div>
                <div style="font-size:14px;color:#334155;line-height:1.6;">
                    Las filas válidas quedaron incorporadas correctamente en el sistema.<br>
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

    render_banner("Cargar planilla", "Vista previa y validación antes de incorporar los registros.")
    render_eciem_nav_pills(total_sol, en_proc)

    estados, periodos, asignaturas, estudiantes = cargar_catalogos()
    periodo_opciones = {p["nombre_periodo"]: p["id_periodo"] for p in periodos}

    with st.container(border=True):
        c1, c2 = st.columns([2.2, 1.0], gap="large")
        with c1:
            archivo = st.file_uploader(
                "Archivo de entrada (.csv o .xlsx)",
                type=["csv", "xlsx"],
            )
        with c2:
            periodo_sel = st.selectbox("Período académico", list(periodo_opciones.keys()))

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

    def buscar_asignatura_y_paralelo(asig_txt: str, carrera_est: str, par_col: str = ""):
        raw = str(asig_txt).strip()
        par_res = par_col.strip().upper() if par_col else ""
        if not par_res and "-" in raw and not raw.upper().startswith(("ICO-", "IICG-")):
            partes = raw.rsplit("-", 1)
            if len(partes[1].strip()) <= 4:
                raw = partes[0].strip()
                par_res = partes[1].strip().upper()
        if not par_res:
            par_res = "A"

        a_low = raw.lower()
        candidatos = [a for a in asignaturas if a.get("carrera") == carrera_est] + asignaturas
        for a in candidatos:
            if a["codigo_asignatura"].strip().lower() == a_low or a["nombre_asignatura"].strip().lower() == a_low:
                return a, par_res
        return None, par_res

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
            errores_fila.append(f"RUT {rut_norm} no registrado")

        asig_raw = "" if pd.isna(row["Asignatura"]) else str(row["Asignatura"]).strip()
        par_raw = "" if ("Paralelo" not in df_raw.columns or pd.isna(row["Paralelo"])) else str(row["Paralelo"]).strip()
        carrera_est = est_obj["nombre_carrera"] if est_obj else ""
        asig_obj, par_final = buscar_asignatura_y_paralelo(asig_raw, carrera_est, par_raw)
        if asig_obj is None:
            errores_fila.append(f"Asignatura '{asig_raw}' inexistente")

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
            clave_u = (est_obj["rut"], f_entrega.isoformat(), asig_obj["id_paralelo"], par_final)
            if clave_u in claves_vistas:
                errores_fila.append("Fila duplicada")
            else:
                claves_vistas.add(clave_u)

        val_txt = "Válida" if not errores_fila else "Error: " + "; ".join(errores_fila)
        vista_previa.append(
            (fila_excel, rut_raw, row["Nombre"], asig_raw, par_final, row["Fecha inicio"], row["Fecha Termino"], val_txt)
        )
        if not errores_fila:
            filas_validas.append(
                {
                    "rut_estudiante": est_obj["rut"],
                    "id_paralelo": asig_obj["id_paralelo"],
                    "paralelo": par_final,
                    "fecha_entrega": f_entrega,
                    "fecha_inicio": f_ini,
                    "fecha_termino": f_ter,
                    "id_estado": id_estado,
                    "fecha_validacion": f_val,
                }
            )

    filas_html = "".join(
        f"<tr><td>{esc(f[0])}</td><td>{esc(f[1])}</td><td><strong>{esc(f[2])}</strong></td>"
        f"<td>{esc(f[3])}</td><td><strong>{esc(f[4])}</strong></td><td>{esc(f[5])}</td>"
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
                        <th>Paralelo</th><th>Inicio</th><th>Término</th><th>Validación</th>
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
                    "paralelo": item["paralelo"],
                    "id_estado": item["id_estado"],
                    "id_funcionario": id_func,
                    "id_periodo": id_periodo_sel,
                    "dias_tramitacion": dias_tram,
                    "cantidad_documentos_adjuntos": 1,
                    "tipo_documento": "Carga masiva",
                    "nombre_archivo": archivo.name,
                    "observacion_revision": "Importado desde planilla.",
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
# PANTALLA 06: GENERAR REPORTE / REPORTE LISTO
# ==============================================================================
def render_generar_reporte():
    df = cargar_hechos_detallados()
    total_sol = df["numero_solicitud"].nunique() if not df.empty else 0
    en_proc = df[df["nombre_estado"] == "En proceso"]["numero_solicitud"].nunique() if not df.empty else 0

    render_topbar("Volver")

    estados, periodos, _, _ = cargar_catalogos()
    nombres_periodos = [p["nombre_periodo"] for p in periodos]
    carreras_opc = ["Todas"] + CARRERAS_OFICIALES
    estados_opc = [e["nombre_estado"] for e in estados]

    filtros_guardados = st.session_state.rep_filtros
    idx_per = nombres_periodos.index(filtros_guardados["periodo"]) if filtros_guardados["periodo"] in nombres_periodos else 0
    idx_car = carreras_opc.index(filtros_guardados.get("carrera", "Todas")) if filtros_guardados.get("carrera", "Todas") in carreras_opc else 0
    idx_est = estados_opc.index(filtros_guardados["estado"]) if filtros_guardados["estado"] in estados_opc else (
        estados_opc.index("Aceptado") if "Aceptado" in estados_opc else 0
    )

    if not st.session_state.reporte_listo:
        render_banner("Generar reporte", "Inasistencias justificadas del período seleccionado.")
        render_eciem_nav_pills(total_sol, en_proc)
        c1, c2, c3 = st.columns(3, gap="medium")
        with c1:
            periodo_sel = st.selectbox("Período académico", nombres_periodos, index=idx_per)
        with c2:
            carrera_sel = st.selectbox("Carrera", carreras_opc, index=idx_car)
        with c3:
            estado_sel = st.selectbox("Estado actual", estados_opc, index=idx_est)
        st.markdown("<div style='height:8px;'></div>", unsafe_allow_html=True)
    else:
        periodo_sel = filtros_guardados["periodo"]
        carrera_sel = filtros_guardados.get("carrera", "Todas")
        estado_sel = filtros_guardados["estado"]
        render_banner("Reporte listo", "Inasistencias justificadas del período seleccionado.")
        render_eciem_nav_pills(total_sol, en_proc)
        st.markdown(
            f'<div class="ucn-strip-ok">📄 inasistencias_{esc(periodo_sel)}.csv · Listo para descargar</div>',
            unsafe_allow_html=True,
        )

    if df.empty:
        st.markdown('<div class="ucn-strip-info">No hay registros disponibles para generar reportes.</div>', unsafe_allow_html=True)
        return

    df_rep = df[(df["nombre_periodo"] == periodo_sel) & (df["nombre_estado"] == estado_sel)].copy()
    if carrera_sel != "Todas":
        df_rep = df_rep[df_rep["carrera_asignatura"] == carrera_sel]

    if df_rep.empty:
        st.markdown('<div class="ucn-strip-warn">No existen registros para los filtros seleccionados.</div>', unsafe_allow_html=True)
        if st.session_state.reporte_listo and st.button("Cambiar filtros", type="secondary"):
            st.session_state.reporte_listo = False
            st.rerun()
        return

    df_rep = df_rep.sort_values(["numero_solicitud", "nombre_asignatura", "paralelo"])

    filas_html = []
    for _, r in df_rep.iterrows():
        filas_html.append(
            f"<tr>"
            f"<td><span class='ucn-sol-id'>#{esc(r['numero_solicitud'])}</span></td>"
            f"<td><strong>{esc(r['nombre_estudiante'])}</strong></td>"
            f"<td>{esc(r['nombre_asignatura'])}</td>"
            f"<td><strong>{esc(r['paralelo'])}</strong></td>"
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
                        <th>Solicitud</th><th>Estudiante</th><th>Asignatura</th><th>Paralelo</th>
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
            <span>{int(df_rep['dias_ausencia'].sum())} días totales</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    df_csv = pd.DataFrame(
        {
            "Solicitud": df_rep["numero_solicitud"],
            "Estudiante": df_rep["nombre_estudiante"],
            "Carrera": df_rep["carrera_asignatura"],
            "Asignatura": df_rep["nombre_asignatura"],
            "Paralelo": df_rep["paralelo"],
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
                "carrera": carrera_sel,
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
