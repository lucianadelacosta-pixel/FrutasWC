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
    border-radius: 15px; padding: 30px; max-width: 1000px; 
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
if "lista" not in st.session_state: st.session_state.lista = {} # Cambiado a dict para facilitar búsqueda
if "pedidos" not in st.session_state: st.session_state.pedidos = {}
if "ultimo_pedido" not in st.session_state: st.session_state.ultimo_pedido = None
if "pedido_finalizado" not in st.session_state: st.session_state.pedido_finalizado = False

# Listas exactas según tu Excel
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
def agregar_item(desc, cant, kg):
    desc = str(desc).strip().upper()
    st.session_state.lista[desc] = {"Cant.": cant, "Kg.": kg}

def generar_pdf_wc(datos):
    buf = BytesIO()
    p = canvas.Canvas(buf, pagesize=A4)
    w, h = A4
    mx, my = 10*mm, 10*mm

    # --- ENCABEZADO ESTILO EXCEL ---
    p.setFont("Helvetica-Bold", 14)
    p.drawString(mx, h-my-5*mm, "FRUTAS Y VERDURAS WC")
    p.setFont("Helvetica-Bold", 12)
    p.drawRightString(w-mx, h-my-5*mm, "NOTA DE PEDIDO")
    
    p.setFont("Helvetica", 8)
    p.drawString(mx, h-my-10*mm, "Contacto: 351 6351605")
    p.drawString(mx, h-my-14*mm, "Correo: frutasyverduraswc@gmail.com")
    
    # Fecha (Día/Mes/Año)
    p.setFont("Helvetica-Bold", 9)
    p.drawString(w-mx-30*mm, h-my-10*mm, f"FECHA: {datos['Fecha']}")
    
    # Datos Cliente
    p.rect(mx, h-my-35*mm, w-2*mx, 15*mm) # Recuadro info
    p.setFont("Helvetica-Bold", 10)
    p.drawString(mx+2*mm, h-my-26*mm, f"CLIENTE: {datos['Cliente']}")
    p.drawString(mx+2*mm, h-my-32*mm, f"DOMICILIO: {datos['Domicilio']}")
    
    # --- TABLA DOBLE COLUMNA ---
    y_start = h-my-45*mm
    col_width = (w - 2*mx) / 2
    
    def dibujar_encabezado_tabla(x, y):
        p.setFont("Helvetica-Bold", 8)
        p.setFillColor(colors.lightgrey)
        p.rect(x, y-4*mm, col_width, 5*mm, fill=1)
        p.setFillColor(colors.black)
        p.drawString(x+2*mm, y-1*mm, "Descripción")
        p.drawString(x+col_width-35*mm, y-1*mm, "Cant.")
        p.drawString(x+col_width-20*mm, y-1*mm, "Kg.")
        p.drawString(x+col_width-10*mm, y-1*mm, "$")

    dibujar_encabezado_tabla(mx, y_start)
    dibujar_encabezado_tabla(mx + col_width, y_start)
    
    # Dibujar filas
    y = y_start - 5*mm
    p.setFont("Helvetica", 8)
    line_height = 4.5*mm
    
    max_filas = max(len(PRODUCTOS_IZQ), len(PRODUCTOS_DER))
    
    pedido = datos['Detalle'] # Es un diccionario {NOMBRE: {Cant, Kg}}

    for i in range(max_filas):
        # Columna Izquierda
        if i < len(PRODUCTOS_IZQ):
            prod = PRODUCTOS_IZQ[i]
            p.drawString(mx+2*mm, y, prod)
            if prod.upper() in pedido:
                p.setFont("Helvetica-Bold", 8)
                p.drawString(mx+col_width-35*mm, y, str(pedido[prod.upper()]['Cant.']) if pedido[prod.upper()]['Cant.'] > 0 else "")
                p.drawString(mx+col_width-20*mm, y, str(pedido[prod.upper()]['Kg.']) if pedido[prod.upper()]['Kg.'] > 0 else "")
                p.setFont("Helvetica", 8)
            p.line(mx, y-1*mm, mx+col_width, y-1*mm)

        # Columna Derecha
        if i < len(PRODUCTOS_DER):
            prod = PRODUCTOS_DER[i]
            p.drawString(mx+col_width+2*mm, y, prod)
            if prod.upper() in pedido:
                p.setFont("Helvetica-Bold", 8)
                p.drawString(mx+2*col_width-35*mm, y, str(pedido[prod.upper()]['Cant.']) if pedido[prod.upper()]['Cant.'] > 0 else "")
                p.drawString(mx+2*col_width-20*mm, y, str(pedido[prod.upper()]['Kg.']) if pedido[prod.upper()]['Kg.'] > 0 else "")
                p.setFont("Helvetica", 8)
            p.line(mx+col_width, y-1*mm, w-mx, y-1*mm)
        
        y -= line_height

    # Bordes verticales
    p.line(mx, y_start+1*mm, mx, y+line_height-1*mm)
    p.line(mx+col_width, y_start+1*mm, mx+col_width, y+line_height-1*mm)
    p.line(w-mx, y_start+1*mm, w-mx, y+line_height-1*mm)

    p.showPage()
    p.save()
    buf.seek(0)
    return buf

