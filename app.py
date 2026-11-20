import re
from datetime import date, datetime
import pandas as pd
import streamlit as st
from supabase import create_client, Client

st.set_page_config(
    page_title="Gestión de Inasistencias - ECIEM UCN",
    page_icon="🎓",
    layout="wide",
)

@st.cache_resource
def get_supabase_client() -> Client:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

supabase: Client = get_supabase_client()


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
    """Garantiza que la fecha exista en dim_tiempo y retorna id_fecha (YYYYMMDD)."""
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
    """Trae hechos_justificacion enriquecidos con sus dimensiones."""
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

if "usuario" not in st.session_state:
    st.session_state.usuario = None
if "pagina" not in st.session_state:
    st.session_state.pagina = "Inicio"
if "detalles_pendientes" not in st.session_state:
    st.session_state.detalles_pendientes = []

def render_login():
    st.markdown("### Universidad Católica del Norte — ECIEM")
    st.title("Gestión de Inasistencias")
    st.caption("Recepción, revisión y seguimiento de solicitudes · Campus Guayacán")

    col1, _ = st.columns([1.2, 1])
    with col1:
        with st.form("form_login"):
            st.subheader("Iniciar sesión")
            perfil_ui = st.radio(
                "Selecciona tu perfil para continuar",
                options=["Secretaría", "Jefatura de Carrera"],
                horizontal=True,
            )
            correo = st.text_input(
                "01. Correo institucional",
                placeholder="Ej.: secretaria.iicg@ucn.cl",
            )
            contrasena = st.text_input(
                "02. Contraseña",
                type="password",
                help="Tu contraseña se muestra oculta.",
            )
            submit = st.form_submit_button("Ingresar", use_container_width=True)

            if submit:
                if not correo.strip() or not validar_email(correo):
                    st.error("Ingresa un correo válido.")
                    return

                res = (
                    supabase.table("dim_funcionario")
                    .select("id_funcionario, nombre_funcionario, rol, email, contrasena")
                    .eq("email", correo.strip().lower())
                    .eq("rol", perfil_ui)
                    .execute()
                )
                if not res.data or res.data[0]["contrasena"] != contrasena:
                    st.error("Usuario o contraseña incorrectos.")
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

def render_sidebar():
    user = st.session_state.usuario
    es_secretaria = user["rol"] == "Secretaría"

    with st.sidebar:
        st.markdown("### UCN · ECIEM")
        st.info(f"**{user['nombre_funcionario']}**\n\nPerfil: `{user['rol']}`")

        if es_secretaria:
            opciones = [
                "Inicio",
                "Registrar solicitud",
                "Consultar solicitudes",
                "Cargar planilla",
                "Generar reporte",
            ]
        else:
            opciones = [
                "Inicio",
                "Consultar y revisar",
                "Generar reporte",
            ]

        if st.session_state.pagina not in opciones:
            st.session_state.pagina = "Inicio"

        seleccion = st.radio("Navegación", opciones, index=opciones.index(st.session_state.pagina))
        st.session_state.pagina = seleccion

        st.divider()
        if st.button("Cerrar sesión", use_container_width=True):
            st.session_state.usuario = None
            st.session_state.detalles_pendientes = []
            st.session_state.pagina = "Inicio"
            st.rerun()


