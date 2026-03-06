# -*- coding: utf-8 -*-
# FRUTAS WC - App de pedidos con PDF + estados + envío por email
# Autoría: personalizada para Luciana - División Logística
# Requisitos: streamlit, reportlab
# -------------------------------------------------------------
# SMTP: configurar en .streamlit/secrets.toml (ver README arriba)

import streamlit as st
import pandas as pd
import re, uuid, smtplib
from email.message import EmailMessage
from datetime import datetime, timedelta, time
from io import BytesIO

from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm

# =========================
# 0) CONFIG INICIAL & CSS
# =========================
st.set_page_config(page_title="FRUTAS WC", layout="wide", initial_sidebar_state="collapsed")

CUSTOM_CSS = """
<style>
[data-testid="stSidebar"] {display: none;}
.stApp {
    background-size: cover;
    background-position: center bottom;
    background-attachment: fixed;
}
.main .block-container {
    background-color: rgba(255, 255, 255, 0.96);
    border-radius: 15px; padding: 30px; max-width: 980px;
}
.wa-float {
    position: fixed; bottom: 20px; right: 20px;
    background-color: #25d366; color: white; border-radius: 50px;
    padding: 12px 20px; display: flex; align-items: center; gap: 10px;
    text-decoration: none; z-index: 100; font-weight: bold;
}
.stButton>button { border-radius: 8px; }
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# =========================
# 1) STATE & HELPERS
# =========================
def init_state():
    if "nav" not in st.session_state: st.session_state.nav = "Inicio"
    if "rol" not in st.session_state: st.session_state.rol = "Cliente"
    if "lista" not in st.session_state: st.session_state.lista = []
    if "ultimo_pedido" not in st.session_state: st.session_state.ultimo_pedido = None
    if "pedidos" not in st.session_state: st.session_state.pedidos = {}  # id -> pedido

    # Catálogo en el orden de tu plantilla (dos columnas fijas del PDF)
    if "catalogo_left" not in st.session_state:
        st.session_state.catalogo_left = [
            "Acelga","Achicoria","Ajo","Alcaucil","Ananá","Apio","Arándanos","Banana","Batata","Berenjena",
            "Brócoli","Calabacín","Calabaza","Cebolla","Cerezas","Champiñón","Chaucha","Choclo","Ciruela","Coliflor",
            "Durazno","Espárragos","Espinaca","Frutilla","Kiwi","Lechuga","Lechuguin","Limón","Mandarina","Manzana",
            "Manzana (V)","Melón"
        ]
    if "catalogo_right" not in st.session_state:
        st.session_state.catalogo_right = [
            "Naranja","Naranja (O)","Palta","Papa","Papa (Bolsa)","Pepino","Pera","Pimiento","Pomelo","Puerro",
            "Remolacha","Repollo","Rúcula","Sandia","Tomate (Cherry)","Tomate (P)","Tomate (R)","Uva","Verdeo","Zanahoria",
            "Zapallito","Zapallo","Zapallo (N)","Zuchini","Oliva","Miel","Huevos","Carbón","Perejil","Bandejas"
        ]
    if "productos_todos" not in st.session_state:
        st.session_state.productos_todos = st.session_state.catalogo_left + st.session_state.catalogo_right

def normalizar_texto(s: str) -> str:
    return (s or "").strip().upper()

def new_order_id() -> str:
    return uuid.uuid4().hex[:8].upper()

EMAIL_REGEX = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
def es_email_valido(email: str) -> bool:
    if not email: return False
    return bool(EMAIL_REGEX.match(email.strip()))

def agregar_item(descripcion: str, cant: float, kg: float, tipo: str):
    """Agrega o acumula un item por Descripción+Tipo."""
    if not descripcion: return
    if (cant or 0) <= 0 and (kg or 0.0) <= 0: return

    descripcion = normalizar_texto(descripcion)
    tipo = normalizar_texto(tipo)

    # acumular si ya existe
    for row in st.session_state.lista:
        if row["Descripción"] == descripcion and row["Tipo"] == tipo:
            row["Cant."] = int(row.get("Cant.", 0)) + int(cant or 0)
            row["Kg."] = float(row.get("Kg.", 0.0)) + float(kg or 0.0)
            return

    st.session_state.lista.append({
        "Descripción": descripcion,
        "Cant.": int(cant or 0),
        "Kg.": float(kg or 0.0),
        "Tipo": tipo
    })

def totals(df: pd.DataFrame):
    if df.empty: return 0, 0.0
    return int(df["Cant."].sum()), float(df["Kg."].sum())

def enviar_email_pdf(destinatario: str, asunto: str, cuerpo_txt: str, nombre_pdf: str, pdf_bytes: bytes) -> tuple[bool, str]:
    """
    Envía email con PDF adjunto usando SMTP definido en st.secrets.
    secrets.toml:
      SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASS, SMTP_FROM
    """
    try:
        host = st.secrets.get("SMTP_HOST", "")
        port = int(st.secrets.get("SMTP_PORT", 587))
        user = st.secrets.get("SMTP_USER", "")
        password = st.secrets.get("SMTP_PASS", "")
        sender = st.secrets.get("SMTP_FROM", user)

        if not all([host, port, user, password, sender]):
            return False, "SMTP no configurado en st.secrets."

        msg = EmailMessage()
        msg["Subject"] = asunto
        msg["From"] = sender
        msg["To"] = destinatario
        msg.set_content(cuerpo_txt)

        msg.add_attachment(pdf_bytes, maintype="application", subtype="pdf", filename=nombre_pdf)

        with smtplib.SMTP(host, port) as server:
            server.starttls()
            server.login(user, password)
            server.send_message(msg)

        return True, "Email enviado."
    except Exception as e:
        return False, f"Fallo al enviar email: {e}"

# =========================
# 2) PDF NOTA DE PEDIDO (plantilla de Excel)
# =========================
PRODUCTOS_COL_IZQ = [
    "Acelga","Achicoria","Ajo","Alcaucil","Ananá","Apio","Arándanos","Banana","Batata","Berenjena",
    "Brócoli","Calabacín","Calabaza","Cebolla","Cerezas","Champiñón","Chaucha","Choclo","Ciruela","Coliflor",
    "Durazno","Espárragos","Espinaca","Frutilla","Kiwi","Lechuga","Lechuguin","Limón","Mandarina","Manzana",
    "Manzana (V)","Melón"
]
PRODUCTOS_COL_DER = [
    "Naranja","Naranja (O)","Palta","Papa","Papa (Bolsa)","Pepino","Pera","Pimiento","Pomelo","Puerro",
    "Remolacha","Repollo","Rúcula","Sandia","Tomate (Cherry)","Tomate (P)","Tomate (R)","Uva","Verdeo","Zanahoria",
    "Zapallito","Zapallo","Zapallo (N)","Zuchini","Oliva","Miel","Huevos","Carbón","Perejil","Bandejas"
]

def _fmt_num(n, dec=2):
    try:
        v = float(n)
    except Exception:
        return ""
    return f"{v:.{dec}f}"

def generar_pdf_wc(datos_pedido):
    """
    datos_pedido:
      {
        "Cliente": str,
        "Domicilio": str,
        "Fecha": "dd/mm/YYYY",
        "Detalle": [ {"Descripción": str, "Cant.": int|float, "Kg.": float, "Importe": float (opcional)} ]
      }
    """
    buf = BytesIO()
    p = canvas.Canvas(buf, pagesize=A4)
    w, h = A4

    margin_x = 15 * mm
    margin_y = 12 * mm

    # Encabezado
    p.setFont("Helvetica-Bold", 16)
    p.drawString(margin_x, h - margin_y - 10, "FRUTAS Y VERDURAS WC")
    p.setFont("Helvetica-Bold", 13)
    p.drawString(margin_x, h - margin_y - 28, "NOTA DE PEDIDO")

    p.setFont("Helvetica", 10)
    p.drawString(margin_x, h - margin_y - 44, "Contacto: 351 6351605")
    p.drawString(margin_x + 150, h - margin_y - 44, "Correo: frutasyverduraswc@gmail.com")

    # Fecha DIA/MES/AÑO
    try:
        dd, mm_, yy = datos_pedido.get("Fecha","").split("/")
    except Exception:
        dd = mm_ = yy = ""
    y_top = h - margin_y - 62
    p.setFont("Helvetica", 10)
    p.drawString(margin_x, y_top, "DIA")
    p.drawString(margin_x + 60, y_top, "MES")
    p.drawString(margin_x + 120, y_top, "AÑO")

    def draw_boxed_text(x, y, txt, w_box=40, h_box=12):
        p.rect(x, y - h_box + 2, w_box, h_box, stroke=1, fill=0)
        p.drawCentredString(x + w_box/2, y - h_box + 4, str(txt))

    draw_boxed_text(margin_x, y_top - 2, dd)
    draw_boxed_text(margin_x + 60, y_top - 2, mm_)
    draw_boxed_text(margin_x + 120, y_top - 2, yy)

    # Cliente y Domicilio
    y_info = y_top - 26
    p.setFont("Helvetica-Bold", 11)
    p.drawString(margin_x, y_info, f"Cliente:  {datos_pedido.get('Cliente','')}")
    y_info -= 16
    p.setFont("Helvetica", 10)
    p.drawString(margin_x, y_info, f"Domicilio:  {datos_pedido.get('Domicilio','')}")

    # Tabla doble
    y_tbl_top = y_info - 18
    col_gap = 10 * mm
    col_width = (w - 2*margin_x - col_gap) / 2
    left_x = margin_x
    right_x = margin_x + col_width + col_gap

    desc_w = col_width * 0.55
    cant_w = col_width * 0.12
    kg_w   = col_width * 0.13
    imp_w  = col_width * 0.20
    row_h  = 12

    def draw_table_header(x0, y0):
        p.setFont("Helvetica-Bold", 10)
        p.drawString(x0 + 2, y0, "Descripción")
        p.drawRightString(x0 + desc_w + cant_w - 2, y0, "Cant.")
        p.drawRightString(x0 + desc_w + cant_w + kg_w - 2, y0, "Kg.")
        p.drawRightString(x0 + desc_w + cant_w + kg_w + imp_w - 2, y0, "Importe")
        p.setStrokeColor(colors.black)
        p.line(x0, y0 - 3, x0 + col_width, y0 - 3)

    # Mapa de items
    idx = {}
    for it in datos_pedido.get("Detalle", []):
        desc = str(it.get("Descripción","")).strip().upper()
        idx[desc] = {
            "cant": it.get("Cant.", ""),
            "kg": it.get("Kg.", ""),
            "imp": it.get("Importe", None)
        }

    def draw_row(x0, y, nombre):
        p.setFont("Helvetica", 10)
        p.drawString(x0 + 2, y, nombre)
        k = idx.get(nombre.upper(), None)
        if k and k["cant"] not in (None, "", 0, 0.0):
            p.drawRightString(x0 + desc_w + cant_w - 2, y, str(int(float(k["cant"]))))
        if k and k["kg"] not in (None, "", 0, 0.0):
            p.drawRightString(x0 + desc_w + cant_w + kg_w - 2, y, _fmt_num(k["kg"]))
        if k and k["imp"] not in (None, "", 0, 0.0):
            p.drawRightString(x0 + desc_w + cant_w + kg_w + imp_w - 2, y, _fmt_num(k["imp"], 2))

    # Bloque izquierdo
    y_cursor_left = y_tbl_top
    draw_table_header(left_x, y_cursor_left)
    y_cursor_left -= row_h
    for nombre in PRODUCTOS_COL_IZQ:
        draw_row(left_x, y_cursor_left + 2, nombre)
        y_cursor_left -= row_h

    # Bloque derecho
    y_cursor_right = y_tbl_top
    draw_table_header(right_x, y_cursor_right)
    y_cursor_right -= row_h
    for nombre in PRODUCTOS_COL_DER:
        draw_row(right_x, y_cursor_right + 2, nombre)
        y_cursor_right -= row_h

    # Totales y leyenda
    total_importe = 0.0
    hay_importes = False
    for v in idx.values():
        if v["imp"] not in (None, "", 0, 0.0):
            total_importe += float(v["imp"])
            hay_importes = True

    vacios = 0
    for nombre in (PRODUCTOS_COL_IZQ + PRODUCTOS_COL_DER):
        k = idx.get(nombre.upper(), None)
        if not k or (not k["cant"] and not k["kg"]):
            vacios += 1

    y_total_line = min(y_cursor_left, y_cursor_right) - 6
    p.setStrokeColor(colors.black)
    p.line(margin_x, y_total_line, w - margin_x, y_total_line)

    y_total = y_total_line - 14
    p.setFont("Helvetica-Bold", 12)
    p.drawString(margin_x, y_total, "TOTAL")
    if hay_importes:
        p.drawRightString(w - margin_x, y_total, _fmt_num(total_importe, 2))

    p.setFont("Helvetica", 10)
    p.drawString(margin_x, y_total - 16, f"Vacíos: {vacios}")

    p.setFont("Helvetica", 11)
    p.drawRightString(w - margin_x, y_total - 16, "Gracias por tu compra.")

    p.showPage()
    p.save()
    buf.seek(0)
    return buf

# =========================
# 3) UI - Navegación
# =========================
init_state()
st.title("🍎 FRUTAS WC")

c1, c2, c3, c4 = st.columns(4)
if st.session_state.rol == "Cliente":
    if c1.button("🏠 Inicio", use_container_width=True): st.session_state.nav = "Inicio"
    if c2.button("📖 Nosotros", use_container_width=True): st.session_state.nav = "Nosotros"
    if c3.button("🛒 Crear Pedido", use_container_width=True): st.session_state.nav = "Crear Pedido"
    if c4.button("🔎 Mi Pedido", use_container_width=True): st.session_state.nav = "Estado"

st.divider()

# =========================
# 4) CREAR PEDIDO
# =========================
if st.session_state.nav == "Crear Pedido":
    st.header("🛒 Armá tu Pedido")

    with st.form("form_pedido", clear_on_submit=False):
        nombre_c = st.text_input("Nombre del Cliente / Negocio").strip()
        domicilio = st.text_input("Domicilio (dirección de entrega)").strip()
        email_cli = st.text_input("Correo electrónico para notificaciones y PDF").strip()

        col_f, col_h1, col_h2 = st.columns([2, 1, 1])
        with col_f:
            fecha_e = st.date_input("Fecha de Entrega", min_value=datetime.now().date() + timedelta(days=1))
        with col_h1:
            h_desde = st.time_input("Desde", value=time(8, 0))
        with col_h2:
            h_hasta = st.time_input("Hasta", value=time(14, 0))

        st.write("---")
        st.subheader("1. Seleccioná de la lista")
        col_p, col_c, col_k, col_b = st.columns([3, 1, 1, 1])
        with col_p:
            item_sel = st.selectbox("Producto", st.session_state.productos_todos, index=0, key="prod_sel")
        with col_c:
            cant_sel = st.number_input("Bultos", min_value=0, step=1, key="cant_sel")
        with col_k:
            kg_sel = st.number_input("Kg.", min_value=0.0, step=0.5, key="kg_sel")
        with col_b:
            st.write(" ")
            add_main = st.form_submit_button("➕ Agregar", use_container_width=True)

        if add_main:
            if cant_sel <= 0 and kg_sel <= 0:
                st.warning("Indicá Bultos y/o Kg para agregar.")
            else:
                agregar_item(item_sel, cant_sel, kg_sel, "Catálogo")

        # ESPECIALES
        with st.expander("➕ Agregar producto que NO está en la lista"):
            st.info("Usá esta sección solo si el producto no figura en el buscador de arriba.")
            col_n1, col_n2, col_n3, col_n4 = st.columns([3, 1, 1, 1])
            with col_n1:
                o_nom = st.text_input("Nombre del producto especial", key="o_nom")
            with col_n2:
                o_can = st.number_input("Bultos", min_value=0, step=1, key="o_can")
            with col_n3:
                o_kg = st.number_input("Kg.", min_value=0.0, step=0.5, key="o_kg")
            with col_n4:
                st.write(" ")
                add_esp = st.form_submit_button("✔ Añadir como ESPECIAL", use_container_width=True)

            if add_esp:
                if not o_nom.strip():
                    st.warning("Escribí el nombre del producto especial.")
                elif o_can <= 0 and o_kg <= 0:
                    st.warning("Indicá Bultos y/o Kg para el producto especial.")
                else:
                    agregar_item(o_nom, o_can, o_kg, "ESPECIAL")

        submitted_final = st.form_submit_button("🚀 FINALIZAR Y GENERAR PDF", use_container_width=True)

    # TABLA EDITABLE
    if st.session_state.lista:
        st.write("### 📋 Tu Pedido hasta ahora")

        df = pd.DataFrame(st.session_state.lista)
        if "Eliminar" not in df.columns:
            df["Eliminar"] = False

        edited_df = st.data_editor(
            df,
            hide_index=True,
            use_container_width=True,
            column_config={
                "Descripción": st.column_config.TextColumn("Descripción", width="large"),
                "Cant.": st.column_config.NumberColumn("Bultos", min_value=0, step=1),
                "Kg.": st.column_config.NumberColumn("Kg.", min_value=0.0, step=0.5, format="%.2f"),
                "Tipo": st.column_config.TextColumn("Tipo"),
                "Eliminar": st.column_config.CheckboxColumn("Eliminar")
            }
        )

        # limpiar y normalizar
        cleaned = []
        for _, r in edited_df.iterrows():
            if r["Eliminar"]:
                continue
            c = max(int(r["Cant."]), 0)
            k = max(float(r["Kg."]), 0.0)
            if c == 0 and k == 0:
                continue
            cleaned.append({
                "Descripción": normalizar_texto(r["Descripción"]),
                "Cant.": c,
                "Kg.": round(k, 2),
                "Tipo": normalizar_texto(r["Tipo"])
            })

        st.session_state.lista = cleaned
        df_now = pd.DataFrame(cleaned)

        c_tot, k_tot = totals(df_now)
        st.info(f"**Totales:** Bultos = {c_tot}  |  Kg = {k_tot:.2f}")

        if st.button("🗑️ Borrar último ítem", use_container_width=True):
            if st.session_state.lista:
                st.session_state.lista.pop()
                st.rerun()
    else:
        df_now = pd.DataFrame(columns=["Descripción", "Cant.", "Kg.", "Tipo"])

    # FINALIZAR
    if submitted_final:
        errores = []
        if not nombre_c: errores.append("• Completá el **Nombre**.")
        if not domicilio: errores.append("• Completá el **Domicilio**.")
        if not es_email_valido(email_cli): errores.append("• Ingresá un **correo electrónico válido**.")
        if not st.session_state.lista: errores.append("• Agregá al menos **un** producto.")
        if h_desde >= h_hasta: errores.append("• Revisá el **rango horario**.")

        if errores:
            st.error("No se pudo finalizar el pedido:\n\n" + "\n".join(errores))
        else:
            resumen = {
                "Cliente": normalizar_texto(nombre_c),
                "Domicilio": domicilio.strip(),
                "Email": email_cli.strip(),
                "Fecha": fecha_e.strftime("%d/%m/%Y"),
                "Horario": f"{h_desde.strftime('%H:%M')} a {h_hasta.strftime('%H:%M')}",
                "Detalle": st.session_state.lista
            }

            pdf_io = generar_pdf_wc(resumen)
            pdf_bytes = pdf_io.read() if hasattr(pdf_io, "read") else pdf_io

            order_id = new_order_id()
            pedido = {
                "id": order_id,
                "estado": "Nuevo",  # Nuevo -> Preparación -> Distribución -> Entregado
                "creado_ts": datetime.now().isoformat(timespec="seconds"),
                "resumen": resumen,
                "pdf_nombre": f"Pedido_{resumen['Cliente']}_{order_id}.pdf",
                "pdf_bytes": pdf_bytes,
            }
            st.session_state.pedidos[order_id] = pedido
            st.session_state.ultimo_pedido = pedido

            st.success(f"¡Pedido confirmado! ID: {order_id}")
            st.download_button(
                label="📥 Descargar Nota de Pedido (PDF)",
                data=pdf_bytes,
                file_name=pedido["pdf_nombre"],
                mime="application/pdf",
                use_container_width=True
            )

# =========================
# 5) Secciones extra
# =========================
if st.session_state.nav == "Inicio":
    st.subheader("Bienvenida/o a FRUTAS WC")
    st.write("Hacé tu pedido de manera simple, rápida y con confirmación en PDF.")

if st.session_state.nav == "Nosotros":
    st.subheader("Sobre nosotros")
    st.write("Somos FRUTAS WC, abasteciendo Córdoba con productos frescos. Calidad, compromiso y entrega a tiempo.")

if st.session_state.nav == "Estado":
    st.subheader("Estado de tu pedido")
    ped = st.session_state.get("ultimo_pedido")
    if ped:
        r = ped["resumen"]
        st.write(f"**ID:** {ped['id']}  |  **Estado:** {ped['estado']}  |  **Creado:** {ped['creado_ts']}")
        st.write(f"**Cliente:** {r['Cliente']}  |  **Entrega:** {r['Fecha']}  |  **Horario:** {r['Horario']}")
        st.write(f"**Domicilio:** {r['Domicilio']}  |  **Email:** {r['Email']}")
        st.dataframe(pd.DataFrame(r["Detalle"]), hide_index=True, use_container_width=True)
        st.download_button("📥 Re-descargar PDF", data=ped["pdf_bytes"], file_name=ped["pdf_nombre"], mime="application/pdf")
    else:
        st.info("Todavía no registraste un pedido en esta sesión.")

# =========================
# 6) Login Administración
# =========================
st.write("---")
if st.session_state.rol == "Cliente":
    with st.expander("🔒 Acceso Administración"):
        u = st.text_input("Usuario")
        p = st.text_input("Contraseña", type="password")
        if st.button("Entrar", use_container_width=True):
            valid_user = st.secrets.get("ADMIN_USER", "Luciana")
            valid_pass = st.secrets.get("ADMIN_PASS", "WC2026")
            if u == valid_user and p == valid_pass:
                st.session_state.rol = "Admin"
                st.success("Acceso concedido.")
                st.rerun()
            else:
                st.error("Usuario o contraseña incorrectos.")

# =========================
# 7) Panel Administración: estados + envío email
# =========================
if st.session_state.get("rol") == "Admin":
    st.subheader("🛠 Administración de pedidos")
    if not st.session_state.pedidos:
        st.info("No hay pedidos en memoria.")
    else:
        opciones = [f"{pid} | {p['resumen']['Cliente']} | {p['estado']} | {p['resumen']['Fecha']}" for pid, p in st.session_state.pedidos.items()]
        sel = st.selectbox("Seleccioná un pedido", opciones)
        pid_sel = sel.split(" | ")[0]
        pedido = st.session_state.pedidos[pid_sel]
        r = pedido["resumen"]

        st.write(f"**Cliente:** {r['Cliente']}  —  **Email:** {r['Email']}")
        st.write(f"**Domicilio:** {r['Domicilio']}")
        st.dataframe(pd.DataFrame(r["Detalle"]), hide_index=True, use_container_width=True)

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            if st.button("⏳ Preparación", use_container_width=True):
                pedido["estado"] = "Preparación"
                st.success("Estado cambiado a Preparación.")
                ok, msg = enviar_email_pdf(
                    destinatario=r["Email"],
                    asunto=f"Tu pedido #{pedido['id']} está en PREPARACIÓN - FRUTAS WC",
                    cuerpo_txt=(
                        f"Hola {r['Cliente']},\n\n"
                        "¡Tu pedido ya está en PREPARACIÓN! Te adjuntamos la nota de pedido en PDF.\n"
                        "Cuando salga a distribución, te avisamos nuevamente.\n\n"
                        "Gracias por elegirnos.\nFRUTAS WC"
                    ),
                    nombre_pdf=pedido["pdf_nombre"],
                    pdf_bytes=pedido["pdf_bytes"]
                )
                st.info("Email: " + ("✔ enviado" if ok else f"✖ {msg}"))

        with col2:
            if st.button("🚚 Distribución", use_container_width=True):
                pedido["estado"] = "Distribución"
                st.success("Estado cambiado a Distribución.")
                ok, msg = enviar_email_pdf(
                    destinatario=r["Email"],
                    asunto=f"Tu pedido #{pedido['id']} está en DISTRIBUCIÓN - FRUTAS WC",
                    cuerpo_txt=(
                        f"Hola {r['Cliente']},\n\n"
                        "¡Tu pedido ya está en DISTRIBUCIÓN! Te adjuntamos la nota de pedido en PDF.\n"
                        "En breve lo recibirás en tu domicilio.\n\n"
                        "Saludos,\nFRUTAS WC"
                    ),
                    nombre_pdf=pedido["pdf_nombre"],
                    pdf_bytes=pedido["pdf_bytes"]
                )
                st.info("Email: " + ("✔ enviado" if ok else f"✖ {msg}"))

        with col3:
            if st.button("✅ Entregado", use_container_width=True):
                pedido["estado"] = "Entregado"
                st.success("Estado cambiado a Entregado.")

        with col4:
            if st.button("↩ Volver a Nuevo", use_container_width=True):
                pedido["estado"] = "Nuevo"
                st.warning("Estado reiniciado a Nuevo.")

# =========================
# 8) WhatsApp flotante
# =========================
import urllib.parse as up
wa_msg_default = up.quote("Consultas FRUTAS WC")
wa_link = f"https://wa.me/543516422893?text={wa_msg_default}"
st.markdown(f'<a href="{wa_link}" class="wa-float" target="_blank">💬 WhatsApp</a>', unsafe_allow_html=True)
