import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

# --- 1. CONFIGURACIÓN VISUAL (FONDO: fondo.jpg) ---
st.set_page_config(page_title="Frutas WLC", layout="wide", initial_sidebar_state="collapsed")

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
        background-color: rgba(255, 255, 255, 0.95);
        border-radius: 15px;
        padding: 30px;
        margin-top: 10px;
        max-width: 900px;
        box-shadow: 0px 4px 15px rgba(0,0,0,0.1);
    }
    
    html, body, [class*="css"] { font-family: "Arial", sans-serif; }
    
    .wa-float {
        position: fixed;
        bottom: 20px;
        right: 20px;
        background-color: #25d366;
        color: white;
        border-radius: 50px;
        padding: 12px 20px;
        display: flex;
        align-items: center;
        gap: 10px;
        text-decoration: none;
        z-index: 100;
        font-weight: bold;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. SESIÓN Y DATOS ---
if 'rol' not in st.session_state: st.session_state.rol = "Cliente"
if 'nav' not in st.session_state: st.session_state.nav = "Inicio"
if 'pedidos' not in st.session_state:
    st.session_state.pedidos = pd.DataFrame(columns=["ID", "Cliente", "Producto", "Cantidad", "Fecha_Entrega", "Estado"])
if 'catalogo' not in st.session_state:
    st.session_state.catalogo = pd.DataFrame({
        "Producto": ["Manzana", "Papa", "Especias", "Carbón", "Huevos"],
        "Precio": [1200, 800, 450, 3500, 5200]
    })

# --- 3. TÍTULO Y NAVEGACIÓN PRINCIPAL ---
st.title("🍎 Frutas WLC")
st.write("Distribución logística de frescuras en Córdoba")

# Botones de navegación (Panel directo)
if st.session_state.rol == "Cliente":
    c1, c2, c3, c4 = st.columns(4)
    if c1.button("🏠 Inicio", use_container_width=True): st.session_state.nav = "Inicio"
    if c2.button("📖 Nosotros", use_container_width=True): st.session_state.nav = "Nosotros"
    if c3.button("🛒 Crear Pedido", use_container_width=True): st.session_state.nav = "Crear Pedido"
    if c4.button("🔎 Mi Pedido", use_container_width=True): st.session_state.nav = "Estado"
else:
    c1, c2, c3, c4 = st.columns(4)
    if c1.button("📊 Resumen", use_container_width=True): st.session_state.nav = "Resumen"
    if c2.button("⚙️ Precios", use_container_width=True): st.session_state.nav = "Precios"
    if c3.button("📦 Proveedores", use_container_width=True): st.session_state.nav = "Proveedores"
    if c4.button("🚪 Salir", use_container_width=True): 
        st.session_state.rol = "Cliente"
        st.rerun()

st.divider()

# --- 4. CONTENIDO ---
if st.session_state.nav == "Inicio":
    st.markdown("#### **Te lo llevamos a casa**")
    st.write("Calidad seleccionada en frutas, verduras, carbón y más.")

elif st.session_state.nav == "Nosotros":
    st.header("Sobre Nosotros")
    st.write("Soy Luciana y en Frutas WLC nos enfocamos en que recibas lo mejor del campo en tu hogar.")

elif st.session_state.nav == "Crear Pedido":
    st.header("Realizá tu Pedido")
    st.dataframe(st.session_state.catalogo, hide_index=True, use_container_width=True)
    with st.form("p_cliente"):
        nombre = st.text_input("Nombre")
        prod = st.selectbox("Producto", st.session_state.catalogo["Producto"])
        cant = st.number_input("Cantidad", min_value=1)
        fecha = st.date_input("Fecha de entrega", min_value=datetime.now().date() + timedelta(days=1))
        if st.form_submit_button("Confirmar"):
            st.success("¡Pedido registrado!")

# --- 5. LOGIN ADMIN (AL FINAL) ---
st.write("---")
with st.expander("🔒 Acceso Administración"):
    u = st.text_input("Usuario")
    p = st.text_input("Contraseña", type="password")
    if st.button("Ingresar"):
        if u == "Luciana" and p == "WLC2026":
            st.session_state.rol = "Admin"
            st.session_state.nav = "Resumen"
            st.rerun()
        else:
            st.error("Acceso denegado")

# --- 6. WHATSAPP ---
wa_link = "https://wa.me/543516422893?text=Consultas%20Frutas%20WLC"
st.markdown(f'<a href="{wa_link}" class="wa-float" target="_blank">💬 WhatsApp</a>', unsafe_allow_html=True)
