import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

# --- 1. CONFIGURACIÓN VISUAL Y FONDO ---
st.set_page_config(page_title="Frutas WLC", layout="wide")

# CSS para fondo de frutas, tipografía y botón WhatsApp
st.markdown("""
    <style>
    .stApp {
        background-image: url("https://img.freepik.com/foto-gratis/composicion-frutas-frescas-limpio_23-2148184644.jpg");
        background-size: cover;
        background-attachment: fixed;
    }
    /* Capa blanca semitransparente para legibilidad */
    .main .block-container {
        background-color: rgba(255, 255, 255, 0.9);
        border-radius: 20px;
        padding: 40px;
        margin-top: 50px;
    }
    html, body, [class*="css"] { font-family: "Arial", sans-serif; }
    
    .wa-float {
        position: fixed;
        bottom: 20px;
        right: 20px;
        background-color: #25d366;
        color: white;
        border-radius: 50px;
        padding: 10px 20px;
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

# --- 2. BASE DE DATOS ---
if 'pedidos' not in st.session_state:
    st.session_state.pedidos = pd.DataFrame(columns=["ID", "Cliente", "Producto", "Cantidad", "Fecha_Entrega", "Estado"])

if 'catalogo' not in st.session_state:
    st.session_state.catalogo = pd.DataFrame({
        "Producto": ["Manzana", "Papa", "Especias", "Carbón", "Huevos"],
        "Precio": [1200, 800, 450, 3500, 5200]
    })

# --- 3. BARRA LATERAL: NAVEGACIÓN Y ROLES ---
st.sidebar.title("Navegación")
rol = st.sidebar.radio("Tipo de Usuario", ["Cliente", "Administración (Luciana)"])

if rol == "Cliente":
    menu = st.sidebar.selectbox("Ir a:", ["Inicio", "Nosotros", "Crear Pedido", "Estado de mi Pedido"])
else:
    menu = st.sidebar.selectbox("Panel Admin:", ["Resumen General", "Actualizar Precios", "Reporte Proveedores"])

# --- 4. SECCIONES CLIENTE ---
if menu == "Inicio":
    st.title("🍎 Frutas WLC")
    st.subheader("Distribución Logística de Frescuras en Córdoba")
    st.markdown("### **Te lo llevamos a casa**")
    st.write("Calidad seleccionada en frutas, verduras, carbón y más.")

elif menu == "Nosotros":
    st.header("Sobre Nosotros")
    st.write("""
    En **Frutas WLC**, somos especialistas en la cadena de suministro de productos frescos. 
    Nuestra misión es garantizar que la calidad del campo llegue intacta a tu mesa en Córdoba, 
    aplicando procesos logísticos de excelencia para tu comodidad.
    """)

elif menu == "Crear Pedido":
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
            st.success("¡Pedido creado con éxito!")

elif menu == "Estado de mi Pedido":
    st.header("Seguimiento")
    id_ver = st.number_input("Ingresá tu Nro de Pedido", step=1)
    # Lógica de búsqueda aquí

# --- 5. SECCIONES ADMINISTRACIÓN (LUCIANA) ---
elif menu == "Resumen General":
    st.header("📊 Resumen de Todos los Pedidos")
    st.dataframe(st.session_state.pedidos, hide_index=True, use_container_width=True)

elif menu == "Actualizar Precios":
    st.header("⚙️ Gestión de Precios")
    archivo = st.file_uploader("Subir Excel de Precios", type=['xlsx', 'csv'])
    if archivo:
        st.session_state.catalogo = pd.read_excel(archivo) if archivo.name.endswith('.xlsx') else pd.read_csv(archivo)
        st.success("Catálogo actualizado.")

elif menu == "Reporte Proveedores":
    st.header("📦 Compras al Proveedor")
    f_rep = st.date_input("Consolidar para fecha:")
    df_dia = st.session_state.pedidos[st.session_state.pedidos['Fecha_Entrega'] == f_rep]
    if not df_dia.empty:
        rep = df_dia.groupby("Producto")["Cantidad"].sum().reset_index()
        st.dataframe(rep, hide_index=True)

# --- 6. BOTÓN WHATSAPP CON LOGO ---
wa_link = "https://wa.me/543516422893?text=Consultas%20Frutas%20WLC"
st.markdown(f"""
    <a href="{wa_link}" class="wa-float" target="_blank">
        <img src="https://upload.wikimedia.org/wikipedia/commons/6/6b/WhatsApp.svg" width="25" height="25">
        Consultas a nuestro WhatsApp
    </a>
    """, unsafe_allow_html=True)
    st.dataframe(st.session_state.pedidos, hide_index=True, use_container_width=True)

# --- 5. BOTÓN WHATSAPP ---
wa_url = "https://wa.me/543516422893?text=Hola%20Frutas%20WLC%20quisiera%20consultar%20por%20un%20pedido"
st.markdown(f'<a href="{wa_url}" class="whatsapp-button" target="_blank">💬 Pedir por WhatsApp</a>', unsafe_allow_html=True)
