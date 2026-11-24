import base64
import html
import io
import os
import re
from datetime import date, datetime
import pandas as pd
import streamlit as st
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
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

ESTADOS_OFICIALES = ["En proceso", "Aceptado", "Rechazado"]
PERIODOS_DISPONIBLES = ["2026-2", "2026-1", "2027-1"]

NIVELES_MAPA = {
    "Nivel 1 (1° Semestre)": 1,
    "Nivel 2 (2° Semestre)": 2,
    "Nivel 3 (3° Semestre)": 3,
    "Nivel 4 (4° Semestre)": 4,
    "Nivel 5 (5° Semestre)": 5,
    "Nivel 6 (6° Semestre)": 6,
}

# ==============================================================================
# ESTILOS CSS (MODO CLARO BLINDADO + ESTÉTICA OFICIAL ECIEM UCN)
# ==============================================================================
CSS_BASE = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

:root, html, body, .stApp, [data-testid="stAppViewContainer"] {
    color-scheme: light !important;
    --primary-color: #003A70 !important;
    --background-color: #F5F8FC !important;
    --secondary-background-color: #FFFFFF !important;
    --text-color: #0F172A !important;
    --ucn-navy-dark: #002D72;
    --ucn-navy: #003A70;
    --eciem-slate: #4E73A3;
    --eciem-pill-bg: #EEF3F8;
    --ucn-gold: #E6B800;
}

[data-testid="stSidebar"],
[data-testid="collapsedControl"],
#MainMenu,
footer,
header[data-testid="stHeader"],
[data-testid="stToolbar"],
[data-testid="stDecoration"] {
    display: none !important;
    height: 0 !important;
}

html, body, [class*="css"], .stApp {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif !important;
    color: #0F172A !important;
    margin: 0 !important;
    padding: 0 !important;
}

[data-testid="stAppViewContainer"],
[data-testid="stMain"],
section.main {
    padding-top: 0 !important;
    margin-top: 0 !important;
}

.stApp {
    background: #F5F8FC !important;
}

.block-container {
    max-width: 1180px !important;
    padding-top: 1rem !important;
    padding-bottom: 3rem !important;
    padding-left: 1.5rem !important;
    padding-right: 1.5rem !important;
}

/* TARJETAS BLANCAS SÓLIDAS */
html body div[data-testid="stVerticalBlock"]:has(> [data-testid="stElementContainer"] .ucn-solid-card),
html body div[data-testid="stVerticalBlock"]:has(> .element-container .ucn-solid-card),
html body [data-testid="stVerticalBlockBorderWrapper"] {
    background-color: #FFFFFF !important;
    border: 1px solid #DCE5F0 !important;
    border-radius: 16px !important;
    padding: 1.5rem 1.75rem !important;
    box-shadow: 0 8px 26px rgba(0, 28, 70, 0.08) !important;
}

/* ENCABEZADO SUPERIOR */
.ucn-header-bar {
    background: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-radius: 14px;
    padding: 10px 22px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    box-shadow: 0 2px 10px rgba(15, 23, 42, 0.04);
    min-height: 60px;
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
    background: #CBD5E1;
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
    color: #475569;
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
    white-space: nowrap;
}

/* BANNER INSTITUCIONAL */
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

/* BOTONES TIPO PÍLDORA ECIEM / UCN */
html body div.stButton > button,
html body div.stDownloadButton > button,
html body div.stFormSubmitButton > button {
    border-radius: 999px !important;
    min-height: 42px !important;
    height: 42px !important;
    font-weight: 600 !important;
    font-size: 13.5px !important;
    padding: 0 20px !important;
    transition: all 0.16s ease !important;
    box-shadow: none !important;
    margin: 0 !important;
}

html body div.stButton > button[kind="primary"],
html body div.stButton > button[data-testid="stBaseButton-primary"],
html body div.stDownloadButton > button[kind="primary"],
html body div.stDownloadButton > button[data-testid="stBaseButton-primary"],
html body div.stFormSubmitButton > button,
html body div.stFormSubmitButton > button[kind="primary"],
html body div.stFormSubmitButton > button[data-testid="stBaseButton-primaryFormSubmit"] {
    background-color: #003A70 !important;
    border: 1px solid #003A70 !important;
    color: #FFFFFF !important;
    -webkit-text-fill-color: #FFFFFF !important;
}
html body div.stButton > button[kind="primary"]:hover,
html body div.stButton > button[data-testid="stBaseButton-primary"]:hover,
html body div.stDownloadButton > button[kind="primary"]:hover,
html body div.stFormSubmitButton > button:hover,
html body div.stFormSubmitButton > button[data-testid="stBaseButton-primaryFormSubmit"]:hover {
    background-color: #002D72 !important;
    border-color: #002D72 !important;
    color: #FFFFFF !important;
    -webkit-text-fill-color: #FFFFFF !important;
}

html body div.stButton > button[kind="secondary"],
html body div.stButton > button[data-testid="stBaseButton-secondary"],
html body div.stDownloadButton > button[kind="secondary"],
html body div.stFormSubmitButton > button[kind="secondary"] {
    background-color: #EEF3F8 !important;
    border: 1px solid #CBD5E1 !important;
    color: #0F172A !important;
    -webkit-text-fill-color: #0F172A !important;
}
html body div.stButton > button[kind="secondary"]:hover,
html body div.stButton > button[data-testid="stBaseButton-secondary"]:hover {
    background-color: #E1EAF4 !important;
    border-color: #003A70 !important;
    color: #003A70 !important;
    -webkit-text-fill-color: #003A70 !important;
}

/* BLINDAJE MODO CLARO EN INPUTS, SELECTS, TEXTAREAS Y CALENDARIOS */
html body [data-testid="stTextInput"] div,
html body [data-testid="stDateInput"] div,
html body [data-testid="stSelectbox"] div,
html body [data-testid="stTextArea"] div,
html body div[data-baseweb="input"],
html body div[data-baseweb="input"] div,
html body div[data-baseweb="base-input"],
html body div[data-baseweb="base-input"] div,
html body div[data-baseweb="select"],
html body div[data-baseweb="select"] div {
    background-color: #FFFFFF !important;
    color: #0F172A !important;
}

html body [data-testid="stTextInput"] div[data-baseweb="input"] > div,
html body [data-testid="stDateInput"] div[data-baseweb="input"] > div,
html body [data-testid="stSelectbox"] div[data-baseweb="select"] > div,
html body [data-testid="stTextArea"] textarea {
    border: 1px solid #CBD5E1 !important;
    border-radius: 10px !important;
    min-height: 42px !important;
    background-color: #FFFFFF !important;
}

html body div[data-baseweb="base-input"],
html body div[data-baseweb="base-input"] > div,
html body div[data-baseweb="select"] > div > div {
    border: none !important;
}

html body [data-testid="stTextInput"] input,
html body [data-testid="stDateInput"] input,
html body [data-testid="stSelectbox"] span,
html body [data-testid="stSelectbox"] div,
html body [data-testid="stSelectbox"] input,
html body [data-testid="stTextArea"] textarea,
html body div[data-baseweb="input"] input,
html body div[data-baseweb="base-input"] input,
html body div[data-baseweb="select"] span,
html body div[data-baseweb="select"] div {
    color: #0F172A !important;
    -webkit-text-fill-color: #0F172A !important;
    opacity: 1 !important;
    font-size: 14px !important;
    font-weight: 500 !important;
}

html body input::selection,
html body textarea::selection {
    background-color: #003A70 !important;
    color: #FFFFFF !important;
    -webkit-text-fill-color: #FFFFFF !important;
}

html body input::placeholder,
html body textarea::placeholder {
    color: #64748B !important;
    -webkit-text-fill-color: #64748B !important;
    opacity: 1 !important;
    font-weight: 400 !important;
}

html body [data-testid="stSelectbox"] svg,
html body [data-testid="stDateInput"] svg,
html body [data-testid="stTextInput"] svg,
html body div[data-baseweb="select"] svg,
html body div[data-baseweb="input"] svg {
    fill: #334155 !important;
    color: #334155 !important;
    opacity: 1 !important;
}

html body div[data-baseweb="input"] > div:focus-within,
html body div[data-baseweb="select"] > div:focus-within,
html body [data-testid="stTextArea"] textarea:focus {
    border-color: #003A70 !important;
    box-shadow: 0 0 0 1.5px #003A70 !important;
}

/* POPOVERS Y CALENDARIO EMERGENTE */
html body div[data-baseweb="popover"],
html body div[data-baseweb="popover"] div,
html body div[data-baseweb="popover"] ul,
html body div[data-baseweb="popover"] li,
html body div[data-baseweb="popover"] table,
html body div[data-baseweb="popover"] thead,
html body div[data-baseweb="popover"] tbody,
html body div[data-baseweb="popover"] tr,
html body div[data-baseweb="popover"] th,
html body div[data-baseweb="popover"] td,
html body div[data-baseweb="calendar"],
html body div[data-baseweb="calendar"] div,
html body div[data-baseweb="menu"],
html body ul[role="listbox"],
html body ul[role="listbox"] li {
    background-color: #FFFFFF !important;
    color: #0F172A !important;
    -webkit-text-fill-color: #0F172A !important;
    border-color: #E2E8F0 !important;
}