def render_inicio():
    user = st.session_state.usuario
    es_secretaria = user["rol"] == "Secretaría"

    st.title("Inicio")
    st.caption(
        "Recibe solicitudes y organiza los antecedentes."
        if es_secretaria
        else "Consulta antecedentes y registra una decisión."
    )

    df = cargar_hechos_detallados()
    total_solicitudes = df["numero_solicitud"].nunique() if not df.empty else 0
    en_proceso = (
        df[df["nombre_estado"] == "En proceso"]["numero_solicitud"].nunique()
        if not df.empty
        else 0
    )
    aceptadas = (
        df[df["nombre_estado"] == "Aceptado"]["numero_solicitud"].nunique()
        if not df.empty
        else 0
    )

    c1, c2, c3 = st.columns(3)
    c1.metric("Solicitudes registradas", total_solicitudes)
    c2.metric("En proceso", en_proceso)
    c3.metric("Aceptadas", aceptadas)

    st.subheader("Solicitudes recientes")
    if df.empty:
        st.info("Aún no existen solicitudes registradas en Supabase.")
        return

    resumen = (
        df.groupby("numero_solicitud", as_index=False)
        .agg(
            Estudiante=("nombre_estudiante", "first"),
            Entrega=("fecha_ingreso", "first"),
            Estado=("nombre_estado", "first"),
            Paralelos=("codigo_asignatura", lambda s: ", ".join(s)),
            Respaldo=("nombre_archivo", "first"),
        )
        .sort_values("numero_solicitud", ascending=False)
        .rename(columns={"numero_solicitud": "Solicitud"})
    )
    resumen["Entrega"] = resumen["Entrega"].apply(lambda d: d.strftime("%d/%m/%Y") if d else "")
    st.dataframe(resumen, use_container_width=True, hide_index=True)


def render_registrar_solicitud():
    if st.session_state.usuario["rol"] != "Secretaría":
        st.error("Acceso restringido: solo Secretaría puede registrar solicitudes.")
        return

    st.title("Registrar solicitud")
    st.caption("Una solicitud puede incluir varios paralelos y períodos de inasistencia.")

    estados, periodos, asignaturas, estudiantes = cargar_catalogos()
    mapa_estudiantes = {normalizar_rut(e["rut"]): e for e in estudiantes}
    estado_en_proceso = next((e["id_estado"] for e in estados if e["nombre_estado"] == "En proceso"), None)

    if not periodos or not asignaturas or estado_en_proceso is None:
        st.warning("Faltan datos maestros en Supabase (dim_periodo, dim_asignatura o dim_estado 'En proceso').")
        return

    col_izq, col_der = st.columns(2)

    with col_izq:
        rut_input = st.text_input("01. RUT del estudiante", placeholder="Ej.: 12.345.678-5")
        estudiante_actual = None
        if rut_input.strip():
            if not validar_rut_chileno(rut_input):
                st.error("El RUT no es válido. Revisa el dígito verificador.")
            else:
                rut_norm = normalizar_rut(rut_input)
                estudiante_actual = mapa_estudiantes.get(rut_norm)
                if estudiante_actual:
                    st.success(
                        f"**{estudiante_actual['nombre_estudiante']}** · "
                        f"{estudiante_actual['nombre_carrera']} "
                        f"(Ingreso {estudiante_actual['anio_ingreso']} · {estudiante_actual['estado_matricula']})"
                    )
                else:
                    st.error("Estudiante no registrado en dim_estudiante.")

        fecha_entrega = st.date_input("02. Fecha de entrega", value=date.today(), format="DD/MM/YYYY")
        periodo_opciones = {p["nombre_periodo"]: p["id_periodo"] for p in periodos}
        periodo_sel = st.selectbox("Período académico", list(periodo_opciones.keys()))

    with col_der:
        tipo_doc = st.text_input("07. Tipo de documento", placeholder="Ej.: Certificado")
        archivo_respaldo = st.file_uploader(
            "08. Respaldo recibido (PDF o imagen)",
            type=["pdf", "png", "jpg", "jpeg"],
            help="La revisión formal del respaldo la realiza Secretaría.",
        )

    st.divider()
    st.subheader("Detalle de paralelos e inasistencias")

    mapa_asig = {
        f"{a['codigo_asignatura']} — {a['nombre_asignatura']} ({a['nombre_docente']})": a
        for a in asignaturas
    }

    with st.form("form_agregar_detalle"):
        d1, d2, d3 = st.columns([2, 1, 1])
        asig_label = d1.selectbox("03. Paralelo", list(mapa_asig.keys()))
        f_inicio = d2.date_input("04. Fecha de inicio", value=date.today(), format="DD/MM/YYYY")
        f_termino = d3.date_input("05. Fecha de término", value=date.today(), format="DD/MM/YYYY")
        btn_add = st.form_submit_button("+ Agregar inasistencia")

        if btn_add:
            if f_termino < f_inicio:
                st.error("La fecha de término no puede ser anterior al inicio.")
            else:
                asig_obj = mapa_asig[asig_label]
                if any(d["id_paralelo"] == asig_obj["id_paralelo"] for d in st.session_state.detalles_pendientes):
                    st.warning("Ese paralelo ya fue agregado a esta solicitud.")
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
        df_det = pd.DataFrame(st.session_state.detalles_pendientes)
        df_det_show = df_det[["codigo_asignatura", "nombre_asignatura", "fecha_inicio", "fecha_termino"]].copy()
        df_det_show.columns = ["Paralelo", "Asignatura", "Desde", "Hasta"]
        st.dataframe(df_det_show, use_container_width=True, hide_index=True)

        if st.button("Limpiar paralelos agregados"):
            st.session_state.detalles_pendientes = []
            st.rerun()

    st.divider()
    b1, _ = st.columns([1, 3])
    if b1.button("Guardar solicitud", type="primary", use_container_width=True):
        errores = []
        if not rut_input.strip() or not validar_rut_chileno(rut_input):
            errores.append("El RUT no es válido. Revisa el dígito verificador.")
        elif estudiante_actual is None:
            errores.append("Estudiante no registrado.")
        if not st.session_state.detalles_pendientes:
            errores.append("Selecciona un paralelo válido y agrégalo al detalle.")
        if not tipo_doc.strip() or archivo_respaldo is None:
            errores.append("Completa el tipo / Selecciona un respaldo.")

        if errores:
            for err in errores:
                st.error(err)
            return

        id_fecha_ingreso = asegurar_fecha_en_dim_tiempo(fecha_entrega)
        num_solicitud = obtener_siguiente_numero_solicitud()
        id_periodo = periodo_opciones[periodo_sel]
        id_funcionario = st.session_state.usuario["id_funcionario"]

        registros = []
        for det in st.session_state.detalles_pendientes:
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
                    "observacion_revision": "Solicitud recibida por Secretaría.",
                }
            )

        supabase.table("hechos_justificacion").insert(registros).execute()
        st.session_state.detalles_pendientes = []
        st.success(f"Solicitud {num_solicitud} registrada correctamente ({len(registros)} paralelo(s)).")

