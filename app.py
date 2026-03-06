# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
import uuid, smtplib
from email.message import EmailMessage
from datetime import datetime, timedelta, time
from io import BytesIO

# Librerías para el PDF
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm

# --- 1. CONFIGURACIÓN Y ESTILO ---
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
}
.wa-float { 
    position: fixed; bottom: 20px; right: 20px; background-color: #25d366; 
    color: white; border-radius: 50px; padding: 12px 20px; 
    display: flex; align-items: center; gap: 10px; text-decoration: none; 
    z-index: 100; font-weight: bold;
}
</style>
""", unsafe_allow_html=True)

# --- 2. ESTADO DE SESIÓN ---
if "nav" not in st.session_state: st.session_state.nav = "Inicio"
if "rol" not in st.session_state: st.session_state.rol = "Cliente"
if "lista" not in st.session_state: st.session_state.lista = []
if "pedidos" not in st.session_state: st.session_state.pedidos = {}

PRODUCTOS_IZQ = ["Acelga","Achicoria","Ajo","Alcaucil","Ananá","Apio","Arándanos","Banana","Batata","Berenjena","Cebolla","Choclo"]
PRODUCTOS_DER = ["Naranja","Palta","Papa","Papa (Bolsa)","Pimiento","Tomate (Cherry)","Tomate (R)","Huevos","Carbón"]
TODOS = sorted(PRODUCTOS_IZQ + PRODUCTOS_DER)

# --- 3. FUNCIONES DE APOYO ---
def agregar_item(desc, cant, kg, tipo):
    desc = str(desc).strip().upper()
    # Si ya existe, sumamos
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

    # Encabezado
    p.setFont("Helvetica-Bold", 16)
    p.drawString(mx, h-my, "FRUTAS Y VERDURAS WC")
    p.setFont("Helvetica", 10)
    p.drawString(mx, h-my-15, "Contacto: 351 6351605 | Correo: frutasyverduraswc@gmail.com")
    p.line(mx, h-my-20, w-mx, h-my-20)

    # Info Cliente
    p.setFont("Helvetica-Bold", 12)
    p.drawString(mx, h-my-40, f"Cliente: {datos['Cliente']}")
    p.setFont("Helvetica", 10)
    p.drawString(mx, h-my-55, f"Fecha: {datos['Fecha']} | Horario: {datos['Horario']}")
    p.drawString(mx, h-my-70, f"Domicilio: {datos['Domicilio']}")

    # Tabla
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
        if y < 40*mm: p.showPage(); y = h-my

    p.showPage()
    p.save()
    buf.seek(0)
    return buf

# --- 4. INTERFAZ ---
st.title("🍎 FRUTAS WC")
c_nav = st.columns(4)
if c_nav[2].button("🛒 Crear Pedido"): 
    st.session_state.nav = "Crear Pedido"
    st.session_state.pedido_exitoso = False

if st.session_state.nav == "Crear Pedido":
    if st.session_state.pedido_exitoso:
        st.markdown(f'<div class="success-msg">✅ Pedido solicitado con éxito<br>Número de pedido: {st.session_state.nro_pedido}</div>', unsafe_allow_html=True)
        if st.button("Hacer otro pedido"):
            st.session_state.pedido_exitoso = False
            st.session_state.lista = []
            st.rerun()
    else:
        cli = st.text_input("Nombre del Cliente")
        dom = st.text_input("Domicilio")
        
        col_prod, col_c, col_k, col_btn = st.columns([3, 1, 1, 1])
        item = col_prod.selectbox("Producto", PRODUCTOS)
        cant = col_c.number_input("Bultos", min_value=0, step=1)
        kg = col_k.number_input("Kg.", min_value=0.0, step=0.5)
        
        if col_btn.button("➕"):
            if cant > 0 or kg > 0:
                agregar_item(item, cant, kg, "CATÁLOGO")
                st.rerun()

        if st.session_state.lista:
            st.table(pd.DataFrame(st.session_state.lista))
            
            if st.button("🚀 FINALIZAR PEDIDO", use_container_width=True):
                if cli and dom:
                    nro = uuid.uuid4().hex[:6].upper()
                    datos = {
                        "Cliente": cli.upper(),
                        "Fecha": datetime.now().strftime("%d/%m/%Y"),
                        "Horario": "A coordinar",
                        "Detalle": st.session_state.lista
                    }
                    pdf = generar_pdf_wc(datos, nro)
                    
                    # ACTIVAR LEYENDA
                    st.session_state.nro_pedido = nro
                    st.session_state.pedido_exitoso = True
                    st.rerun()
                else:
                    st.error("Completa los datos de envío.")

# WhatsApp
st.markdown(f'<a class="wa-float" href="https://wa.me/543516422893" target="_blank">💬 WhatsApp</a>', unsafe_allow_html=True)
