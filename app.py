import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import io

# --- 1. CONFIGURACIÓN VISUAL Y ESTILO (ARIAL + MINIMALISMO) ---
st.set_page_config(page_title="Frutas WLC - Gestión Logística", layout="wide")

st.markdown("""
    <style>
    html, body, [class*="css"] {
        font-family: "Arial", sans-serif;
    }
    .stButton>button {
        border-radius: 5px;
        background-color: #f0f2f6;
    }
    .whatsapp-button {
        position: fixed;
        bottom: 20px;
        right: 20px;
        background-color: #25d366;
        color: white;
        border-radius: 50px;
        padding: 15px 25px;
        font-weight: bold;
        text-decoration: none;
        z-index: 100;
        box-shadow: 2px 2px 10px rgba(0,0,0,0.2);
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. GESTIÓN DE DATOS (BASE DE DATOS SIMULADA) ---
if 'pedidos' not in st.session_state:
    st.session_state.pedidos = pd.DataFrame(columns=[
        "ID", "Cliente", "Producto", "Cantidad", "Unidad", "Fecha_Entrega", "Estado"
    ])

if 'catalogo' not in st.session_state:
    st.session_state.catalogo = pd.DataFrame({
        "Producto": ["Manzana", "Papa", "Especias", "Carbón", "Huevos"],
        "Unidad": ["Kg", "Kg", "100g", "Bolsa 10kg", "Maple x30"],
        "Precio": [1200, 800, 450, 3500, 5200]
    })

# --- 3. FUNCIONES DE LÓGICA LOGÍSTICA ---
def puede_editar(fecha_entrega):
    hoy = datetime.now().date()
    return (fecha_entrega - hoy).days >= 1

def borrar_datos(fecha_limite, cliente=None):
    df = st.session_state.pedidos
    if cliente:
        mask = ~((df['Fecha_Entrega'] <= fecha_limite) & (df['Cliente'] == cliente))
    else:
        mask = df['Fecha_Entrega'] > fecha_limite
    st.session_state.pedidos = df[mask]

# --- 4. MENÚ LATERAL (ADMINISTRACIÓN) ---
st.sidebar.image("https://img.freepik.com/foto-gratis/composicion-frutas-frescas-limpio_23-2148184644.jpg", use_container_width=True)
st.sidebar.title("Panel de Control")
menu = st.sidebar.radio("Navegación", ["Inicio & Servicios", "Hacer Pedido", "Estado de mi Pedido", "Panel Logístico (WLC)"])

archivo_precios = st.sidebar.file_uploader("Actualizar Precios (Excel/CSV)", type=['csv', 'xlsx'])
if archivo_precios:
    try:
        df_new = pd.read_csv(archivo_precios) if archivo_precios.name.endswith('.csv') else pd.read_excel(archivo_precios)
        st.session_state.catalogo = df_new
        st.sidebar.success("Catálogo actualizado")
    except Exception as e:
        st.sidebar.error("Error al cargar archivo")

# --- 5. SECCIONES DE LA WEB ---

if menu == "Inicio & Servicios":
    st.title("🍎 Frutas WLC")
    st.subheader("Calidad seleccionada y logística de precisión en Córdoba.")
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("### 🚛 Entrega Domiciliaria\nTe lo llevamos a tu casa con la mayor frescura.")
    with col2:
        st.markdown("### 📦 Pedidos Programados\nGestión eficiente para que nunca te falte nada.")
    
    st.divider()
    st.image("https://img.freepik.com/foto-gratis/variedad-frutas-verduras-frescas-aisladas-blanco_1232-4545.jpg", caption="Minimalismo y Frescura WLC")

elif menu == "Hacer Pedido":
    st.header("Realizá tu Pedido")
    st.table(st.session_state.catalogo)
    
    with st.form("form_p"):
        nombre = st.text_input("Nombre y Apellido")
        prod = st.selectbox("Producto", st.session_state.catalogo["Producto"])
        cant = st.number_input("Cantidad", min_value=1)
        fecha = st.date_input("Fecha de entrega", min_value=datetime.now().date() + timedelta(days=1))
        if st.form_submit_button("Confirmar"):
            nuevo = {"ID": len(st.session_state.pedidos)+1, "Cliente": nombre, "Producto": prod, 
                     "Cantidad": cant, "Unidad": "Un/Kg", "Fecha_Entrega": fecha, "Estado": "Pendiente"}
            st.session_state.pedidos = pd.concat([st.session_state.pedidos, pd.DataFrame([nuevo])], ignore_index=True)
            st.success("Pedido registrado correctamente.")

elif menu == "Estado de mi Pedido":
    st.header("Seguimiento")
    id_busq = st.number_input("Nro de Pedido", step=1)
    # Lógica simplificada para el ejemplo
    st.info("Recordá: Los cambios solo se aceptan con más de 24hs de antelación.")

elif menu == "Panel Logístico (WLC)":
    st.header("Gestión Operativa para Norma")
    t1, t2 = st.tabs(["📊 Reporte Proveedor", "🧹 Limpieza"])
    
    with t1:
        f_rep = st.date_input("Consolidar para fecha:")
        df_dia = st.session_state.pedidos[st.session_state.pedidos['Fecha_Entrega'] == f_rep]
        if not df_dia.empty:
            rep = df_dia.groupby("Producto")["Cantidad"].sum().reset_index()
            st.dataframe(rep)
            st.download_button("Descargar Lista de Compra", rep.to_csv(index=False), "compra.csv")
        else:
            st.write("No hay pedidos para esta fecha.")
            
    with t2:
        f_borrar = st.date_input("Borrar hasta:")
        c_borrar = st.text_input("Cliente (opcional)")
        if st.button("Ejecutar Borrado"):
            borrar_datos(f_borrar, c_borrar if c_borrar else None)
            st.success("Limpieza completada.")

# --- 6. BOTÓN FLOTANTE WHATSAPP ---
wa_url = f"https://wa.me/543516422893?text=Hola%20Frutas%20WLC%20quisiera%20consultar%20por%20un%20pedido"
st.markdown(f'<a href="{wa_url}" class="whatsapp-button" target="_blank">💬 Contactar a WLC</a>', unsafe_allow_html=True)
