import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

# --- 1. CONFIGURACIÓN VISUAL Y FONDO (PANTALLA COMPLETA) ---
st.set_page_config(page_title="Frutas WLC", layout="wide", initial_sidebar_state="collapsed")

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
st.title("🍎 Frutas W