# ==============================================================================
# PANTALLA 04: CONSULTAR Y REVISAR (SECRETARÍA SOLO LECTURA / JEFATURA DECIDE)
# ==============================================================================
def render_consultar_revisar():
    es_jefatura = st.session_state.usuario["rol"] != "Secretaría"

    st.title("Consultar y revisar" if es_jefatura else "Consultar solicitudes")
    st.caption(
        "Revisa el respaldo y deja registro de la decisión."
        if es_jefatura
        else "Busca por estudiante o estado actual. La revisión y la decisión corresponden a Jefatura."
    )

    df = cargar_hechos_detallados()
    estados, _, _, _ = cargar_catalogos()
    mapa_estados = {e["nombre_estado"]: e["id_estado"] for e in estados}

    f1, f2 = st.columns([2, 1])
    filtro_rut = f1.text_input("RUT / estudiante", placeholder="Ej.: 12.345.678-5 o nombre")
    filtro_estado = f2.selectbox("Estado actual", ["Todos"] + list(mapa_estados.keys()))

    if df.empty:
        st.info("No existen solicitudes registradas.")
        return

    df_filtrado = df.copy()
    if filtro_rut.strip():
        q = filtro_rut.strip().lower()
        q_rut = normalizar_rut(filtro_rut).lower()
        df_filtrado = df_filtrado[
            df_filtrado["rut_estudiante"].str.lower().str.contains(q_rut, na=False)
            | df_filtrado["nombre_estudiante"].str.lower().str.contains(q, na=False)
        ]
    if filtro_estado != "Todos":
        df_filtrado = df_filtrado[df_filtrado["nombre_estado"] == filtro_estado]

    if df_filtrado.empty:
        st.warning("No se encontraron coincidencias con los filtros aplicados.")
        return

    tabla_vista = df_filtrado[
        [
            "numero_solicitud",
            "nombre_estudiante",
            "rut_estudiante",
            "fecha_ingreso",
            "codigo_asignatura",
            "fecha_inicio_ausencia",
            "fecha_termino_ausencia",
            "nombre_estado",
            "nombre_archivo",
        ]
    ].copy()
    tabla_vista.columns = [
        "Solicitud",
        "Estudiante",
        "RUT",
        "Entrega",
        "Paralelo",
        "Desde",
        "Hasta",
        "Estado",
        "Respaldo",
    ]
    st.dataframe(tabla_vista, use_container_width=True, hide_index=True)

    if es_jefatura:
        st.divider()
        st.subheader("Panel de resolución (Jefatura)")
        solicitudes_unicas = sorted(df_filtrado["numero_solicitud"].unique().tolist(), reverse=True)
        sol_sel = st.selectbox("Selecciona el N° de solicitud a revisar", solicitudes_unicas)

        filas_sol = df[df["numero_solicitud"] == sol_sel]
        primera = filas_sol.iloc[0]

        st.markdown(
            f"**Solicitud {sol_sel}** · Estado actual: `{primera['nombre_estado']}`  \n"
            f"Estudiante: **{primera['nombre_estudiante']}** ({primera['rut_estudiante']})  \n"
            f"Respaldo: `{primera['nombre_archivo'] or 'Sin nombre registrado'}` "
            f"({primera['tipo_documento'] or 'Documento'}) · "
            f"Observación vigente: *{primera['observacion_revision'] or 'Sin observaciones'}*"
        )

        observacion = st.text_area(
            "09. Observación de la revisión",
            value=primera["observacion_revision"],
            placeholder="Deja un motivo al rechazar o solicitar antecedentes.",
        )

        b_ac, b_re, b_an = st.columns(3)
        accion = None
        if b_ac.button("Aceptar", type="primary", use_container_width=True):
            accion = "Aceptado"
        elif b_re.button("Rechazar", use_container_width=True):
            accion = "Rechazado"
        elif b_an.button("Solicitar antecedentes", use_container_width=True):
            accion = "En proceso"

        if accion:
            if accion in ("Rechazado", "En proceso") and not observacion.strip():
                st.error("Describe el motivo de la decisión.")
                return

            id_nuevo_estado = mapa_estados[accion]
            hoy = date.today()
            id_fecha_res = None
            dias_tram = None

            if accion in ("Aceptado", "Rechazado"):
                id_fecha_res = asegurar_fecha_en_dim_tiempo(hoy)
                f_ing = primera["fecha_ingreso"]
                dias_tram = max(0, (hoy - f_ing).days) if f_ing else 0

            supabase.table("hechos_justificacion").update(
                {
                    "id_estado": id_nuevo_estado,
                    "id_funcionario": st.session_state.usuario["id_funcionario"],
                    "id_fecha_resolucion": id_fecha_res,
                    "dias_tramitacion": dias_tram,
                    "observacion_revision": observacion.strip() or "Solicitud aceptada por Jefatura.",
                }
            ).eq("numero_solicitud", int(sol_sel)).execute()

            st.success(f"Solicitud {sol_sel} actualizada a estado '{accion}'.")
            st.rerun()


