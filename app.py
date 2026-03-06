import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

# --- 1. CONFIGURACIÓN VISUAL Y ESTILO ---
st.set_page_config(page_title="FRUTAS WC", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
    <style>
    /* Ocultar barra lateral predeterminada */
    [data-testid="stSidebar"] {display: none;}
    
    /* Fondo de pantalla con tu imagen fondo.jpg */
    .stApp {
        background-image: url("app/static/fondo.jpg"); 
        background-size: cover;
        background-position: center bottom;
        background-attachment: fixed;
    }
    
    /* Contenedor de contenido con transparencia para que se vea el fondo */
    .main .block-container {
        background-color: rgba(255, 255, 255, 0.96);
        border-radius: 15px;
        padding: 30px;
        max-width: 950px;
        box-shadow: 0px 4px 15px rgba(0,0,0,0.1);
        margin-top: 20px;
    }
    
    html, body, [class*="css"] { font-family: "Arial", sans-serif; }
    
    /* Botón flotante de WhatsApp estilo WC */
    .wa-float {
        position: fixed; bottom: 20px; right: 20px;
        background-color: #25d366; color: white; border-radius: 50px;
        padding: 12px 20px; display: flex; align-items: center; gap: 10px;
        text-decoration: none; z-index: 100; font-weight: bold;
        box-shadow: 2px 2px 10px rgba(0,0,0,0.3);
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. BASE DE DATOS Y ESTADO DE SESIÓN ---
if 'rol' not in st.session_state: st.session_state.rol = "Cliente"
if 'nav' not in st.session_state: st.session_state.nav = "Inicio"
if 'lista_temporal' not in st.session_state: st.session_state.lista_temporal = []
if 'pedidos_db' not in st.session_state: st.session_state.pedidos_db = []

# Lista de productos inicial (se actualiza automáticamente al subir tu Excel en el panel Admin)
if 'productos_wc' not in st.session_state:
    st.session_state.productos_wc = [
        "Acelga", "Anco", "Banana", "Batata", "Cebolla", "Huevos", 
        "Manzana", "Naranja", "Papa", "Pimiento", "Tomate", "Zanahoria"
    ]

# --- 3. NAVEGACIÓN PRINCIPAL (BOTONES DIRECTOS) ---
st.title("🍎 FRUTAS WC")

if st.session_state.rol == "Cliente":
    c1, c2, c3, c4 = st.columns(4)
    if c1.button("🏠 Inicio", use_container_width=True): st.session_state.nav = "Inicio"
    if c2.button("📖 Nosotros", use_container_width=True