html body div[data-baseweb="popover"] *,
html body div[data-baseweb="calendar"] *,
html body ul[role="listbox"] * {
    color: #0F172A !important;
    -webkit-text-fill-color: #0F172A !important;
    opacity: 1 !important;
}

html body div[data-baseweb="calendar"] svg,
html body div[data-baseweb="popover"] svg {
    fill: #003A70 !important;
    color: #003A70 !important;
}

html body div[data-baseweb="calendar"] [aria-selected="true"],
html body div[data-baseweb="calendar"] [aria-selected="true"] *,
html body ul[role="listbox"] li:hover,
html body ul[role="listbox"] li:hover *,
html body ul[role="listbox"] li[aria-selected="true"],
html body ul[role="listbox"] li[aria-selected="true"] * {
    background-color: #003A70 !important;
    color: #FFFFFF !important;
    -webkit-text-fill-color: #FFFFFF !important;
    font-weight: 600 !important;
}

html body div[data-baseweb="calendar"] [role="gridcell"]:hover,
html body div[data-baseweb="calendar"] [role="gridcell"]:hover * {
    background-color: #EEF3F8 !important;
    color: #003A70 !important;
    -webkit-text-fill-color: #003A70 !important;
}

html body .stTextInput label,
html body .stSelectbox label,
html body .stDateInput label,
html body .stTextArea label,
html body .stFileUploader label,
html body .stTextInput label p,
html body .stSelectbox label p,
html body .stDateInput label p,
html body .stTextArea label p,
html body .stFileUploader label p {
    color: #1E293B !important;
    -webkit-text-fill-color: #1E293B !important;
    font-weight: 600 !important;
    font-size: 13.5px !important;
    margin-bottom: 4px !important;
}

html body [data-testid="stFileUploader"] section,
html body [data-testid="stFileUploaderDropzone"] {
    background-color: #F8FAFC !important;
    border: 1.5px dashed #CBD5E1 !important;
    border-radius: 12px !important;
    color: #1E293B !important;
}
html body [data-testid="stFileUploaderDropzone"] small,
html body [data-testid="stFileUploaderDropzone"] span,
html body [data-testid="stFileUploaderDropzone"] div {
    color: #475569 !important;
    -webkit-text-fill-color: #475569 !important;
}
html body [data-testid="stFileUploaderDropzone"] button {
    background-color: #FFFFFF !important;
    color: #003A70 !important;
    -webkit-text-fill-color: #003A70 !important;
    border: 1px solid #CBD5E1 !important;
    border-radius: 999px !important;
}