def render_cargar_planilla():
    if st.session_state.usuario["rol"] != "Secretaría":
        st.error("Acceso restringido: solo Secretaría puede realizar cargas masivas.")
        return

    st.title("Cargar planilla")
    st.caption("Carga masiva desde la planilla histórica/operativa (Entrada Ejemplo - Hoja 1.csv).")
    st.info(
        "Política de datos (Criterios 3 y 6): las columnas **Mail** y **Diagnostico** "
        "se omiten automáticamente al migrar a Supabase para evitar redundancia y resguardar la privacidad médica."
    )

    estados, periodos, asignaturas, estudiantes = cargar_catalogos()
    periodo_opciones = {p["nombre_periodo"]: p["id_periodo"] for p in periodos}
    periodo_sel = st.selectbox("Período académico para esta carga", list(periodo_opciones.keys()))
    id_periodo_sel = periodo_opciones[periodo_sel]

    archivo = st.file_uploader("Selecciona archivo CSV o Excel (.csv, .xlsx)", type=["csv", "xlsx"])
    if not archivo:
        return

    try:
        df_raw = pd.read_csv(archivo) if archivo.name.endswith(".csv") else pd.read_excel(archivo)
    except Exception as exc:
        st.error(f"No se pudo leer el archivo: {exc}")
        return

    # Limpia espacios accidentales en encabezados (ej. 'Rut ' y ' Fecha Entrega')
    df_raw.columns = [str(c).strip() for c in df_raw.columns]

    columnas_requeridas = [
        "Rut",
        "Nombre",
        "Asignatura",
        "Docente",
        "Fecha Entrega",
        "Fecha inicio",
        "Fecha Termino",
        "Validación JC",
        "Fecha Validación",
    ]
    faltantes = [c for c in columnas_requeridas if c not in df_raw.columns]
    if faltantes:
        st.error(f"Faltan columnas obligatorias en la planilla: {', '.join(faltantes)}")
        return

    if df_raw.empty:
        st.warning("La planilla no contiene filas de datos (solo encabezados).")
        return

    mapa_est = {normalizar_rut(e["rut"]): e for e in estudiantes}
    mapa_estados = {e["nombre_estado"].lower(): e["id_estado"] for e in estados}

    def buscar_paralelo(asig_txt: str, doc_txt: str):
        a_clean = str(asig_txt).strip().lower()
        d_clean = str(doc_txt).strip().lower()
        for a in asignaturas:
            coincide_asig = (
                a["codigo_asignatura"].strip().lower() == a_clean
                or a["nombre_asignatura"].strip().lower() == a_clean
            )
            if coincide_asig:
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
    filas_validas_preparadas = []
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
            errores_fila.append(f"Asignatura/Docente '{asig_raw} / {doc_raw}' no existe en dim_asignatura")

        f_entrega = parsear_fecha_flexible(row["Fecha Entrega"])
        f_ini = parsear_fecha_flexible(row["Fecha inicio"])
        f_ter = parsear_fecha_flexible(row["Fecha Termino"])
        f_val = parsear_fecha_flexible(row["Fecha Validación"])

        if f_entrega is None:
            errores_fila.append("Fecha Entrega inválida")
        if f_ini is None or f_ter is None:
            errores_fila.append("Fecha inicio o Fecha Termino inválida")
        elif f_ter < f_ini:
            errores_fila.append("Fecha Termino anterior a Fecha inicio")

        id_estado = mapear_estado(row["Validación JC"])
        if id_estado is None:
            errores_fila.append(f"Validación JC '{row['Validación JC']}' no reconocida")

        if f_val is not None and f_entrega is not None and f_val < f_entrega:
            errores_fila.append("Fecha Validación anterior a Fecha Entrega")

        if not errores_fila:
            clave_unica = (est_obj["rut"], f_entrega.isoformat(), asig_obj["id_paralelo"])
            if clave_unica in claves_vistas:
                errores_fila.append("Registro duplicado en el archivo (mismo RUT, fecha de entrega y paralelo)")
            else:
                claves_vistas.add(clave_unica)

        estado_validacion = "Válida" if not errores_fila else "Error: " + "; ".join(errores_fila)
        vista_previa.append(
            {
                "Fila": fila_excel,
                "Rut": rut_raw,
                "Nombre": row["Nombre"],
                "Asignatura": asig_raw,
                "Docente": doc_raw,
                "Fecha Entrega": row["Fecha Entrega"],
                "Fecha inicio": row["Fecha inicio"],
                "Fecha Termino": row["Fecha Termino"],
                "Validación JC": row["Validación JC"],
                "Validación": estado_validacion,
            }
        )

        if not errores_fila:
            filas_validas_preparadas.append(
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

    df_prev = pd.DataFrame(vista_previa)
    st.subheader("Vista previa de validación")
    st.dataframe(df_prev, use_container_width=True, hide_index=True)

    n_validas = len(filas_validas_preparadas)
    n_err = len(df_prev) - n_validas
    st.write(f"**Resumen:** {n_validas} fila(s) válida(s) · {n_err} fila(s) con error.")

    if n_validas > 0 and st.button(f"Cargar {n_validas} fila(s) válida(s) en Supabase", type="primary"):
        siguiente_num = obtener_siguiente_numero_solicitud()
        mapa_solicitud_por_grupo = {}
        registros_insert = []
        id_func = st.session_state.usuario["id_funcionario"]

        for item in filas_validas_preparadas:
            clave_grupo = (item["rut_estudiante"], item["fecha_entrega"].isoformat())
            if clave_grupo not in mapa_solicitud_por_grupo:
                mapa_solicitud_por_grupo[clave_grupo] = siguiente_num
                siguiente_num += 1
            num_sol = mapa_solicitud_por_grupo[clave_grupo]

            id_f_ing = asegurar_fecha_en_dim_tiempo(item["fecha_entrega"])
            id_f_res = (
                asegurar_fecha_en_dim_tiempo(item["fecha_validacion"])
                if item["fecha_validacion"]
                else None
            )
            dias_tram = (
                max(0, (item["fecha_validacion"] - item["fecha_entrega"]).days)
                if item["fecha_validacion"]
                else None
            )

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
                    "observacion_revision": "Importado desde planilla histórica.",
                }
            )

        supabase.table("hechos_justificacion").insert(registros_insert).execute()
        st.success(f"Carga confirmada: {n_validas} registro(s) incorporado(s). {n_err} fila(s) omitida(s).")


