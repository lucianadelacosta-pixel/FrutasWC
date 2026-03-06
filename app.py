import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib import colors

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

    # Encabezado
    p.setFont("Helvetica-Bold", 16)
    p.drawString(50, h - 50, "FRUTAS WC - NOTA DE PEDIDO")
    p.setFont("Helvetica", 10)
    p.drawString(50, h - 65, "Distribución Logística de Frescuras en Córdoba")
    p.line(50, h - 70, 550, h - 70)

    # Información del Cliente
    p.setFont("Helvetica-Bold", 12)
    p.drawString(50, h - 100, f"Cliente: {datos_pedido['Cliente']}")
    p.setFont("Helvetica", 11)
    p.drawString(50, h - 115, f"Fecha de Entrega: {datos_pedido['Fecha']}")
    p.drawString(50, h - 130, f"Rango Horario: {datos_pedido['Horario']}")

    # Tabla de Productos
    y = h - 170
    p.setFont("Helvetica-Bold", 11)
    p.drawString(50, y, "Descripción")
    p.drawString(350, y, "Cant. (Bultos)")
    p.drawString(450, y, "Kg.")
    p.line(50, y - 5, 550, y - 5)
    
    y -= 20
    p.setFont("Helvetica", 10)
    for item in datos_pedido['Detalle']:
        p.drawString(50, y, str(item['Descripción']))
        p.drawString(350, y, str(item['Cant.']))
        p.drawString(450, y, str(item['Kg.']))
        y -= 15
        if y < 50: # Nueva página si es muy largo
            p.showPage()
            y = h - 50

    p.showPage()
    p.save()
    buffer.seek(0)
    return buffer

# --- 3. BASE DE DATOS Y ESTADO ---
if 'rol' not in st.session_state: st.session_state.rol = "Cliente"
if 'nav' not in st.session_state: st.session_state.nav = "Inicio"
if 'lista_temporal' not in st.session_state: st.session_state.lista_temporal = []
if 'pedidos_db' not in st.session_state: st.session_state.pedidos_db = []
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
else:
    if c1.button("📊 Pedidos", use_container_width=True): st.session_state.nav = "Resumen"
    if c2.button("⚙️ Actualizar Excel", use_container_width=True): st.session_state.nav = "Precios"
    if c3.button("🚪 Salir", use_container_width=True): 
        st.session_state.rol = "Cliente"
        st.rerun()

st.divider()

# --- 5. SECCIÓN CREAR PEDIDO ---
if st.session_state.nav == "Crear Pedido" and st.session_state.rol == "Cliente":
    st.header("📝 Armá tu Pedido")
    nombre_c = st.text_input("Nombre del Cliente / Negocio")
    
    col_f, col_h1, col_h2 = st.columns([2, 1, 1])
    with col_f:
        fecha_e = st.date_input("Fecha de Entrega", min_value=datetime.now().date() + timedelta(days=1))
    with col_h1: h_desde = st.time_input("Desde", value=datetime.strptime("08:00", "%H:%M"))
    with col_h2: h_hasta = st.time_input("Hasta", value=datetime.strptime("14:00", "%H:%M"))

    st.write("---")
    col_p, col_c, col_k, col_b = st.columns([3, 1, 1, 1])
    with col_p: item_sel = st.selectbox("Buscar producto...", st.session_state.productos_wc)
    with col_c: cant_sel = st.number_input("Bultos", min_value=0, step=1)
    with col_k: kg_sel = st.number_input("Kg.", min_value=0.0, step=0.5)
    with col_b:
        st.write(" ")
        if st.button("➕ Agregar"):
            if cant_sel > 0 or kg_sel > 0:
                st.session_state.lista_temporal.append({"Descripción": item_sel, "Cant.": cant_sel, "Kg.": kg_sel})
                st.rerun()

    if st.session_state.lista_temporal:
        st.write("### Resumen:")
        st.table(pd.DataFrame(st.session_state.lista_temporal))
        
        if st.button("🚀 CONFIRMAR PEDIDO"):
            if nombre_c:
                resumen = {
                    "Cliente": nombre_c, "Fecha": fecha_e.strftime("%d/%m/%Y"),
                    "Horario": f"{h_desde.strftime('%H:%M')} a {h_hasta.strftime('%H:%M')}",
                    "Detalle": st.session_state.lista_temporal
                }
                st.session_state.pedidos_db.append(resumen)
                pdf_fp = generar_pdf(resumen)
                
                st.success("¡Pedido confirmado!")
                st.download_button(
                    label="📥 Descargar Nota de Pedido (PDF)",
                    data=pdf_fp,
                    file_name=f"Pedido_{nombre_c}_{fecha_e}.pdf",
                    mime="application/pdf"
                )
                st.session_state.lista_temporal = []
            else: st.error("Ingresá tu nombre.")

# --- LOGIN ADMIN AL FINAL ---
st.write("---")
if st.session_state.rol == "Cliente":
    with st.expander("🔒 Acceso Administración"):
        u = st.text_input("Usuario")
        p = st.text_input("Contraseña", type="password")
        if st.button("Entrar"):
            if u == "Luciana" and p == "WC2026":
                st.session_state.rol = "Admin"
                st.session_state.nav = "Resumen"
                st.rerun()

wa_link = "https://wa.me/543516422893?text=Consultas%20FRUTAS%20WC"
st.markdown(f'<a href="{wa_link}" class="wa-float" target="_blank">💬 WhatsApp</a>', unsafe_allow_html=True)