/* TARJETAS KPI */
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
.ucn-kpi-card.green-accent {
    border-top-color: #256747;
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
    font-size: 32px;
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
.ucn-kpi-card.green-accent .ucn-kpi-number {
    background: #EAF5EE;
    color: #256747;
}

/* TABLAS MODERNAS */
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

/* PASOS NUMERADOS */
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
    background: #003A70;
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

/* FRANJAS DE FEEDBACK */
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
    color: #003A70;
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
# UTILIDADES DE RUT, EXCEL INSTITUCIONAL, ANTI-DUPLICADOS Y BASE DE DATOS
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

def limpiar_caracteres_rut(rut_str: str) -> str:
    return re.sub(r"[^0-9kK]", "", str(rut_str or "")).upper()

def normalizar_rut(rut_str: str) -> str:
    limpio = limpiar_caracteres_rut(rut_str)
    if len(limpio) >= 2:
        return f"{limpio[:-1]}-{limpio[-1]}"
    return limpio

def formatear_rut_visual(rut_str: str) -> str:
    limpio = limpiar_caracteres_rut(rut_str)
    if len(limpio) < 2:
        return str(rut_str or "").strip().upper()
    cuerpo, dv = limpio[:-1], limpio[-1]
    if cuerpo.isdigit():
        cuerpo_puntos = f"{int(cuerpo):,}".replace(",", ".")
    else:
        cuerpo_puntos = cuerpo
    return f"{cuerpo_puntos}-{dv}"

def validar_rut_chileno(rut_str: str) -> bool:
    limpio = limpiar_caracteres_rut(rut_str)
    if len(limpio) < 2:
        return False
    cuerpo, dv = limpio[:-1], limpio[-1]
    if not cuerpo.isdigit():
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
    asignaturas = (
        supabase.table("dim_asignatura")
        .select("*")
        .order("carrera")
        .order("semestre")
        .order("id_asignatura")
        .execute()
        .data
    )
    estudiantes = supabase.table("dim_estudiante").select("*").execute().data
    return asignaturas, estudiantes

def cargar_hechos_detallados() -> pd.DataFrame:
    res = (
        supabase.table("hechos_justificacion")
        .select(
            "id_hecho, numero_solicitud, id_fecha_ingreso, id_fecha_resolucion, "
            "fecha_inicio_ausencia, fecha_termino_ausencia, rut_estudiante, "
            "id_asignatura, paralelo, estado, periodo, id_funcionario, "
            "dias_tramitacion, cantidad_documentos_adjuntos, tipo_documento, "
            "nombre_archivo, observacion_revision, "
            "dim_estudiante(rut, nombre_estudiante, nombre_carrera, anio_ingreso, estado_matricula), "
            "dim_asignatura(id_asignatura, carrera, semestre, codigo_asignatura, nombre_asignatura), "
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
        par_txt = (r.get("paralelo") or "A").strip().upper()
        nom_asig = asig.get("nombre_asignatura", "")

        filas.append(
            {
                "id_hecho": r["id_hecho"],
                "numero_solicitud": r["numero_solicitud"],
                "fecha_ingreso": fecha_ingreso,
                "fecha_resolucion": fecha_resolucion,
                "fecha_inicio_ausencia": f_ini,
                "fecha_termino_ausencia": f_ter,
                "dias_ausencia": dias_ausencia,
                "rut_bd": r["rut_estudiante"],
                "rut_estudiante": formatear_rut_visual(r["rut_estudiante"]),
                "nombre_estudiante": est.get("nombre_estudiante", ""),
                "nombre_carrera": est.get("nombre_carrera", ""),
                "id_asignatura": r["id_asignatura"],
                "carrera_asignatura": asig.get("carrera", ""),
                "semestre": asig.get("semestre", 1),
                "codigo_asignatura": asig.get("codigo_asignatura", ""),
                "nombre_asignatura": nom_asig,
                "paralelo": par_txt,
                "estado": r.get("estado", "En proceso"),
                "periodo": r.get("periodo", "2026-2"),
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

def verificar_duplicado_o_cruce(
    df_existente: pd.DataFrame,
    rut_bd: str,
    id_asignatura: int,
    paralelo: str,
    f_ini: date,
    f_ter: date,
):
    """
    Revisa si ya existe un registro ACTIVO ('En proceso' o 'Aceptado') para el mismo
    estudiante, asignatura y paralelo con fechas idénticas o solapadas.
    Permite reingreso si el registro anterior fue 'Rechazado'.
    """
    if df_existente.empty:
        return None

    par_norm = paralelo.strip().upper()
    activos = df_existente[
        (df_existente["rut_bd"] == rut_bd)
        & (df_existente["id_asignatura"] == int(id_asignatura))
        & (df_existente["paralelo"].str.upper() == par_norm)
        & (df_existente["estado"].isin(["En proceso", "Aceptado"]))
    ]
    for _, ex in activos.iterrows():
        ex_ini = ex["fecha_inicio_ausencia"]
        ex_ter = ex["fecha_termino_ausencia"]
        if f_ini <= ex_ter and f_ter >= ex_ini:
            tipo = "duplicado exacto" if (f_ini == ex_ini and f_ter == ex_ter) else "cruce de fechas"
            return (
                f"Se detectó un {tipo} con la Solicitud #{ex['numero_solicitud']} "
                f"({ex['estado']}) en {ex['nombre_asignatura']} (Par. {par_norm}, "
                f"{formatear_rango_inasistencia(ex_ini, ex_ter)})."
            )
    return None

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

def generar_excel_institucional(df_datos: pd.DataFrame, titulo_hoja: str, subtitulo: str) -> bytes:
    """Genera un archivo .xlsx con formato institucional UCN/ECIEM listo para entregar."""
    wb = Workbook()
    ws = wb.active
    ws.title = "Inasistencias"
    ws.views.sheetView[0].showGridLines = True

    fill_banner = PatternFill(start_color="002D72", end_color="002D72", fill_type="solid")
    fill_sub = PatternFill(start_color="EEF3F8", end_color="EEF3F8", fill_type="solid")
    fill_header = PatternFill(start_color="003A70", end_color="003A70", fill_type="solid")
    fill_zebra = PatternFill(start_color="F8FAFC", end_color="F8FAFC", fill_type="solid")
    fill_white = PatternFill(start_color="FFFFFF", end_color="FFFFFF", fill_type="solid")
    fill_total = PatternFill(start_color="EEF3F8", end_color="EEF3F8", fill_type="solid")

    font_banner = Font(name="Calibri", size=13, bold=True, color="FFFFFF")
    font_sub = Font(name="Calibri", size=10, italic=True, color="334155")
    font_header = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
    font_body = Font(name="Calibri", size=10, color="1E293B")
    font_bold = Font(name="Calibri", size=10, bold=True, color="003A70")
    font_total = Font(name="Calibri", size=10, bold=True, color="002D72")

    thin_side = Side(border_style="thin", color="CBD5E1")
    gold_bottom = Side(border_style="medium", color="E6B800")
    border_cell = Border(left=thin_side, right=thin_side, top=thin_side, bottom=thin_side)
    border_banner = Border(bottom=gold_bottom)

    num_cols = len(df_datos.columns)
    last_col_letter = get_column_letter(num_cols)

    ws.merge_cells(f"A1:{last_col_letter}1")
    ws["A1"] = titulo_hoja
    ws["A1"].font = font_banner
    ws["A1"].fill = fill_banner
    ws["A1"].alignment = Alignment(horizontal="left", vertical="center", indent=1)
    ws.row_dimensions[1].height = 30
    for c in range(1, num_cols + 1):
        ws.cell(row=1, column=c).fill = fill_banner
        ws.cell(row=1, column=c).border = border_banner

    ws.merge_cells(f"A2:{last_col_letter}2")
    ws["A2"] = subtitulo
    ws["A2"].font = font_sub
    ws["A2"].fill = fill_sub
    ws["A2"].alignment = Alignment(horizontal="left", vertical="center", indent=1)
    ws.row_dimensions[2].height = 22
    for c in range(1, num_cols + 1):
        ws.cell(row=2, column=c).fill = fill_sub

    ws.row_dimensions[3].height = 8

    header_row = 4
    ws.row_dimensions[header_row].height = 26
    centered_cols = {"Solicitud", "RUT", "Paralelo", "Desde", "Hasta", "Días", "Estado", "Nivel"}

    for col_idx, col_name in enumerate(df_datos.columns, start=1):
        cell = ws.cell(row=header_row, column=col_idx, value=col_name)
        cell.font = font_header
        cell.fill = fill_header
        cell.border = border_cell
        cell.alignment = Alignment(
            horizontal="center" if col_name in centered_cols else "left",
            vertical="center",
        )

    for row_offset, (_, row) in enumerate(df_datos.iterrows(), start=1):
        r_idx = header_row + row_offset
        ws.row_dimensions[r_idx].height = 22
        row_fill = fill_zebra if row_offset % 2 == 0 else fill_white
        for col_idx, col_name in enumerate(df_datos.columns, start=1):
            cell = ws.cell(row=r_idx, column=col_idx, value=row[col_name])
            cell.fill = row_fill
            cell.border = border_cell
            cell.font = font_bold if col_name == "Solicitud" else font_body
            cell.alignment = Alignment(
                horizontal="center" if col_name in centered_cols else "left",
                vertical="center",
            )

    total_row = header_row + len(df_datos) + 1
    ws.row_dimensions[total_row].height = 24
    for col_idx, col_name in enumerate(df_datos.columns, start=1):
        cell = ws.cell(row=total_row, column=col_idx)
        cell.fill = fill_total
        cell.border = border_cell
        cell.font = font_total
        if col_idx == 1:
            cell.value = "Total"
            cell.alignment = Alignment(horizontal="center", vertical="center")
        elif col_idx == 2:
            cell.value = f"{len(df_datos)} registro(s)"
            cell.alignment = Alignment(horizontal="left", vertical="center")
        elif col_name == "Días":
            cell.value = int(df_datos["Días"].sum())
            cell.alignment = Alignment(horizontal="center", vertical="center")

    for col_idx, col_name in enumerate(df_datos.columns, start=1):
        max_len = max([len(str(col_name))] + [len(str(v)) for v in df_datos[col_name].tolist()])
        ws.column_dimensions[get_column_letter(col_idx)].width = max(min(max_len + 5, 48), 13)

    ws.freeze_panes = f"A{header_row + 1}"
    ws.auto_filter.ref = f"A{header_row}:{last_col_letter}{header_row + len(df_datos)}"

    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()

# ==============================================================================
# COMPONENTES DE LAYOUT REUTILIZABLES
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
    rol = user["rol"]
    if rol == "Docente":
        etiqueta_rol = f"Docente · {user['nombre_funcionario']}"
    elif rol == "Secretaría":
        etiqueta_rol = "Secretaría"
    else:
        etiqueta_rol = "Jefatura de Carrera"

    if rol == "Docente":
        col_brand, col_logout = st.columns([8.4, 1.6], vertical_alignment="center")
        with col_brand:
            st.markdown(
                f"""
                <div class="ucn-header-bar">
                    <div class="ucn-brand-group">
                        {brand_logos_html()}
                    </div>
                    <span class="ucn-role-pill">{esc(etiqueta_rol)}</span>
                </div>
                """,
                unsafe_allow_html=True,
            )
        with col_logout:
            if st.button("Cerrar sesión", key="nav_top_logout_doc", type="secondary", use_container_width=True):
                st.session_state.usuario = None
                st.session_state.pagina = "Inicio"
                st.rerun()
        return

    col_brand, col_nav1, col_nav2 = st.columns([7.2, 1.3, 1.5], vertical_alignment="center")
    with col_brand:
        st.markdown(
            f"""
            <div class="ucn-header-bar">
                <div class="ucn-brand-group">
                    {brand_logos_html()}
                </div>
                <span class="ucn-role-pill">{esc(etiqueta_rol)}</span>
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

def render_banner(titulo: str, subtitulo: str, tag: str = "Gestión de Inasistencias"):
    st.markdown(
        f"""
        <div class="ucn-banner">
            <div>
                <h1>{esc(titulo)}</h1>
                <p>{esc(subtitulo)}</p>
            </div>
            <span class="ucn-banner-tag">{esc(tag)}</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

def render_eciem_nav_pills(total_sol: int = 0, en_proc: int = 0):
    rol = st.session_state.usuario["rol"]
    pag = st.session_state.pagina

    if rol == "Secretaría":
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
    elif rol == "Jefatura de Carrera":
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
    "modo_registro_docente": False,
    "detalles_pendientes": [],
    "ultima_solicitud_guardada": None,
    "ultima_carga_confirmada": None,
    "reporte_listo": False,
    "rep_filtros": {"periodo": "2026-2", "carrera": "Todas", "estado": "Aceptado"},
    "filtro_consulta_rut": "",
    "filtro_consulta_estado": "Todos",
    "reg_rut_input": "",
    "reg_nombre_est": "",
    "reg_carrera_sel": CARRERAS_OFICIALES[0],
    "ultimo_rut_autodetectado": "",
    "limpiar_form_registro": False,
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ==============================================================================
# PANTALLA 01: INICIAR SESIÓN (SECRETARÍA / JEFATURA / DOCENTE + REGISTRO DOCENTE)
# ==============================================================================
def render_login():
    fondo_css = (
        f"linear-gradient(90deg, rgba(0, 45, 114, 0.88) 0%, rgba(0, 58, 112, 0.78) 52%, rgba(0, 58, 112, 0.65) 100%), url('{FONDO_CAMPUS_B64}')"
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
            max-width: 1240px !important;
            padding-top: 96px !important;
            padding-bottom: 2rem !important;
            padding-left: 2rem !important;
            padding-right: 2rem !important;
        }}
        .ucn-login-fixedbar {{
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            width: 100%;
            height: 68px;
            z-index: 9999;
            background: #FFFFFF;
            border-bottom: 1px solid #E2E8F0;
            padding: 0 44px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            box-shadow: 0 2px 10px rgba(0, 25, 65, 0.08);
            box-sizing: border-box;
        }}
        .ucn-login-left-col {{
            min-height: 450px;
            border-right: 4px solid #E6B800;
            padding-right: 36px;
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

        <div class="ucn-login-fixedbar">
            <div class="ucn-brand-group">
                {brand_logos_html()}
            </div>
            <div class="ucn-campus-tag">Gestión de Inasistencias · Campus Guayacán</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    col_left, col_right = st.columns([4.2, 5.8], gap="large", vertical_alignment="center")

    with col_left:
        st.markdown(
            """
            <div class="ucn-login-left-col">
                <div class="ucn-hero-kicker">GESTIÓN ACADÉMICA</div>
                <div class="ucn-hero-h1">Gestión de<br>inasistencias</div>
                <div class="ucn-hero-p">Recepción, revisión, seguimiento y consulta docente de justificaciones.</div>
                <div class="ucn-hero-caption">Escuela de Ciencias Empresariales · Coquimbo</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col_right:
        with st.container(border=True):
            st.markdown('<span class="ucn-solid-card"></span>', unsafe_allow_html=True)

            # ---- MODO REGISTRO DE DOCENTE ----
            if st.session_state.modo_registro_docente:
                st.markdown(
                    """
                    <div style="font-size:24px;font-weight:700;color:#0F172A;margin-bottom:4px;">Registro de docente</div>
                    <div style="font-size:13.5px;color:#475569;margin-bottom:16px;">Crea tu cuenta para consultar las inasistencias justificadas de tus cursos.</div>
                    """,
                    unsafe_allow_html=True,
                )
                with st.form("form_reg_docente", border=False):
                    nom_doc = st.text_input("Nombre completo", placeholder="Ej.: Prof. Carlos Silva")
                    mail_doc = st.text_input("Correo institucional", placeholder="nombre.apellido@ucn.cl")
                    pass_doc = st.text_input("Contraseña", type="password", placeholder="Mínimo 6 caracteres")
                    pass_doc2 = st.text_input("Confirmar contraseña", type="password", placeholder="Repite la contraseña")
                    st.markdown("<div style='height:6px;'></div>", unsafe_allow_html=True)
                    crear_btn = st.form_submit_button("Crear cuenta docente", type="primary", use_container_width=True)

                if st.button("← Volver a Iniciar sesión", type="secondary", use_container_width=True):
                    st.session_state.modo_registro_docente = False
                    st.rerun()

                if crear_btn:
                    mail_clean = mail_doc.strip().lower()
                    errores = []
                    if not nom_doc.strip():
                        errores.append("Ingresa tu nombre completo.")
                    if not validar_email(mail_clean):
                        errores.append("Ingresa un correo electrónico válido.")
                    if len(pass_doc) < 6:
                        errores.append("La contraseña debe tener al menos 6 caracteres.")
                    if pass_doc != pass_doc2:
                        errores.append("Las contraseñas no coinciden.")

                    if errores:
                        for e in errores:
                            st.markdown(f'<div class="ucn-strip-err">{esc(e)}</div>', unsafe_allow_html=True)
                        return

                    existe = supabase.table("dim_docente").select("id_docente").eq("email", mail_clean).execute()
                    if existe.data:
                        st.markdown('<div class="ucn-strip-err">Ya existe una cuenta docente registrada con ese correo.</div>', unsafe_allow_html=True)
                        return

                    supabase.table("dim_docente").insert(
                        {
                            "nombre_docente": nom_doc.strip(),
                            "email": mail_clean,
                            "contrasena": pass_doc,
                        }
                    ).execute()
                    st.session_state.modo_registro_docente = False
                    st.session_state.perfil_login = "Docente"
                    st.markdown('<div class="ucn-strip-ok">Cuenta creada correctamente. Ya puedes iniciar sesión.</div>', unsafe_allow_html=True)
                return

            # ---- MODO INICIO DE SESIÓN ----
            st.markdown(
                """
                <div style="font-size:26px;font-weight:700;color:#0F172A;margin-bottom:4px;">Iniciar sesión</div>
                <div style="font-size:14px;color:#475569;margin-bottom:16px;">Selecciona tu perfil para continuar.</div>
                """,
                unsafe_allow_html=True,
            )

            p1, p2, p3 = st.columns(3, gap="small")
            perfil = st.session_state.perfil_login
            with p1:
                if st.button("Secretaría", type="primary" if perfil == "Secretaría" else "secondary", use_container_width=True, key="btn_p_sec"):
                    st.session_state.perfil_login = "Secretaría"
                    st.rerun()
            with p2:
                if st.button("Jefatura", type="primary" if perfil == "Jefatura de Carrera" else "secondary", use_container_width=True, key="btn_p_jef"):
                    st.session_state.perfil_login = "Jefatura de Carrera"
                    st.rerun()
            with p3:
                if st.button("Docente", type="primary" if perfil == "Docente" else "secondary", use_container_width=True, key="btn_p_doc"):
                    st.session_state.perfil_login = "Docente"
                    st.rerun()

            st.markdown("<div style='height:8px;'></div>", unsafe_allow_html=True)

            if perfil == "Secretaría":
                placeholder_correo = "secretaria.iicg@ucn.cl"
            elif perfil == "Jefatura de Carrera":
                placeholder_correo = "jc.iicg.cqbo@ucn.cl"
            else:
                placeholder_correo = "docente@ucn.cl"

            with st.form("form_login_ucn", border=False):
                correo = st.text_input("Correo institucional", placeholder=placeholder_correo)
                contrasena = st.text_input("Contraseña", type="password", placeholder="Ingresa tu contraseña")
                st.markdown("<div style='height:6px;'></div>", unsafe_allow_html=True)
                ingresar = st.form_submit_button("Ingresar", type="primary", use_container_width=True)

            if perfil == "Docente":
                if st.button("¿Primera vez? Crear cuenta docente", type="secondary", use_container_width=True):
                    st.session_state.modo_registro_docente = True
                    st.rerun()

            if ingresar:
                mail_clean = correo.strip().lower()
                if not mail_clean or not validar_email(mail_clean):
                    st.markdown('<div class="ucn-strip-err">Ingresa un correo válido.</div>', unsafe_allow_html=True)
                    return

                if perfil == "Docente":
                    res = (
                        supabase.table("dim_docente")
                        .select("id_docente, nombre_docente, email, contrasena")
                        .eq("email", mail_clean)
                        .execute()
                    )
                    if not res.data or res.data[0]["contrasena"] != contrasena:
                        st.markdown('<div class="ucn-strip-err">Correo o contraseña incorrectos.</div>', unsafe_allow_html=True)
                        return
                    doc = res.data[0]
                    st.session_state.usuario = {
                        "id_funcionario": doc["id_docente"],
                        "nombre_funcionario": doc["nombre_docente"],
                        "rol": "Docente",
                        "email": doc["email"],
                    }
                    st.session_state.pagina = "Portal Docente"
                    st.rerun()
                else:
                    res = (
                        supabase.table("dim_funcionario")
                        .select("id_funcionario, nombre_funcionario, rol, email, contrasena")
                        .eq("email", mail_clean)
                        .eq("rol", perfil)
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
# PANEL DOCENTE (SOLO LECTURA + FILTROS POR ASIGNATURA, PARALELO Y ESTUDIANTE)
# ==============================================================================
def render_portal_docente():
    render_topbar()
    render_banner(
        "Consulta de Inasistencias Justificadas",
        "Visualiza únicamente las inasistencias aceptadas por Jefatura de Carrera. Usa los filtros para revisar tus cursos.",
        tag="Portal Docente · Solo lectura",
    )

    df_all = cargar_hechos_detallados()
    asignaturas, _ = cargar_catalogos()

    # El docente SOLO puede ver solicitudes ACEPTADAS
    df_acc = df_all[df_all["estado"] == "Aceptado"].copy() if not df_all.empty else pd.DataFrame()

    with st.container(border=True):
        st.markdown('<span class="ucn-solid-card"></span>', unsafe_allow_html=True)
        f1, f2, f3, f4 = st.columns([0.9, 1.35, 1.45, 0.85], gap="small")

        periodos_en_datos = sorted(df_acc["periodo"].unique().tolist(), reverse=True) if not df_acc.empty else []
        periodos_opc = ["Todos"] + sorted(list(set(PERIODOS_DISPONIBLES + periodos_en_datos)), reverse=True)
        with f1:
            per_sel = st.selectbox("Período", periodos_opc, index=1 if len(periodos_opc) > 1 else 0, key="doc_per")

        with f2:
            car_sel = st.selectbox("Carrera", ["Todas"] + CARRERAS_OFICIALES, key="doc_car")

        asig_base = [a for a in asignaturas if (car_sel == "Todas" or a["carrera"] == car_sel)]
        nombres_asig = sorted(list({a["nombre_asignatura"] for a in asig_base}))
        with f3:
            asig_sel = st.selectbox("Asignatura", ["Todas"] + nombres_asig, key="doc_asig")

        if not df_acc.empty:
            sub_par = df_acc.copy()
            if per_sel != "Todos":
                sub_par = sub_par[sub_par["periodo"] == per_sel]
            if car_sel != "Todas":
                sub_par = sub_par[sub_par["carrera_asignatura"] == car_sel]
            if asig_sel != "Todas":
                sub_par = sub_par[sub_par["nombre_asignatura"] == asig_sel]
            paralelos_disp = sorted(sub_par["paralelo"].dropna().unique().tolist())
        else:
            paralelos_disp = []

        with f4:
            par_sel = st.selectbox("Paralelo", ["Todos"] + paralelos_disp, key="doc_par")

        b_est = st.text_input("Buscar por nombre o RUT del estudiante (opcional)", placeholder="Ej.: 12.345.678-5 o Camila Rojas", key="doc_busq")

    df_fil = df_acc.copy()
    if not df_fil.empty:
        if per_sel != "Todos":
            df_fil = df_fil[df_fil["periodo"] == per_sel]
        if car_sel != "Todas":
            df_fil = df_fil[df_fil["carrera_asignatura"] == car_sel]
        if asig_sel != "Todas":
            df_fil = df_fil[df_fil["nombre_asignatura"] == asig_sel]
        if par_sel != "Todos":
            df_fil = df_fil[df_fil["paralelo"] == par_sel]
        if b_est.strip():
            q_low = b_est.strip().lower()
            q_rut_vis = formatear_rut_visual(b_est).lower()
            df_fil = df_fil[
                df_fil["nombre_estudiante"].str.lower().str.contains(q_low, na=False)
                | df_fil["rut_estudiante"].str.lower().str.contains(q_rut_vis, na=False)
                | df_fil["rut_bd"].str.lower().str.contains(normalizar_rut(b_est).lower(), na=False)
            ]

    st.markdown("<div style='height:10px;'></div>", unsafe_allow_html=True)

    n_reg = len(df_fil)
    n_est = df_fil["rut_bd"].nunique() if not df_fil.empty else 0
    n_dias = int(df_fil["dias_ausencia"].sum()) if not df_fil.empty else 0

    k1, k2, k3 = st.columns(3, gap="medium")
    with k1:
        st.markdown(
            f'<div class="ucn-kpi-card green-accent"><div><div class="ucn-kpi-info-title">Justificaciones vigentes</div>'
            f'<div class="ucn-kpi-info-sub">Según filtros aplicados</div></div><div class="ucn-kpi-number">{n_reg}</div></div>',
            unsafe_allow_html=True,
        )
    with k2:
        st.markdown(
            f'<div class="ucn-kpi-card"><div><div class="ucn-kpi-info-title">Estudiantes justificados</div>'
            f'<div class="ucn-kpi-info-sub">Alumnos únicos en lista</div></div><div class="ucn-kpi-number">{n_est}</div></div>',
            unsafe_allow_html=True,
        )
    with k3:
        st.markdown(
            f'<div class="ucn-kpi-card gold-accent"><div><div class="ucn-kpi-info-title">Total de días justificados</div>'
            f'<div class="ucn-kpi-info-sub">Suma inclusiva de fechas</div></div><div class="ucn-kpi-number">{n_dias}</div></div>',
            unsafe_allow_html=True,
        )

    if df_fil.empty:
        st.markdown('<div class="ucn-strip-info">No hay inasistencias aceptadas que coincidan con los filtros seleccionados.</div>', unsafe_allow_html=True)
        return

    df_fil = df_fil.sort_values(["nombre_asignatura", "paralelo", "fecha_inicio_ausencia"], ascending=[True, True, False])

    filas_html = []
    for _, r in df_fil.iterrows():
        filas_html.append(
            f"<tr>"
            f"<td><span class='ucn-sol-id'>#{esc(r['numero_solicitud'])}</span></td>"
            f"<td><strong>{esc(r['nombre_estudiante'])}</strong></td>"
            f"<td>{esc(r['rut_estudiante'])}</td>"
            f"<td>{esc(r['nombre_asignatura'])}</td>"
            f"<td><strong>{esc(r['paralelo'])}</strong></td>"
            f"<td>📅 {esc(r['fecha_inicio_ausencia'].strftime('%d/%m/%Y'))}</td>"
            f"<td>📅 {esc(r['fecha_termino_ausencia'].strftime('%d/%m/%Y'))}</td>"
            f"<td><strong>{esc(r['dias_ausencia'])}</strong></td>"
            f"</tr>"
        )

    st.markdown(
        f"""
        <div class="ucn-section-title">Listado de inasistencias aceptadas</div>
        <div class="ucn-table-wrap">
            <table class="ucn-table">
                <thead>
                    <tr>
                        <th>Solicitud</th><th>Estudiante</th><th>RUT</th><th>Asignatura</th>
                        <th>Paralelo</th><th>Desde</th><th>Hasta</th><th>Días</th>
                    </tr>
                </thead>
                <tbody>{''.join(filas_html)}</tbody>
            </table>
        </div>
        """,
        unsafe_allow_html=True,
    )

    df_export = pd.DataFrame(
        {
            "Solicitud": df_fil["numero_solicitud"],
            "Estudiante": df_fil["nombre_estudiante"],
            "RUT": df_fil["rut_estudiante"],
            "Carrera": df_fil["carrera_asignatura"],
            "Asignatura": df_fil["nombre_asignatura"],
            "Paralelo": df_fil["paralelo"],
            "Desde": df_fil["fecha_inicio_ausencia"].apply(lambda d: d.strftime("%d/%m/%Y")),
            "Hasta": df_fil["fecha_termino_ausencia"].apply(lambda d: d.strftime("%d/%m/%Y")),
            "Días": df_fil["dias_ausencia"],
        }
    )
    xlsx_bytes = generar_excel_institucional(
        df_export,
        f"INASISTENCIAS JUSTIFICADAS · CONSULTA DOCENTE ({per_sel})",
        f"Asignatura: {asig_sel}  |  Paralelo: {par_sel}  |  Descargado el {date.today().strftime('%d/%m/%Y')}",
    )

    d1, _ = st.columns([2.6, 7.4])
    d1.download_button(
        label="📥 Descargar nómina en Excel (.xlsx)",
        data=xlsx_bytes,
        file_name=f"nomina_inasistencias_{per_sel}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        type="primary",
        use_container_width=True,
    )

# ==============================================================================
# PANTALLA 02: INICIO (DASHBOARD SECRETARÍA / JEFATURA)
# ==============================================================================
def render_inicio():
    user = st.session_state.usuario
    es_secretaria = user["rol"] == "Secretaría"

    df = cargar_hechos_detallados()
    periodo_actual = PERIODOS_DISPONIBLES[0]

    total_solicitudes = df["numero_solicitud"].nunique() if not df.empty else 0
    en_proceso = (
        df[df["estado"] == "En proceso"]["numero_solicitud"].nunique()
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
            Estado=("estado", "first"),
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
# PANTALLA 03: REGISTRAR SOLICITUD (ANTI-DUPLICADOS + AUTOFORMATO RUT)
# ==============================================================================
def on_rut_change_callback(mapa_estudiantes_ref):
    raw_val = st.session_state.get("reg_rut_input", "")
    formateado = formatear_rut_visual(raw_val)
    st.session_state["reg_rut_input"] = formateado
    rut_bd = normalizar_rut(formateado)
    if validar_rut_chileno(formateado) and rut_bd != st.session_state.get("ultimo_rut_autodetectado", ""):
        est_existente = mapa_estudiantes_ref.get(rut_bd)
        if est_existente:
            st.session_state["reg_nombre_est"] = est_existente["nombre_estudiante"]
            if est_existente["nombre_carrera"] in CARRERAS_OFICIALES:
                st.session_state["reg_carrera_sel"] = est_existente["nombre_carrera"]
        st.session_state["ultimo_rut_autodetectado"] = rut_bd

def render_registrar_solicitud():
    if st.session_state.usuario["rol"] != "Secretaría":
        st.session_state.pagina = "Inicio"
        st.rerun()

    if st.session_state.get("limpiar_form_registro"):
        st.session_state["reg_rut_input"] = ""
        st.session_state["reg_nombre_est"] = ""
        st.session_state["ultimo_rut_autodetectado"] = ""
        st.session_state["limpiar_form_registro"] = False

    df_all = cargar_hechos_detallados()
    total_sol = df_all["numero_solicitud"].nunique() if not df_all.empty else 0
    en_proc = df_all[df_all["estado"] == "En proceso"]["numero_solicitud"].nunique() if not df_all.empty else 0

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
            f"<td>Nivel {esc(d['nivel'])}</td>"
            f"<td>{esc(d['nombre_asignatura'])}</td>"
            f"<td><strong>{esc(d['paralelo'])}</strong></td>"
            f"<td>{esc(d['fecha_inicio'].strftime('%d/%m/%Y'))}</td>"
            f"<td>{esc(d['fecha_termino'].strftime('%d/%m/%Y'))}</td></tr>"
            for d in info["detalles"]
        )

        with st.container(border=True):
            st.markdown(
                f"""
                <span class="ucn-solid-card"></span>
                <div style="margin-bottom:10px;">{badge_estado_html('En proceso')}</div>
                <div style="font-size:19px;font-weight:700;color:#1E293B;margin-bottom:4px;">
                    {esc(info['nombre_estudiante'])} · {esc(info['rut_visual'])}
                </div>
                <div style="font-size:13.5px;color:#475569;margin-bottom:14px;">
                    Entrega y recepción: {esc(info['fecha_entrega'].strftime('%d/%m/%Y'))} ·
                    {esc(info['nombre_archivo'])} · {len(info['detalles'])} detalle(s)
                </div>
                <div class="ucn-table-wrap" style="margin-bottom:0;">
                    <table class="ucn-table">
                        <thead><tr><th>Carrera</th><th>Nivel</th><th>Asignatura</th><th>Paralelo</th><th>Desde</th><th>Hasta</th></tr></thead>
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

    asignaturas, estudiantes = cargar_catalogos()
    mapa_estudiantes = {normalizar_rut(e["rut"]): e for e in estudiantes}

    if not asignaturas:
        st.markdown('<div class="ucn-strip-err">Faltan asignaturas en la base de datos.</div>', unsafe_allow_html=True)
        return

    # PASO 1: DATOS DEL ESTUDIANTE
    with st.container(border=True):
        st.markdown(
            """
            <span class="ucn-solid-card"></span>
            <div class="ucn-step-header">
                <span class="ucn-step-num">1</span>
                <span class="ucn-step-title">Datos del estudiante</span>
                <span class="ucn-step-sub">El RUT se formatea automáticamente al ingresarlo</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

        c_rut, c_nom, c_car = st.columns([1.0, 1.4, 1.3], gap="medium")

        with c_rut:
            rut_raw_val = st.text_input(
                "RUT del estudiante",
                key="reg_rut_input",
                placeholder="Ej.: 12.345.678-5",
                on_change=on_rut_change_callback,
                args=(mapa_estudiantes,),
            )
            rut_formateado = formatear_rut_visual(rut_raw_val)
            rut_valido = validar_rut_chileno(rut_formateado) if rut_raw_val.strip() else False
            if rut_raw_val.strip() and not rut_valido:
                st.markdown('<div class="ucn-strip-err">Dígito verificador inválido.</div>', unsafe_allow_html=True)

        with c_nom:
            nombre_est_input = st.text_input(
                "Nombre completo del estudiante",
                key="reg_nombre_est",
                placeholder="Ej.: Camila Rojas Pérez",
            )

        with c_car:
            carrera_sel = st.selectbox("Carrera", CARRERAS_OFICIALES, key="reg_carrera_sel")

    st.markdown("<div style='height:10px;'></div>", unsafe_allow_html=True)

    # PASO 2: ASIGNATURAS Y FECHAS DE INASISTENCIA (CON CONTROL ANTI-DUPLICADOS)
    with st.container(border=True):
        st.markdown(
            """
            <span class="ucn-solid-card"></span>
            <div class="ucn-step-header">
                <span class="ucn-step-num">2</span>
                <span class="ucn-step-title">Asignaturas y fechas de inasistencia</span>
                <span class="ucn-step-sub">Nivel (1° a 6°) → Asignatura · Paralelo libre</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

        s1, s2, s3 = st.columns([1.05, 1.75, 0.70], gap="medium")
        with s1:
            nivel_label = st.selectbox("Nivel (Semestre)", list(NIVELES_MAPA.keys()), key="reg_nivel_sel")
            nivel_num = NIVELES_MAPA[nivel_label]

        asig_filtradas = [
            a for a in asignaturas
            if a.get("carrera") == carrera_sel and int(a.get("semestre", 1)) == nivel_num
        ] or [a for a in asignaturas if a.get("carrera") == carrera_sel] or asignaturas

        mapa_asig = {a["nombre_asignatura"]: a for a in asig_filtradas}
        with s2:
            asig_label = st.selectbox("Asignatura del nivel", list(mapa_asig.keys()))

        with s3:
            paralelo_input = st.text_input("Paralelo", placeholder="Ej.: A, B, 1")

        st.markdown("<div style='height:4px;'></div>", unsafe_allow_html=True)

        d1, d2, d3 = st.columns([1.0, 1.0, 1.15], gap="medium", vertical_alignment="bottom")
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
            asig_obj = mapa_asig[asig_label]
            if f_termino < f_inicio:
                st.markdown('<div class="ucn-strip-err">Corrige las fechas antes de agregar el detalle.</div>', unsafe_allow_html=True)
            elif not par_limpio:
                st.markdown('<div class="ucn-strip-err">Escribe el paralelo antes de agregar (Ej.: A, B, 1).</div>', unsafe_allow_html=True)
            else:
                cruce_local = any(
                    d["id_asignatura"] == asig_obj["id_asignatura"]
                    and d["paralelo"] == par_limpio
                    and f_inicio <= d["fecha_termino"]
                    and f_termino >= d["fecha_inicio"]
                    for d in st.session_state.detalles_pendientes
                )
                msg_bd = (
                    verificar_duplicado_o_cruce(
                        df_all, normalizar_rut(rut_formateado), asig_obj["id_asignatura"], par_limpio, f_inicio, f_termino
                    )
                    if rut_valido
                    else None
                )
                if cruce_local:
                    st.markdown('<div class="ucn-strip-warn">Ya agregaste esa asignatura y paralelo en fechas coincidentes dentro de esta solicitud.</div>', unsafe_allow_html=True)
                elif msg_bd:
                    st.markdown(f'<div class="ucn-strip-err">Registro bloqueado: {esc(msg_bd)}</div>', unsafe_allow_html=True)
                else:
                    st.session_state.detalles_pendientes.append(
                        {
                            "id_asignatura": asig_obj["id_asignatura"],
                            "carrera": carrera_sel,
                            "nivel": nivel_num,
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
                f"<td>Nivel {esc(d['nivel'])}</td>"
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
                        <thead><tr><th>#</th><th>Carrera</th><th>Nivel</th><th>Asignatura</th><th>Paralelo</th><th>Desde</th><th>Hasta</th></tr></thead>
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
            <span class="ucn-solid-card"></span>
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
            periodo_sel = st.selectbox("Período", PERIODOS_DISPONIBLES)

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
        st.session_state.limpiar_form_registro = True
        st.session_state.pagina = "Inicio"
        st.rerun()

    if guardar_clic:
        detalles_a_guardar = list(st.session_state.detalles_pendientes)
        par_limpio = paralelo_input.strip().upper()
        if not detalles_a_guardar and f_termino >= f_inicio and par_limpio:
            asig_obj = mapa_asig[asig_label]
            detalles_a_guardar.append(
                {
                    "id_asignatura": asig_obj["id_asignatura"],
                    "carrera": carrera_sel,
                    "nivel": nivel_num,
                    "codigo_asignatura": asig_obj["codigo_asignatura"],
                    "nombre_asignatura": asig_obj["nombre_asignatura"],
                    "paralelo": par_limpio,
                    "fecha_inicio": f_inicio,
                    "fecha_termino": f_termino,
                }
            )

        errores = []
        if not rut_raw_val.strip() or not validar_rut_chileno(rut_formateado):
            errores.append("Ingresa un RUT válido (el dígito verificador no coincide).")
        if not nombre_est_input.strip():
            errores.append("Ingresa el nombre completo del estudiante.")
        if f_termino < f_inicio and not st.session_state.detalles_pendientes:
            errores.append("La fecha de término no puede ser anterior al inicio.")
        if not detalles_a_guardar:
            errores.append("Completa la asignatura e ingresa el paralelo (Ej.: A, B, 1).")
        if not tipo_doc.strip() or archivo_respaldo is None:
            errores.append("Completa el tipo de documento y adjunta un respaldo.")

        if not errores:
            rut_bd = normalizar_rut(rut_formateado)
            for det in detalles_a_guardar:
                msg_dup = verificar_duplicado_o_cruce(
                    df_all,
                    rut_bd,
                    det["id_asignatura"],
                    det["paralelo"],
                    det["fecha_inicio"],
                    det["fecha_termino"],
                )
                if msg_dup:
                    errores.append(msg_dup)

        if errores:
            for e_msg in errores:
                st.markdown(f'<div class="ucn-strip-err">{esc(e_msg)}</div>', unsafe_allow_html=True)
            return

        rut_bd = normalizar_rut(rut_formateado)
        est_previo = mapa_estudiantes.get(rut_bd)
        supabase.table("dim_estudiante").upsert(
            {
                "rut": rut_bd,
                "nombre_estudiante": nombre_est_input.strip(),
                "nombre_carrera": carrera_sel,
                "anio_ingreso": est_previo["anio_ingreso"] if est_previo else date.today().year,
                "estado_matricula": est_previo["estado_matricula"] if est_previo else "Alumno Regular",
            },
            on_conflict="rut",
        ).execute()

        id_fecha_ingreso = asegurar_fecha_en_dim_tiempo(fecha_entrega)
        num_solicitud = obtener_siguiente_numero_solicitud()
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
                    "rut_estudiante": rut_bd,
                    "id_asignatura": det["id_asignatura"],
                    "paralelo": det["paralelo"],
                    "estado": "En proceso",
                    "periodo": periodo_sel,
                    "id_funcionario": id_funcionario,
                    "dias_tramitacion": None,
                    "cantidad_documentos_adjuntos": 1,
                    "tipo_documento": tipo_doc.strip(),
                    "nombre_archivo": archivo_respaldo.name,
                    "observacion_revision": f"Solicitud recibida ({fecha_recepcion.strftime('%d/%m/%Y')}).",
                }
            )

        supabase.table("hechos_justificacion").insert(registros).execute()
        st.session_state.detalles_pendientes = []
        st.session_state.limpiar_form_registro = True
        st.session_state.ultima_solicitud_guardada = {
            "numero_solicitud": num_solicitud,
            "rut_visual": rut_formateado,
            "nombre_estudiante": nombre_est_input.strip(),
            "fecha_entrega": fecha_entrega,
            "nombre_archivo": archivo_respaldo.name,
            "detalles": detalles_a_guardar,
        }
        st.rerun()

# ==============================================================================
# PANTALLA 04: CONSULTAR SOLICITUDES / CONSULTAR Y REVISAR
# ==============================================================================
def render_consultar_revisar():
    es_jefatura = st.session_state.usuario["rol"] == "Jefatura de Carrera"

    df = cargar_hechos_detallados()
    total_sol = df["numero_solicitud"].nunique() if not df.empty else 0
    en_proc = df[df["estado"] == "En proceso"]["numero_solicitud"].nunique() if not df.empty else 0

    render_topbar("Inicio")
    render_banner(
        "Consultar y revisar" if es_jefatura else "Consultar solicitudes",
        "Revisa los antecedentes y registra una resolución."
        if es_jefatura
        else "Filtra por estudiante o estado de la solicitud.",
    )
    render_eciem_nav_pills(total_sol, en_proc)

    lista_estados = ["Todos"] + ESTADOS_OFICIALES

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
                q_rut_vis = formatear_rut_visual(rut_q).lower()
                df_fil = df_fil[
                    df_fil["rut_estudiante"].str.lower().str.contains(q_rut_vis, na=False)
                    | df_fil["rut_bd"].str.lower().str.contains(normalizar_rut(rut_q).lower(), na=False)
                    | df_fil["nombre_estudiante"].str.lower().str.contains(q_low, na=False)
                ]
            if est_q != "Todos":
                df_fil = df_fil[df_fil["estado"] == est_q]

        if df_fil.empty:
            with st.container(border=True):
                st.markdown(
                    """
                    <span class="ucn-solid-card"></span>
                    <div style="font-size:17px;font-weight:700;color:#1E293B;margin-bottom:4px;">Sin resultados</div>
                    <div style="font-size:13.5px;color:#475569;margin-bottom:12px;">
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
                f"<td><strong>{esc(r['nombre_estudiante'])}</strong><br><span style='font-size:12px;color:#64748B;'>{esc(r['rut_estudiante'])}</span></td>"
                f"<td>📅 {esc(f_ent)}</td>"
                f"<td>Nivel {esc(r['semestre'])} · {esc(r['nombre_asignatura'])}</td>"
                f"<td><strong>{esc(r['paralelo'])}</strong></td>"
                f"<td>{esc(rango)}</td>"
                f"<td>{badge_estado_html(r['estado'])}</td>"
                f"</tr>"
            )

        st.markdown(
            f"""
            <div class="ucn-table-wrap">
                <table class="ucn-table">
                    <thead>
                        <tr>
                            <th>Solicitud</th><th>Estudiante</th><th>Entrega</th>
                            <th>Asignatura</th><th>Paralelo</th><th>Inasistencia</th><th>Estado actual</th>
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
                q_rut_vis = formatear_rut_visual(rut_q).lower()
                df_fil = df_fil[
                    df_fil["rut_estudiante"].str.lower().str.contains(q_rut_vis, na=False)
                    | df_fil["rut_bd"].str.lower().str.contains(normalizar_rut(rut_q).lower(), na=False)
                    | df_fil["nombre_estudiante"].str.lower().str.contains(q_low, na=False)
                ]
            if est_q != "Todos":
                df_fil = df_fil[df_fil["estado"] == est_q]

        if df_fil.empty:
            with st.container(border=True):
                st.markdown(
                    '<span class="ucn-solid-card"></span>'
                    '<div style="font-size:16px;font-weight:700;color:#1E293B;">Sin resultados</div>'
                    '<div style="font-size:13px;color:#475569;margin:4px 0 10px 0;">No se encontraron coincidencias.</div>',
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
                Estado=("estado", "first"),
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
            f"<strong>Nivel {esc(r['semestre'])} · {esc(r['nombre_asignatura'])} (Par. {esc(r['paralelo'])})</strong> · "
            f"{esc(formatear_rango_inasistencia(r['fecha_inicio_ausencia'], r['fecha_termino_ausencia']))}"
            for _, r in filas_sol.iterrows()
        )
        f_ing_txt = primera["fecha_ingreso"].strftime("%d/%m/%Y") if primera["fecha_ingreso"] else "—"
        f_res_txt = primera["fecha_resolucion"].strftime("%d/%m/%Y") if primera["fecha_resolucion"] else f_ing_txt

        with st.container(border=True):
            st.markdown(
                f"""
                <span class="ucn-solid-card"></span>
                <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:8px;">
                    <div style="font-size:20px;font-weight:700;color:#003A70;">Solicitud #{esc(sol_sel)}</div>
                    <div>{badge_estado_html(primera['estado'])}</div>
                </div>
                <div style="font-size:14px;color:#1E293B;margin-bottom:8px;">
                    <strong>{esc(primera['nombre_estudiante'])}</strong> · {esc(primera['rut_estudiante'])}<br>
                    <span style="font-size:12.5px;color:#475569;">{esc(primera['nombre_carrera'])}</span>
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
                            "estado": accion,
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
                    <div style="font-size:12.5px;font-weight:700;color:#003A70;margin-bottom:4px;">
                        Historial de la solicitud #{esc(sol_sel)}
                    </div>
                    <div style="font-size:12px;color:#475569;line-height:1.45;">
                        <strong>{esc(f_res_txt)}</strong> · {esc(primera['nombre_funcionario'])} ({esc(primera['rol_funcionario'])}) ·
                        <strong>{esc(primera['estado'])}</strong><br>
                        {esc(primera['observacion_revision'] or 'Solicitud recibida.')}
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

# ==============================================================================
# PANTALLA 05: CARGAR PLANILLA (CON CONTROL ANTI-DUPLICADOS CONTRA BDD)
# ==============================================================================
def render_cargar_planilla():
    if st.session_state.usuario["rol"] != "Secretaría":
        st.session_state.pagina = "Inicio"
        st.rerun()

    df_all = cargar_hechos_detallados()
    total_sol = df_all["numero_solicitud"].nunique() if not df_all.empty else 0
    en_proc = df_all[df_all["estado"] == "En proceso"]["numero_solicitud"].nunique() if not df_all.empty else 0

    render_topbar("Inicio")

    if st.session_state.ultima_carga_confirmada is not None:
        res = st.session_state.ultima_carga_confirmada
        render_banner("Carga confirmada", "Resultado de la incorporación desde planilla.")
        render_eciem_nav_pills(total_sol, en_proc)
        st.markdown(
            f'<div class="ucn-strip-ok">{res["validas"]} registro(s) cargado(s). {res["errores"]} fila(s) omitida(s) por error o duplicado.</div>',
            unsafe_allow_html=True,
        )
        with st.container(border=True):
            st.markdown(
                f"""
                <span class="ucn-solid-card"></span>
                <div style="font-size:18px;font-weight:700;color:#003A70;margin-bottom:6px;">📄 {esc(res['archivo'])}</div>
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

    asignaturas, estudiantes = cargar_catalogos()

    with st.container(border=True):
        st.markdown('<span class="ucn-solid-card"></span>', unsafe_allow_html=True)
        c1, c2 = st.columns([2.2, 1.0], gap="large")
        with c1:
            archivo = st.file_uploader("Archivo de entrada (.csv o .xlsx)", type=["csv", "xlsx"])
        with c2:
            periodo_sel = st.selectbox("Período académico", PERIODOS_DISPONIBLES)

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
        st.markdown(f'<div class="ucn-strip-err">Faltan columnas obligatorias: {esc(", ".join(faltantes))}</div>', unsafe_allow_html=True)
        return

    if df_raw.empty:
        st.markdown('<div class="ucn-strip-warn">La planilla seleccionada solo contiene encabezados (0 filas de datos).</div>', unsafe_allow_html=True)
        return

    mapa_est = {normalizar_rut(e["rut"]): e for e in estudiantes}

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
            return "En proceso"
        t = str(texto_val).strip().lower()
        if t in ("aprobado", "aceptado", "si", "sí"):
            return "Aceptado"
        if t in ("rechazado", "no"):
            return "Rechazado"
        if t in ("en proceso", "pendiente"):
            return "En proceso"
        return None

    vista_previa = []
    filas_validas = []
    claves_vistas = set()

    for idx, row in df_raw.iterrows():
        fila_excel = idx + 2
        errores_fila = []

        rut_raw = "" if pd.isna(row["Rut"]) else str(row["Rut"]).strip()
        rut_norm = normalizar_rut(rut_raw)
        rut_vis = formatear_rut_visual(rut_raw) if rut_raw else ""
        nom_raw = "" if pd.isna(row["Nombre"]) else str(row["Nombre"]).strip()
        est_obj = mapa_est.get(rut_norm)

        if not rut_raw or not validar_rut_chileno(rut_raw):
            errores_fila.append("RUT inválido")
        if not nom_raw:
            errores_fila.append("Falta nombre del estudiante")

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

        estado_txt = mapear_estado(row["Validación JC"])
        if estado_txt is None:
            errores_fila.append(f"Estado '{row['Validación JC']}' no reconocido")
        if f_val is not None and f_entrega is not None and f_val < f_entrega:
            errores_fila.append("Fecha Validación anterior a Entrega")

        if not errores_fila:
            clave_u = (rut_norm, asig_obj["id_asignatura"], par_final, f_ini.isoformat(), f_ter.isoformat())
            if clave_u in claves_vistas:
                errores_fila.append("Duplicada dentro del archivo")
            else:
                msg_bd = verificar_duplicado_o_cruce(
                    df_all, rut_norm, asig_obj["id_asignatura"], par_final, f_ini, f_ter
                )
                if msg_bd:
                    errores_fila.append(msg_bd)
                else:
                    claves_vistas.add(clave_u)

        val_txt = "Válida" if not errores_fila else "Error: " + "; ".join(errores_fila)
        vista_previa.append(
            (fila_excel, rut_vis or rut_raw, nom_raw, asig_raw, par_final, row["Fecha inicio"], row["Fecha Termino"], val_txt)
        )
        if not errores_fila:
            filas_validas.append(
                {
                    "rut_estudiante": rut_norm,
                    "nombre_estudiante": nom_raw,
                    "carrera": asig_obj["carrera"],
                    "id_asignatura": asig_obj["id_asignatura"],
                    "paralelo": par_final,
                    "fecha_entrega": f_entrega,
                    "fecha_inicio": f_ini,
                    "fecha_termino": f_ter,
                    "estado": estado_txt,
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

        for item in filas_validas:
            est_prev = mapa_est.get(item["rut_estudiante"])
            if not est_prev:
                supabase.table("dim_estudiante").upsert(
                    {
                        "rut": item["rut_estudiante"],
                        "nombre_estudiante": item["nombre_estudiante"],
                        "nombre_carrera": item["carrera"],
                        "anio_ingreso": date.today().year,
                        "estado_matricula": "Alumno Regular",
                    },
                    on_conflict="rut",
                ).execute()
                mapa_est[item["rut_estudiante"]] = {"rut": item["rut_estudiante"]}

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
                    "id_asignatura": item["id_asignatura"],
                    "paralelo": item["paralelo"],
                    "estado": item["estado"],
                    "periodo": periodo_sel,
                    "id_funcionario": id_func,
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
# PANTALLA 06: GENERAR REPORTE (EXCEL FORMATEADO .XLSX + .CSV)
# ==============================================================================
def render_generar_reporte():
    df = cargar_hechos_detallados()
    total_sol = df["numero_solicitud"].nunique() if not df.empty else 0
    en_proc = df[df["estado"] == "En proceso"]["numero_solicitud"].nunique() if not df.empty else 0

    render_topbar("Volver")

    carreras_opc = ["Todas"] + CARRERAS_OFICIALES
    filtros_guardados = st.session_state.rep_filtros
    idx_per = PERIODOS_DISPONIBLES.index(filtros_guardados["periodo"]) if filtros_guardados["periodo"] in PERIODOS_DISPONIBLES else 0
    idx_car = carreras_opc.index(filtros_guardados.get("carrera", "Todas")) if filtros_guardados.get("carrera", "Todas") in carreras_opc else 0
    idx_est = ESTADOS_OFICIALES.index(filtros_guardados["estado"]) if filtros_guardados["estado"] in ESTADOS_OFICIALES else 1

    if not st.session_state.reporte_listo:
        render_banner("Generar reporte", "Inasistencias justificadas del período seleccionado.")
        render_eciem_nav_pills(total_sol, en_proc)
        c1, c2, c3 = st.columns(3, gap="medium")
        with c1:
            periodo_sel = st.selectbox("Período académico", PERIODOS_DISPONIBLES, index=idx_per)
        with c2:
            carrera_sel = st.selectbox("Carrera", carreras_opc, index=idx_car)
        with c3:
            estado_sel = st.selectbox("Estado actual", ESTADOS_OFICIALES, index=idx_est)
        st.markdown("<div style='height:8px;'></div>", unsafe_allow_html=True)
    else:
        periodo_sel = filtros_guardados["periodo"]
        carrera_sel = filtros_guardados.get("carrera", "Todas")
        estado_sel = filtros_guardados["estado"]
        render_banner("Reporte listo", "Inasistencias justificadas del período seleccionado.")
        render_eciem_nav_pills(total_sol, en_proc)
        st.markdown(
            f'<div class="ucn-strip-ok">📊 inasistencias_{esc(periodo_sel)}.xlsx · Listo para descargar</div>',
            unsafe_allow_html=True,
        )

    if df.empty:
        st.markdown('<div class="ucn-strip-info">No hay registros disponibles para generar reportes.</div>', unsafe_allow_html=True)
        return

    df_rep = df[(df["periodo"] == periodo_sel) & (df["estado"] == estado_sel)].copy()
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
            f"<td>{esc(r['rut_estudiante'])}</td>"
            f"<td>{esc(r['nombre_asignatura'])}</td>"
            f"<td><strong>{esc(r['paralelo'])}</strong></td>"
            f"<td>{esc(r['fecha_inicio_ausencia'].strftime('%d/%m/%Y'))}</td>"
            f"<td>{esc(r['fecha_termino_ausencia'].strftime('%d/%m/%Y'))}</td>"
            f"<td>{esc(r['dias_ausencia'])}</td>"
            f"<td>{badge_estado_html(r['estado'])}</td>"
            f"</tr>"
        )

    st.markdown(
        f"""
        <div class="ucn-table-wrap">
            <table class="ucn-table">
                <thead>
                    <tr>
                        <th>Solicitud</th><th>Estudiante</th><th>RUT</th><th>Asignatura</th><th>Paralelo</th>
                        <th>Desde</th><th>Hasta</th><th>Días</th><th>Estado</th>
                    </tr>
                </thead>
                <tbody>{''.join(filas_html)}</tbody>
            </table>
        </div>
        <div class="ucn-summary-bar">
            <span>{len(df_rep)} detalles</span>
            <span>{df_rep['numero_solicitud'].nunique()} solicitudes</span>
            <span>{df_rep['rut_bd'].nunique()} estudiantes</span>
            <span>{int(df_rep['dias_ausencia'].sum())} días totales</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    df_export = pd.DataFrame(
        {
            "Solicitud": df_rep["numero_solicitud"],
            "Estudiante": df_rep["nombre_estudiante"],
            "RUT": df_rep["rut_estudiante"],
            "Carrera": df_rep["carrera_asignatura"],
            "Asignatura": df_rep["nombre_asignatura"],
            "Paralelo": df_rep["paralelo"],
            "Desde": df_rep["fecha_inicio_ausencia"].apply(lambda d: d.strftime("%d/%m/%Y")),
            "Hasta": df_rep["fecha_termino_ausencia"].apply(lambda d: d.strftime("%d/%m/%Y")),
            "Días": df_rep["dias_ausencia"],
            "Estado": df_rep["estado"],
        }
    )

    xlsx_bytes = generar_excel_institucional(
        df_export,
        f"REPORTE DE INASISTENCIAS · ECIEM UCN (PERÍODO {periodo_sel})",
        f"Carrera: {carrera_sel}   |   Estado: {estado_sel}   |   Generado el {date.today().strftime('%d/%m/%Y')}",
    )
    csv_bytes = df_export.to_csv(index=False, sep=";").encode("utf-8-sig")

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
        b1, b2, b3, _ = st.columns([2.5, 1.9, 1.9, 3.7], gap="small")
        b1.download_button(
            label="📥 Descargar Excel (.xlsx)",
            data=xlsx_bytes,
            file_name=f"inasistencias_{periodo_sel}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            type="primary",
            use_container_width=True,
        )
        b2.download_button(
            label="Descargar .csv",
            data=csv_bytes,
            file_name=f"inasistencias_{periodo_sel}.csv",
            mime="text/csv",
            type="secondary",
            use_container_width=True,
        )
        if b3.button("Cambiar filtros", type="secondary", use_container_width=True):
            st.session_state.reporte_listo = False
            st.rerun()

# ==============================================================================
# ENRUTADOR PRINCIPAL
# ==============================================================================
if st.session_state.usuario is None:
    render_login()
elif st.session_state.usuario["rol"] == "Docente":
    render_portal_docente()
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
