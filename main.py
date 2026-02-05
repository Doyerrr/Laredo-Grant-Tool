import streamlit as st
import pandas as pd
from datetime import datetime

# --- CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(page_title="Salary Forecasting Tool", layout="wide")

st.title("📊 Project 8: Salary & Fringe Cost Forecasting")
st.markdown("Herramienta de estimación para planeación de grants.")

# --- SIDEBAR: CONFIGURACIÓN (TURNKEY ASPECT) ---
st.sidebar.header("Configuraciones Maestras")
cola_rate = st.sidebar.number_input("COLA Rate (%)", value=4.0) / 100
fringe_rate_a = st.sidebar.number_input("Fringe Rate Grade A (%)", value=35.0) / 100
fringe_rate_b = st.sidebar.number_input("Fringe Rate Grade B (%)", value=25.0) / 100

# Diccionario de tasas basado en el grado
fringe_rates = {"Grade A": fringe_rate_a, "Grade B": fringe_rate_b}

# --- ENTRADA DE DATOS DE EMPLEADOS ---
with st.expander("➕ Añadir Nuevo Empleado al Grant", expanded=True):
    col1, col2, col3 = st.columns(3)
    with col1:
        nombre = st.text_input("Nombre del Empleado")
        grado = st.selectbox("Grado del Empleado", ["Grade A", "Grade B"])
    with col2:
        salario_base = st.number_input("Salario Base Anual ($)", value=50000)
        fte = st.slider("FTE (Dedicación)", 0.0, 1.0, 1.0)
    with col3:
        fecha_inicio = st.date_input("Fecha Inicio Grant")
        fecha_fin = st.date_input("Fecha Fin Grant")

# --- LÓGICA DE CÁLCULO ---
def calcular_presupuesto():
    # Calcular meses (pro-rating)
    delta = fecha_fin - fecha_inicio
    months = delta.days / 30.44  # Promedio de días al mes
    
    # Aplicar COLA
    salario_ajustado = salario_base * (1 + cola_rate)
    
    # Costo Salarial
    salary_cost = (salario_ajustado / 12) * months * fte
    
    # Costo Fringe
    fringe_cost = salary_cost * fringe_rates[grado]
    
    return round(salary_cost, 2), round(fringe_cost, 2), round(salary_cost + fringe_cost, 2)

# --- MOSTRAR RESULTADOS ---
if st.button("Calcular Estimación"):
    s_cost, f_cost, total = calcular_presupuesto()
    
    st.divider()
    res_col1, res_col2, res_col3 = st.columns(3)
    res_col1.metric("Costo Salarial", f"${s_cost:,}")
    res_col2.metric("Costo Fringe", f"${f_cost:,}")
    res_col3.metric("Total del Grant", f"${total:,}", delta_color="normal")
    
    # Crear un DataFrame para simular la tabla que se exportará
    data = {
        "Empleado": [nombre],
        "Grado": [grado],
        "FTE": [fte],
        "Salario Estimado": [s_cost],
        "Fringe Estimado": [f_cost],
        "Total": [total]
    }
    df = pd.DataFrame(data)
    st.table(df)
    
    # Botón para descargar (Simulado para el MVP)
    st.download_button("📥 Exportar a Excel", data=df.to_csv().encode('utf-8'), file_name="forecast.csv", mime="text/csv")