# =========================
# 3) INTERFAZ DE USUARIO
# =========================
st.title("🍎 FRUTAS WC")
c_nav = st.columns(4)
if c_nav[0].button("🏠 Inicio", use_container_width=True): 
    st.session_state.nav = "Inicio"
    st.session_state.pedido_finalizado = False
if c_nav[1].button("📖 Nosotros", use_container_width=True): 
    st.session_state.nav = "Nosotros"
if c_nav[2].button("🛒 Crear Pedido", use_container_width=True): 
    st.session_state.nav = "Crear Pedido"
    st.session_state.pedido_finalizado = False
if c_nav[3].button("🔎 Mi Pedido", use_container_width=True): 
    st.session_state.nav = "Estado"

st.divider()

if st.session_state.nav == "Crear Pedido":
    if st.session_state.pedido_finalizado:
        st.balloons()
        st.success("## ✅ ¡Pedido Generado con Éxito!")
        p = st.session_state.ultimo_pedido
        st.write(f"### ID del Pedido: **{p['id']}**")
        
        c_ex1, c_ex2 = st.columns(2)
        with c_ex1:
            st.download_button("📥 Descargar NOTA DE PEDIDO (PDF)", data=p['pdf_bytes'], 
                               file_name=f"Nota_Pedido_{p['id']}.pdf", mime="application/pdf", use_container_width=True)
        with c_ex2:
            if st.button("🔎 Ver Estado de mi Pedido", use_container_width=True):
                st.session_state.nav = "Estado"; st.session_state.pedido_finalizado = False; st.rerun()
        
        if st.button("🛒 Crear otro Pedido", use_container_width=True):
            st.session_state.pedido_finalizado = False; st.rerun()

    else:
        st.header("🛒 Armá tu Pedido")
        with st.container():
            col_cli, col_dom, col_mail = st.columns(3)
            cli = col_cli.text_input("Nombre / Negocio")
            dom = col_dom.text_input("Domicilio")
            mail = col_mail.text_input("Email")
            
            c_t1, c_t2, c_t3 = st.columns([2,1,1])
            fec = c_t1.date_input("Fecha de entrega", min_value=datetime.now().date() + timedelta(days=1))
            h1 = c_t2.time_input("Desde", value=time(8,0))
            h2 = c_t3.time_input("Hasta", value=time(14,0))

        st.write("---")
        st.subheader("1. Seleccioná del catálogo")
        cp, cc, ck, cb = st.columns([3, 1, 1, 1])
        item = cp.selectbox("Producto", TODOS)
        cant = cc.number_input("Cant. (Bultos)", min_value=0, step=1)
        kg = ck.number_input("Kg.", min_value=0.0, step=0.5)
        if cb.button("➕ Agregar", use_container_width=True):
            if cant > 0 or kg > 0:
                agregar_item(item, cant, kg)
                st.toast(f"Agregado: {item}")

        if st.session_state.lista:
            st.write("### 📋 Resumen del Pedido")
            df_resumen = pd.DataFrame.from_dict(st.session_state.lista, orient='index').reset_index()
            df_resumen.columns = ["Descripción", "Cant.", "Kg."]
            st.dataframe(df_resumen, hide_index=True, use_container_width=True)
            
            if st.button("🗑️ Vaciar Lista"):
                st.session_state.lista = {}
                st.rerun()

            if st.button("🚀 CONFIRMAR PEDIDO Y GENERAR PDF", use_container_width=True):
                if cli and dom:
                    datos = {
                        "Cliente": cli.upper(), "Domicilio": dom, "Email": mail,
                        "Fecha": fec.strftime("%d/%m/%Y"),
                        "Horario": f"{h1.strftime('%H:%M')} a {h2.strftime('%H:%M')}",
                        "Detalle": dict(st.session_state.lista)
                    }
                    pdf_io = generar_pdf_wc(datos)
                    pdf_bytes = pdf_io.getvalue()
                    oid = uuid.uuid4().hex[:6].upper()
                    
                    pedido = {"id": oid, "resumen": datos, "pdf_bytes": pdf_bytes, "estado": "Nuevo"}
                    st.session_state.pedidos[oid] = pedido
                    st.session_state.ultimo_pedido = pedido
                    st.session_state.pedido_finalizado = True
                    st.session_state.lista = {}
                    st.rerun()
                else:
                    st.error("⚠️ El nombre y domicilio son obligatorios.")

# --- SECCIONES RESTANTES ---
elif st.session_state.nav == "Inicio":
    st.subheader("Bienvenida/o a FRUTAS WC")
    st.info("Hacé tu pedido online y recibí tu nota de pedido profesional al instante.")

elif st.session_state.nav == "Estado":
    st.subheader("🔎 Mi Pedido")
    p = st.session_state.ultimo_pedido
    if p:
        st.write(f"**Pedido ID:** {p['id']} | **Estado:** {p['estado']}")
        df_p = pd.DataFrame.from_dict(p['resumen']['Detalle'], orient='index').reset_index()
        df_p.columns = ["Descripción", "Cant.", "Kg."]
        st.dataframe(df_p, hide_index=True)
        st.download_button("📥 Descargar PDF nuevamente", data=p['pdf_bytes'], file_name=f"Pedido_{p['id']}.pdf")
    else: st.warning("No tienes pedidos activos.")

st.markdown(f'<a class="wa-float" href="https://wa.me/543516422893" target="_blank">💬 WhatsApp</a>', unsafe_allow_html=True)
