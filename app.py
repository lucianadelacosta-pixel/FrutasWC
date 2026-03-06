import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

# --- 1. CONFIGURACIÓN VISUAL Y FONDO (PANTALLA COMPLETA) ---
st.set_page_config(page_title="Frutas WC", layout="wide", initial_sidebar_state="collapsed")

# CSS para ocultar el panel lateral por completo y mejorar la estética
st.markdown("""
    <style>
    /* Ocultar botón de menú lateral y el panel */
    [data-testid="stSidebar"] {display: none;}
    [data-testid="stSidebarNav"] {display: none;}
    
    .stApp {
        background-image: url("https://img.freepik.com/foto-gratis/fondo-frutas-verduras-frescas-tonos-verdes-naranjas_1232-4545.jpg");
        background-size: cover;
        background-attachment: fixed;
    }
    .main .block-container {
        background-color: rgba(255, 255, 255, 0.94);
        border-radius: 15px;
        padding: 30px;
        margin-top: 10px;
        max-width: 900px;
    }
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
        box-shadow: 2px 2px 10px rgba(0,0,0,0.3);
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. BASE DE DATOS Y ESTADO DE SESIÓN ---
if 'rol' not in st.session_state: st.session_state.rol = "Cliente"
if 'nav' not in st.session_state: st.session_state.nav = "Inicio"
if 'pedidos' not in st.session_state:
    st.session_state.pedidos = pd.DataFrame(columns=["ID", "Cliente", "Producto", "Cantidad", "Fecha_Entrega", "Estado"])
if 'catalogo' not in st.session_state:
    st.session_state.catalogo = pd.DataFrame({
        "Producto": ["Manzana", "Papa", "Especias", "Carbón", "Huevos"],
        "Precio": [1200, 800, 450, 3500, 5200]
    })

# --- 3. NAVEGACIÓN PRINCIPAL (CLIENTE O ADMIN) ---
st.title("🍎 Frutas WC")

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
if st.session_state.rol == "Cliente":
    if st.session_state.nav == "Inicio":
        st.subheader("Distribución Logística de Frescuras en Córdoba")
        st.markdown("#### **Te lo llevamos a casa**")
        st.write("Calidad seleccionada en frutas, verduras, carbón y más.")
    
    elif st.session_state.nav == "Nosotros":
        st.header("Sobre Nosotros")
        st.write("Somos Luciana y el equipo de Frutas WLC. Llevamos frescura con eficiencia logística.")

    elif st.session_state.nav == "Crear Pedido":
        st.header("Realizá tu Pedido")
        st.dataframe(st.session_state.catalogo, hide_index=True, use_container_width=True)
        with st.form("p_cliente"):
            nombre = st.text_input("Tu Nombre")
            prod = st.selectbox("Producto", st.session_state.catalogo["Producto"])
            cant = st.number_input("Cantidad", min_value=1)
            fecha = st.date_input("Fecha de entrega", min_value=datetime.now().date() + timedelta(days=1))
            if st.form_submit_button("Confirmar Pedido"):
                nuevo = {"ID": len(st.session_state.pedidos)+1, "Cliente": nombre, "Producto": prod, 
                         "Cantidad": cant, "Fecha_Entrega": fecha, "Estado": "Pendiente"}
                st.session_state.pedidos = pd.concat([st.session_state.pedidos, pd.DataFrame([nuevo])], ignore_index=True)
                st.success(f"¡Pedido #{len(st.session_state.pedidos)} registrado!")

else: # VISTA ADMINISTRACIÓN (LUCIANA)
    if st.session_state.nav == "Resumen":
        st.header("📊 Resumen de Pedidos")
        st.dataframe(st.session_state.pedidos, hide_index=True, use_container_width=True)
    elif st.session_state.nav == "Precios":
        st.header("⚙️ Actualizar Catálogo")
        st.file_uploader("Subir nuevo Excel", type=['xlsx'])

# --- 5. ACCESO ADMINISTRACIÓN (AL FINAL DE TODO) ---
st.write("---")
with st.expander("🔒 Acceso Administración"):
    u = st.text_input("Usuario")
    p = st.text_input("Contraseña", type="password")
    if st.button("Ingresar como Luciana"):
        if u == "Luciana" and p == "WLC2026":
            st.session_state.rol = "Admin"
            st.session_state.nav = "Resumen"
            st.rerun()
        else:
            st.error("Datos incorrectos")

# --- 6. WHATSAPP FLOTANTE ---
wa_link = "https://wa.me/543516422893?text=Consultas%20Frutas%20WLC"
st.markdown(f"""
    <a href="{wa_link}" class="wa-float" target="_blank">
        <img src="https://upload.wikimedia.org/wikipedia/commons/6/6b/WhatsApp.svg" width="20" height="20">
        Consultas a nuestro WhatsApp
    </a>
    """, unsafe_allow_html=True)
