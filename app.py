import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

# --- 1. CONFIGURACIÓN VISUAL ---
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
        border-radius: 15px; padding: 30px; max-width: 950px;
    }
    .wa-float {
        position: fixed; bottom: 20px; right: 20px;
        background-color: #25d366; color: white; border-radius: 50px;
        padding: 12px 20px; display: flex; align-items: center; gap: 10px;
        text-decoration: none; z-index: 100; font-weight: bold;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. FUNCIÓN PARA GENERAR EL PDF ---
def generar_pdf(datos_pedido):
    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=A4)
    w, h = A4

    p.setFont("Helvetica-Bold", 16)
    p.drawString(50, h - 50, "FRUTAS WC - NOTA DE PEDIDO")
    p.setFont("Helvetica", 10)
    p.drawString(50, h - 65, "Contacto: 351 6351605 | Correo: frutasyverduraswc@gmail.com")
    p.line(50, h - 70, 550, h - 70)

    p.setFont("Helvetica-Bold", 12)
    p.drawString(50, h - 100, f"Cliente: {datos_pedido['Cliente']}")
    p.setFont("Helvetica", 11)
    p.drawString(50, h - 115, f"Fecha de Entrega: {datos_pedido['Fecha']}")
    p.drawString(50, h - 130, f"Rango Horario: {datos_pedido['Horario']}")

    y = h - 170
    p.setFont("Helvetica-Bold", 11)
    p.drawString(50, y, "Descripción")
    p.drawString(250, y, "Cant.")
    p.drawString(320, y, "Kg.")
    p.drawString(400, y, "Tipo")
    p.line(50, y - 5, 550, y - 5)
    
    y -= 20
    p.setFont("Helvetica", 10)
    for item in datos_pedido['Detalle']:
        p.drawString(50, y, str(item['Descripción']))
        p.drawString(250, y, str(item['Cant.']))
        p.drawString(320, y, str(item['Kg.']))
        p.drawString(400, y, str(item['Tipo']))
        y -= 15
        if y < 50:
            p.showPage()
            y = h - 50

    p.showPage()
    p.save()
    buffer.seek(0)
    return buffer

# --- 3. ESTADO DE SESIÓN ---
if 'nav' not in st.session_state: st.session_state.nav = "Inicio"
if 'rol' not in st.session_state: st.session_state.rol = "Cliente"
if 'lista_temporal' not in st.session_state: st.session_state.lista_temporal = []
if 'productos_wc' not in st.session_state:
    st.session_state.productos_wc = ["Acelga", "Anco", "Banana", "Cebolla", "Huevos", "Papa", "Tomate"]

# --- 4. NAVEGACIÓN ---
st.title("🍎 FRUTAS WC")
c1, c2, c3, c4 = st.columns(4)
if st.session_state.rol == "Cliente":
    if c1.button("🏠 Inicio", use_container_width=True): st.session_state.nav = "Inicio"
    if c2.button("📖 Nosotros", use_container_width=True): st.session_state.nav = "Nosotros"
    if c3.button("🛒 Crear Pedido", use_container_width=True): st.session_state.nav = "Crear Pedido"
    if c4.button("🔎 Mi Pedido", use_container_width=True): st.session_state.nav = "Estado"

st.divider()

# --- 5. SECCIÓN CREAR PEDIDO ---
if st.session_state.nav == "Crear Pedido":
    st.header("🛒 Armá tu Pedido")
    
    # Datos iniciales
    nombre_c = st.text_input("Nombre del Cliente / Negocio")
    col_f, col_h1, col_h2 = st.columns([2, 1, 1])
    with col_f:
        fecha_e = st.date_input("Fecha de Entrega", min_value=datetime.now().date() + timedelta(days=1))
    with col_h1: h_desde = st.time_input("Desde", value=datetime.strptime("08:00", "%H:%M"))
    with col_h2: h_hasta = st.time_input("Hasta", value=datetime.strptime("14:00", "%H:%M"))

    st.write("---")
    
    # PARTE 1: SELECCIÓN DE CATÁLOGO (LISTA DESPLEGABLE)
    st.subheader("1. Seleccioná de la lista")
    col_p, col_c, col_k, col_b = st.columns([3, 1, 1, 1])
    with col_p: 
        item_sel = st.selectbox("Escribí para buscar producto...", st.session_state.productos_wc)
    with col_c: 
        cant_sel = st.number_input("Cant. (Bultos)", min_value=0, step=1, key="c_main")
    with col_k: 
        kg_sel = st.number_input("Kg.", min_value=0.0, step=0.5, key="k_main")
    with col_b:
        st.write(" ") # Espaciador
        if st.button("➕ Agregar"):
            if cant_sel > 0 or kg_sel > 0:
                st.session_state.lista_temporal.append({
                    "Descripción": item_sel, "Cant.": cant_sel, "Kg.": kg_sel, "Tipo": "Catálogo"
                })
                st.rerun()

    # PARTE 2: TU PEDIDO ACTUAL (JUSTO DEBAJO)
    if st.session_state.lista_temporal:
        st.write("### 📋 Tu Pedido Actual")
        st.dataframe(pd.DataFrame(st.session_state.lista_temporal), hide_index=True, use_container_width=True)
        if st.button("🗑️ Borrar último ítem"):
            st.session_state.lista_temporal.pop()
            st.rerun()
        st.write("---")

    # PARTE 3: AGREGAR PRODUCTO ESPECIAL (AL FINAL)
    with st.expander("➕ Agregar producto que NO está en la lista"):
        col_n1, col_n2, col_n3, col_n4 = st.columns([3, 1, 1, 1])
        with col_n1: 
            o_nom = st.text_input("Nombre del producto especial")
        with col_n2: 
            o_can = st.number_input("Cant.", min_value=0, step=1, key="o_c")
        with col_n3: 
            o_kg = st.number_input("Kg.", min_value=0.0, step=0.5, key="o_k")
        with col_n4:
