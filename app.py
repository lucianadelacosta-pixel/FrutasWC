# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
import uuid, smtplib
from email.message import EmailMessage
from datetime import datetime, timedelta, time
from io import BytesIO

from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm

# =========================
# 0) CONFIGURACIÓN Y ESTILO
# =========================
st.set_page_config(page_title="FRUTAS WC", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
<style>
[data-testid="stSidebar"] {display: none;}
.stApp { 
    background-image: url("app/static/fondo.jpg"); 
    background-size: cover; 
    background-position: center bottom; 
    background-attachment: fixed; 
}
.main .block-container { 
    background-color: rgba(255, 255, 255, 0.96); 
    border-radius: 15px; padding: 30px; max-width: 980px; 
    box-shadow: 0px 4px 15px rgba(0,0,0,0.1);
}
.wa-float { 
    position: fixed; bottom: 20px; right: 20px; background-color: #25d366; 
    color: white; border-radius: 50px; padding: 12px 20px; 
    display: flex; align-items: center; gap: 10px; text-decoration: none; 
    z-index: 100; font-weight: bold; box-shadow: 2px 2px 10px rgba(0,0,0,0.2);
}
</style>
""", unsafe_allow_html=True)

# =========================
# 1) ESTADO DE SESIÓN
# =========================
if "nav" not in st.session_state: st.session_state.nav = "Inicio"
if "rol" not in st.session_state: st.session_state.rol = "Cliente"
if "lista" not in st.session_state: st.session_state.lista = []
if "pedidos" not in st.session_state: st.session_state.pedidos = {}
if "ultimo_pedido" not in st.session_state: st.session_state.ultimo_pedido = None

PRODUCTOS_IZQ = [
    "Acelga","Achicoria","Ajo","Alcaucil","Ananá","Apio","Arándanos","Banana","Batata","Berenjena",
    "Brócoli","Calabacín","Calabaza","Cebolla","Cerezas","Champiñón","Chaucha","Choclo","Ciruela","Coliflor",
    "Durazno","Espárragos","Espinaca","Frutilla","Kiwi","Lechuga","Lechuguin","Limón","Mandarina","Manzana",
    "Manzana (V)","Melón"
]
PRODUCTOS_DER = [
    "Naranja","Naranja (O)","Palta","Papa","Papa (Bolsa)","Pepino","Pera","Pimiento","Pomelo","Puerro",
    "Remolacha","Repollo","Rúcula","Sandia","Tomate (Cherry)","Tomate (P)","Tomate (R)","Uva","Verdeo","Zanahoria",
    "Zapallito","Zapallo","Zapallo (N)","Zuchini","Oliva","Miel","Huevos","Carbón","Perejil","Bandejas"
]
TODOS = sorted(PRODUCTOS_IZQ + PRODUCTOS_DER)

# =========================
# 2) FUNCIONES CORE
# =========================
def agregar_item(desc, cant, kg, tipo):
    desc = str(desc).strip().upper()
    for row in st.session_state.lista:
        if row["Descripción"] == desc:
            row["Cant."] += cant
            row["Kg."] += kg
            return
    st.session_state.lista.append({"Descripción": desc, "Cant.": cant, "Kg.": kg, "Tipo": tipo})

def generar_pdf_wc(datos):
    buf = BytesIO()
    p = canvas.Canvas(buf, pagesize=A4)
    w, h = A4
    mx, my = 15*mm, 15*mm

    # Header
    p.setFont("Helvetica-Bold", 16)
    p.drawString(mx, h-my, "FRUTAS Y VERDURAS WC")
    p.setFont("Helvetica", 10)
    p.drawString(mx, h-my-15, "Contacto: 351 6351605 | Correo: frutasyverduraswc@gmail.com")
    p.line(mx, h-my-20, w-mx, h-my-20)

    # Info Pedido
    p.setFont("Helvetica-Bold", 12)
    p.drawString(mx, h-my-40, f"Cliente: {datos['Cliente']}")
    p.setFont("Helvetica", 10)
    p.drawString(mx, h-my-55, f"Fecha: {datos['Fecha']} | Horario: {datos['Horario']}")
    p.drawString(mx, h-my-70, f"Domicilio: {datos['Domicilio']}")

    # Tabla de Pedido
    y = h-my-100
    p.setFont("Helvetica-Bold", 10)
    p.drawString(mx, y, "Descripción")
    p.drawString(mx+260, y, "Bultos")
    p.drawString(mx+320, y, "Kg.")
    p.drawString(mx+400, y, "Tipo")
    p.line(mx, y-5, w-mx, y-5)

    y -= 20
    p.setFont("Helvetica", 10)
    for it in datos['Detalle']:
        p.drawString(mx, y, it['Descripción'])
        p.drawString(mx+260, y, str(it['Cant.']))
        p.drawString(mx+320, y, str(it['Kg.']))
        p.drawString(mx+400, y, it['Tipo'])
        y -= 15
        if y < 40*mm: p.showPage(); y = h-my # Salto de página simple

    p.showPage()
    p.save()
    buf.seek(0)
    return buf

def enviar_email(dest, asunto, cuerpo, pdf_nombre, pdf_bytes):
    try:
        msg = EmailMessage()
        msg["Subject"] = asunto
        msg["From"] = st.secrets["SMTP_FROM"]
        msg["To"] = dest
        msg.set_content(cuerpo)
        msg.add_attachment(pdf_bytes, maintype="application", subtype="pdf", filename=pdf_nombre)
        with smtplib.SMTP(st.secrets["SMTP_HOST"], st.secrets["SMTP_PORT"], timeout=10) as s:
            s.starttls()
            s.login(st.secrets["SMTP_USER"], st.secrets["SMTP_PASS"])
            s.send_message(msg)
        return True, "Enviado"
    except Exception as e: return False, str(e)

# =========================
# 3) INTERFAZ DE USUARIO
# =========================
st.title("🍎 FRUTAS WC")
c_nav = st.columns(4)
if c_nav[0].button("🏠 Inicio", use_container_width=True): st.session_state.nav = "Inicio"
if c_nav[1].button("📖 Nosotros", use_container_width=True): st.session_state.nav = "Nosotros"
if c_nav[2].button("🛒 Crear Pedido", use_container_width=True): st.session_state.nav = "Crear Pedido"
if c_nav[3].button("🔎 Mi Pedido", use_container_width=True): st.session_state.nav = "Estado"

st.divider()

if st.session_state.nav == "Crear Pedido":
    st.header("🛒 Armá tu Pedido")
    
    # Datos de contacto
    with st.container():
        cli = st.text_input("Nombre del Cliente / Negocio")
        dom = st.text_input("Domicilio de Entrega")
        mail = st.text_input("Email para el PDF")
        
        c_t1, c_t2, c_t3 = st.columns([2,1,1])
        fec = c_t1.date_input("Fecha de entrega", min_value=datetime.now().date() + timedelta(days=1))
        h1 = c_t2.time_input("Desde", value=time(8,0))
        h2 = c_t3.time_input("Hasta", value=time(14,0))

    st.write("---")

    # 1. Selección de Catálogo
    st.subheader("1. Seleccioná del catálogo")
    cp, cc, ck, cb = st.columns([3, 1, 1, 1])
    item = cp.selectbox("Producto", TODOS)
    cant = cc.number_input("Bultos", min_value=0, step=1, key="c_cat")
    kg = ck.number_input("Kg.", min_value=0.0, step=0.5, key="k_cat")
    if cb.button("➕ Agregar", use_container_width=True):
        if cant > 0 or kg > 0:
            agregar_item(item, cant, kg, "CATÁLOGO")
            st.rerun()

    # 2. Tu Pedido Actual (Justo debajo de la selección)
    if st.session_state.lista:
        st.write("### 📋 Tu Pedido Actual")
        df = pd.DataFrame(st.session_state.lista)
        st.dataframe(df, hide_index=True, use_container_width=True)
        if st.button("🗑️ Vaciar Lista"):
            st.session_state.lista = []
            st.rerun()
        st.write("---")

    # 3. Producto Especial (Al final)
    with st.expander("➕ Agregar producto que NO está en la lista"):
        ce1, ce2, ce3, ce4 = st.columns([3, 1, 1, 1])
        e_nom = ce1.text_input("Nombre producto especial")
        e_can = ce2.number_input("Bultos", min_value=0, step=1, key="c_esp")
        e_kg = ce3.number_input("Kg.", min_value=0.0, step=0.5, key="k_esp")
        if ce4.button("✔ Añadir Especial"):
            if e_nom:
                agregar_item(e_nom, e_can, e_kg, "ESPECIAL")
                st.rerun()

    # 4. Botón Confirmar
    if st.session_state.lista:
        if st.button("🚀 CONFIRMAR PEDIDO Y GENERAR PDF", use_container_width=True):
            if cli and mail and dom:
                datos = {
                    "Cliente": cli.upper(), "Domicilio": dom,
                    "Fecha": fec.strftime("%d/%m/%Y"),
                    "Horario": f"{h1.strftime('%H:%M')} a {h2.strftime('%H:%M')}",
                    "Detalle": st.session_state.lista
                }
                pdf_io = generar_pdf_wc(datos)
                pdf_bytes = pdf_io.getvalue()
                oid = uuid.uuid4().hex[:6].upper()
                
                pedido = {"id": oid, "resumen": datos, "pdf_bytes": pdf_bytes, "estado": "Nuevo"}
                st.session_state.pedidos[oid] = pedido
                st.session_state.ultimo_pedido = pedido
                
                st.success(f"¡Pedido confirmado! ID: {oid}")
                st.download_button("📥 Descargar mi PDF", data=pdf_bytes, file_name=f"Pedido_WC_{cli}.pdf", mime="application/pdf")
            else:
                st.error("Por favor completa Nombre, Domicilio y Email.")

# --- INICIO, NOSOTROS Y ESTADO ---
elif st.session_state.nav == "Inicio":
    st.subheader("Bienvenida/o a FRUTAS WC")
    st.info("Hacé tu pedido online y recibí el PDF al instante.")

elif st.session_state.nav == "Estado":
    st.subheader("🔎 Mi Pedido")
    p = st.session_state.ultimo_pedido
    if p:
        st.write(f"**ID:** {p['id']} | **Estado:** {p['estado']}")
        st.dataframe(pd.DataFrame(p['resumen']['Detalle']), hide_index=True)
        st.download_button("📥 Descargar PDF nuevamente", data=p['pdf_bytes'], file_name=f"Pedido_{p['id']}.pdf")
    else: st.warning("No tienes pedidos activos.")

# =========================
# 6) ADMIN
# =========================
st.write("---")
if st.session_state.rol == "Cliente":
    with st.expander("🔒 Admin"):
        u = st.text_input("Usuario")
        p = st.text_input("Contraseña", type="password")
        if st.button("Entrar"):
            if u == st.secrets["ADMIN_USER"] and p == st.secrets["ADMIN_PASS"]:
                st.session_state.rol = "Admin"; st.rerun()
else:
    st.subheader("🛠 Panel de Administración")
    if not st.session_state.pedidos: st.info("No hay pedidos.")
    else:
        for pid, ped in st.session_state.pedidos.items():
            with st.expander(f"Pedido {pid} - {ped['resumen']['Cliente']}"):
                st.write(f"**Estado actual:** {ped['estado']}")
                c_a1, c_a2 = st.columns(2)
                if c_a1.button(f"Enviar Distribución {pid}"):
                    ok, res = enviar_email(ped['resumen']['Email'], "Tu pedido WC está en camino", "Tu pedido está en distribución.", f"Pedido_{pid}.pdf", ped['pdf_bytes'])
                    if ok: ped['estado'] = "Distribución"; st.success("Email enviado.")
                    else: st.error(res)
                if c_a2.button(f"Marcar Entregado {pid}"): ped['estado'] = "Entregado"; st.rerun()

# WhatsApp
st.markdown(f'<a class="wa-float" href="https://wa.me/543516422893" target="_blank">💬 WhatsApp</a>', unsafe_allow_html=True)
