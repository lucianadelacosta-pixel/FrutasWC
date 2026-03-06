# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
import uuid, smtplib
from email.message import EmailMessage
from datetime import datetime, timedelta, time
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm

# ==========================================
# 1. CONFIGURACIÓN, ESTILOS Y DATOS
# ==========================================
def configurar_pagina():
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

PRODUCTOS_IZQ = ["Acelga","Achicoria","Ajo","Ananá","Apio","Banana","Batata","Berenjena","Cebolla","Lechuga","Limón","Manzana","Melón"]
PRODUCTOS_DER = ["Naranja","Palta","Papa","Pera","Pimiento","Tomate (Cherry)","Tomate (R)","Zanahoria","Huevos","Carbón"]
TODOS = sorted(PRODUCTOS_IZQ + PRODUCTOS_DER)

# ==========================================
# 2. FUNCIONES DE APOYO (PDF, EMAIL, LOGICA)
# ==========================================
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
    p.setFont("Helvetica-Bold", 16)
    p.drawString(mx, h-my, "FRUTAS Y VERDURAS WC")
    # ... (Resto del código de generación de PDF que ya tienes)
    p.save()
    buf.seek(0)
    return buf

# ==========================================
# 3. SECCIONES DE LA PAGINA (LOS BOTONES)
# ==========================================

def pantalla_inicio():
    st.subheader("Bienvenida/o a FRUTAS WC")
    st.info("Hacé tu pedido online y recibí el PDF al instante.")
    st.write("Estamos trabajando para brindarte la mejor calidad de Córdoba.")

def pantalla_nosotros():
    st.subheader("📖 Nuestra Historia")
    st.write("Más de 15 años de experiencia en logística aplicados a la frescura de tu hogar.")
    # Aquí puedes agregar más texto o imágenes sobre el hangar/oficina

def pantalla_crear_pedido():
    if st.session_state.pedido_finalizado:
        st.balloons()
        st.success("## ✅ ¡Pedido Generado con Éxito!")
        p = st.session_state.ultimo_pedido
        st.write(f"### ID del Pedido: **{p['id']}**")
        st.download_button("📥 Descargar Comprobante PDF", data=p['pdf_bytes'], 
                           file_name=f"Pedido_WC_{p['id']}.pdf", mime="application/pdf", use_container_width=True)
        if st.button("🛒 Crear otro Pedido"):
            st.session_state.pedido_finalizado = False
            st.rerun()
    else:
        st.header("🛒 Armá tu Pedido")
        cli = st.text_input("Nombre del Cliente / Negocio")
        dom = st.text_input("Domicilio de Entrega")
        mail = st.text_input("Email para el PDF")
        
        c_t1, c_t2, c_t3 = st.columns([2,1,1])
        fec = c_t1.date_input("Fecha de entrega", min_value=datetime.now().date() + timedelta(days=1))
        h1 = c_t2.time_input("Desde", value=time(8,0))
        h2 = c_t3.time_input("Hasta", value=time(14,0))

        st.divider()
        st.subheader("1. Seleccioná del catálogo")
        cp, cc, ck, cb = st.columns([3, 1, 1, 1])
        item = cp.selectbox("Producto", TODOS)
        cant = cc.number_input("Bultos", min_value=0, step=1, key="c_cat")
        kg = ck.number_input("Kg.", min_value=0.0, step=0.5, key="k_cat")
        if cb.button("➕ Agregar"):
            if cant > 0 or kg > 0:
                agregar_item(item, cant, kg, "CATÁLOGO")
                st.rerun()

        if st.session_state.lista:
            st.write("### 📋 Tu Pedido Actual")
            st.dataframe(pd.DataFrame(st.session_state.lista), hide_index=True, use_container_width=True)
            if st.button("🚀 CONFIRMAR PEDIDO"):
                if cli and mail and dom:
                    # Lógica de guardado y generación de PDF
                    oid = uuid.uuid4().hex[:6].upper()
                    datos = {"Cliente": cli.upper(), "Domicilio": dom, "Email": mail, "Fecha": fec.strftime("%d/%m/%Y"), 
                             "Horario": f"{h1.strftime('%H:%M')} a {h2.strftime('%H:%M')}", "Detalle": list(st.session_state.lista)}
                    pdf_io = generar_pdf_wc(datos)
                    pedido = {"id": oid, "resumen": datos, "pdf_bytes": pdf_io.getvalue(), "estado": "Nuevo"}
                    st.session_state.pedidos[oid] = pedido
                    st.session_state.ultimo_pedido = pedido
                    st.session_state.pedido_finalizado = True
                    st.session_state.lista = []
                    st.rerun()

def pantalla_estado_pedido():
    st.subheader("🔎 Mi Pedido")
    p = st.session_state.ultimo_pedido
    if p:
        st.write(f"**ID:** {p['id']} | **Estado:** {p['estado']}")
        st.dataframe(pd.DataFrame(p['resumen']['Detalle']), hide_index=True)
        st.download_button("📥 Descargar PDF nuevamente", data=p['pdf_bytes'], file_name=f"Pedido_{p['id']}.pdf")
    else:
        st.warning("No tienes pedidos activos.")

# ==========================================
# 4. LÓGICA DE NAVEGACIÓN Y ADMIN
# ==========================================
configurar_pagina()

# Inicializar Estados
if "nav" not in st.session_state: st.session_state.nav = "Inicio"
if "rol" not in st.session_state: st.session_state.rol = "Cliente"
if "lista" not in st.session_state: st.session_state.lista = []
if "pedidos" not in st.session_state: st.session_state.pedidos = {}
if "ultimo_pedido" not in st.session_state: st.session_state.ultimo_pedido = None
if "pedido_finalizado" not in st.session_state: st.session_state.pedido_finalizado = False

# Botones de Navegación
st.title("🍎 FRUTAS WC")
c_nav = st.columns(4)
if c_nav[0].button("🏠 Inicio", use_container_width=True): st.session_state.nav = "Inicio"
if c_nav[1].button("📖 Nosotros", use_container_width=True): st.session_state.nav = "Nosotros"
if c_nav[2].button("🛒 Crear Pedido", use_container_width=True): st.session_state.nav = "Crear Pedido"
if c_nav[3].button("🔎 Mi Pedido", use_container_width=True): st.session_state.nav = "Estado"

st.divider()

# Switch de Pantallas
if st.session_state.nav == "Inicio":
    pantalla_inicio()
elif st.session_state.nav == "Nosotros":
    pantalla_nosotros()
elif st.session_state.nav == "Crear Pedido":
    pantalla_crear_pedido()
elif st.session_state.nav == "Estado":
    pantalla_estado_pedido()

# Footer / Admin / WhatsApp
st.write("---")
with st.expander("🔒 Panel Admin"):
    # (Aquí va tu lógica de login de admin que ya tienes)
    pass

st.markdown(f'<a class="wa-float" href="https://wa.me/543516422893" target="_blank">💬 WhatsApp</a>', unsafe_allow_html=True)