def render_generar_reporte():
    st.title("Generar reporte")
    st.caption("Inasistencias aceptadas del período seleccionado (formato oficial para notificación docente).")

    df = cargar_hechos_detallados()
    estados, periodos, asignaturas, _ = cargar_catalogos()

    c1, c2, c3 = st.columns(3)
    nombres_periodos = [p["nombre_periodo"] for p in periodos]
    periodo_sel = c1.selectbox("Período académico", nombres_periodos)
    paralelos_opc = ["Todos"] + [a["codigo_asignatura"] for a in asignaturas]
    paralelo_sel = c2.selectbox("Paralelo", paralelos_opc)
    estados_opc = [e["nombre_estado"] for e in estados]
    idx_aceptado = estados_opc.index("Aceptado") if "Aceptado" in estados_opc else 0
    estado_sel = c3.selectbox("Estado actual", estados_opc, index=idx_aceptado)

    if df.empty:
        st.info("No hay registros disponibles para generar reportes.")
        return

    df_rep = df[
        (df["nombre_periodo"] == periodo_sel) & (df["nombre_estado"] == estado_sel)
    ].copy()
    if paralelo_sel != "Todos":
        df_rep = df_rep[df_rep["codigo_asignatura"] == paralelo_sel]

    if df_rep.empty:
        st.warning("No existen registros para los filtros seleccionados.")
        return

    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Detalles", len(df_rep))
    k2.metric("Solicitudes", df_rep["numero_solicitud"].nunique())
    k3.metric("Estudiantes", df_rep["rut_estudiante"].nunique())
    k4.metric("Días por detalle", int(df_rep["dias_ausencia"].sum()))

    df_csv = pd.DataFrame(
        {
            "Solicitud": df_rep["numero_solicitud"],
            "Estudiante": df_rep["nombre_estudiante"],
            "Paralelo": df_rep["codigo_asignatura"],
            "Desde": df_rep["fecha_inicio_ausencia"].apply(lambda d: d.strftime("%d/%m/%Y")),
            "Hasta": df_rep["fecha_termino_ausencia"].apply(lambda d: d.strftime("%d/%m/%Y")),
        }
    ).sort_values(["Solicitud", "Paralelo"])

    st.dataframe(df_csv, use_container_width=True, hide_index=True)
    st.caption(
        "Reporte filtrado sin diagnóstico médico ni archivo adjunto, apto para notificación a docentes."
    )

    csv_bytes = df_csv.to_csv(index=False).encode("utf-8-sig")
    st.download_button(
        label="Descargar .csv (Salida Ejemplo - Reporte.csv)",
        data=csv_bytes,
        file_name=f"inasistencias_{periodo_sel}.csv",
        mime="text/csv",
        type="primary",
    )

if st.session_state.usuario is None:
    render_login()
else:
    render_sidebar()
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
