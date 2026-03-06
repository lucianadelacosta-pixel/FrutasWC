import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

# --- 1. CONFIGURACIÓN VISUAL Y FONDO ---
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
        border-radius: 15px;
        padding: 30px;
        max-width: 1000px;
    }
    html, body, [class*="css"] { font-family: "Arial", sans-serif; }
    .wa-float {
        position: fixed; bottom: 20px; right: 20px;
        background-color: #25d366; color: white; border-radius: 50px;
        padding: 12px 20px; display: flex; align-items: center; gap: 10px;
        text-decoration: none; z-index: 100; font-weight: bold;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. BASE DE DATOS E INTERFAZ TIPO EXCEL ---
if 'rol' not in st.session_state: st.session_state.rol = "Cliente"
if 'nav' not in st.session_state: st.session_state.nav = "Inicio"

# Carga inicial del catálogo basado en tu formato de NOTA DE PEDIDO
if 'catalogo_wc' not in st.session_state:
    data = {
        "DETALLE": ["PAPA", "CEBOLLA", "ANCO", "CABUTIA", "ZANAHORIA", "TOMATE", "HUEVOS", "MANZANA", "BANANA", "CARBON"],
        "MEDIDA": ["KG", "KG", "KG", "KG", "KG", "KG", "MAPLE", "KG", "KG", "BOLSA"],
        "CANTIDAD": [0] * 10,
        "PEDIDO_KG_UN": [0.0] * 10
    }
    st.session_state.catalogo_wc = pd.DataFrame(data)

if 'pedidos_db' not in st.session_state:
    st.session_state.pedidos_db = []

# --- 3. NAVEGACIÓN ---
st.title("🍎 FRUTAS WC")
st.write("Distribución logística de frescuras en Córdoba")

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
    if c3.button("🚪 Salir", use_container_width=True): 
        st.session_state.rol = "Cliente"
        st.rerun()

st.divider()

# --- 4. CONTENIDO DINÁMICO ---
if st.session_state.nav == "Inicio":
    st.markdown("#### **Te lo llevamos a casa**")
    st.write("Calidad seleccionada en frutas, verduras, carbón y más.")

elif st.session_state.nav == "Nosotros":
    st.header("Sobre Nosotros")
    st.write("Soy Luciana y en FRUTAS WC nos enfocamos en que recibas lo mejor del campo en tu hogar.")

elif st.session_state.nav == "Crear Pedido":
    st.header("📝 Nota de Pedido WC")
    st.write("Completá las columnas de Cantidad y KG/Un para armar tu pedido:")
    
    # El cliente edita directamente sobre la tabla
    nombre_cliente = st.text_input("Nombre y Apellido del Cliente / Negocio")
    fecha_entrega = st.date_input("Fecha de entrega", min_value=datetime.now().date() + timedelta(days=1))
    
    # Editor de tabla: solo mostramos Detalle, Medida, Cantidad y Pedido_KG_UN
    df_pedido = st.data_editor(
        st.session_state.catalogo_wc,
        column_config={
            "DETALLE": st.column_config.Column("Producto", disabled=True),
            "MEDIDA": st.column_config.Column("Unidad", disabled=True),
            "CANTIDAD": st.column_config.NumberColumn("Cantidad (Bolsas/Bultos)", min_value=0, step=1),
            "PEDIDO_KG_UN": st.column_config.NumberColumn("Total KG / Unidades", min_value=0.0, step=0.5),
        },
        hide_index=True,
        use_container_width=True
    )
    
    if st.button("🚀 Confirmar y Enviar Pedido"):
        if nombre_cliente:
            # Filtramos solo lo que tiene cantidad > 0
            items_pedidos = df_pedido[(df_pedido['CANTIDAD'] > 0) | (df_pedido['PEDIDO_KG_UN'] > 0)]
            if not items_pedidos.empty:
                resumen = {
                    "Cliente": nombre_cliente,
                    "Fecha": fecha_entrega,
                    "Items": items_pedidos.to_dict('records'),
                    "Estado": "Pendiente"
                }
                st.session_state.pedidos_db.append(resumen)
                st.success(f"¡Pedido de {nombre_cliente} registrado! Ya podés cerrar la página.")
            else:
                st.warning("El pedido está vacío.")
        else:
            st.error("Por favor, ingresá tu nombre.")

# --- 5. ACCESO ADMIN (AL FINAL) ---
st.write("---")
with st.expander("🔒 Acceso Administración"):
    u = st.text_input("Usuario")
    p = st.text_input("Contraseña", type="password")
    if st.button("Ingresar"):
        if u == "Luciana" and p == "WC2026":
            st.session_state.rol = "Admin"
            st.session_state.nav = "Resumen"
            st.rerun()

# --- 6. WHATSAPP ---
wa_link = "https://wa.me/543516422893?text=Hola%20Luciana%2C%20tengo%20una%20consulta%20sobre%20mi%20pedido%20en%20FRUTAS%20WC"
st.markdown(f'''
    <a href="{wa_link}" class="wa-float" target="_blank">
        <img src="https://upload.wikimedia.org/wikipedia/commons/6/6b/WhatsApp.svg" width="20" height="20">
        Consultas a nuestro WhatsApp
    </a>
    ''', unsafe_allow_html=True)
