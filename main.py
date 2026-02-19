import streamlit as st
import sqlite3
import pandas as pd
import hashlib
import io
import os
from datetime import datetime

# --- CONFIGURACIÓN DE DATOS (Basado en el correo de la Ciudad de Laredo) ---
COSTOS_MEDICOS = {
    "S - Employee Only": 350.00,
    "SP - Spouse + Employee": 700.00,
    "CH - Child + Employee": 600.00,
    "F - Family": 950.00
}
COSTOS_DENTALES = {
    "S - Employee Only": 25.00,
    "DD - Dental Dependent": 55.00
}

# Nombre del archivo que debes tener en tu carpeta
LAREDO_LOGO = "laredo_logo.png"

# 1. --- DATABASE (Security & Persistence) ---
def init_db():
    conn = sqlite3.connect('laredo_vault.db')
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, password TEXT)')
    hashed_pw = hashlib.sha256("laredo123".encode()).hexdigest()
    c.execute("INSERT OR IGNORE INTO users VALUES (?, ?)", ('admin', hashed_pw))
    conn.commit()
    conn.close()

init_db()

# --- CUSTOM CSS (Laredo Professional Theme) ---
def apply_style():
    st.markdown(f"""
        <style>
        .stApp {{ background-color: #F8F9FA; }}
        [data-testid="stSidebar"] {{ background-color: #002855; color: white; }}
        [data-testid="stSidebar"] * {{ color: white !important; }}
        .stButton>button {{ 
            background-color: #002855; color: white; border-radius: 8px; 
            width: 100%; border: 2px solid #8B734B; font-weight: bold;
        }}
        .stButton>button:hover {{ background-color: #8B734B; border: 2px solid #002855; }}
        h1, h2, h3 {{ color: #002855; }}
        .metric-card {{
            background-color: white; padding: 20px; border-radius: 10px;
            box-shadow: 2px 2px 10px rgba(0,0,0,0.1); border-left: 5px solid #8B734B;
        }}
        </style>
    """, unsafe_allow_html=True)

# 2. --- LOGIN MANAGEMENT ---
if 'auth' not in st.session_state:
    st.session_state['auth'] = False

if not st.session_state['auth']:
    st.set_page_config(page_title="Laredo - Login", page_icon="🔐")
    apply_style()
    
    col_log1, col_log2, col_log3 = st.columns([1,2,1])
    with col_log2:
        if os.path.exists(LAREDO_LOGO):
            st.image(LAREDO_LOGO, use_container_width=True)
        st.title("Grant Forecasting Login")
        u = st.text_input("Username")
        p = st.text_input("Password", type="password")
        if st.button("Access Portal"):
            hp = hashlib.sha256(p.encode()).hexdigest()
            conn = sqlite3.connect('laredo_vault.db')
            res = conn.execute("SELECT * FROM users WHERE username=? AND password=?", (u, hp)).fetchone()
            if res:
                st.session_state['auth'] = True
                st.rerun()
            else: st.error("Invalid Credentials")
else:
    # 3. --- MAIN INTERFACE ---
    st.set_page_config(page_title="City of Laredo Grant Tool", layout="wide")
    apply_style()
    
    with st.sidebar:
        if os.path.exists(LAREDO_LOGO):
            st.image(LAREDO_LOGO, use_container_width=True)
        st.write("---")
        if st.button("Log Out"):
            st.session_state['auth'] = False
            st.rerun()
        st.header("Assumptions")
        cola = st.number_input("COLA (%)", value=4.0) / 100
        tax_rate = st.number_input("Taxes/Other Fringe (%)", value=7.65) / 100

    # Header with Logo
    head1, head2 = st.columns([1, 4])
    with head1:
        if os.path.exists(LAREDO_LOGO):
            st.image(LAREDO_LOGO, width=150)
    with head2:
        st.title("Salary & Fringe Forecasting Tool")
        st.markdown("#### Official Project 8 Portal - City of Laredo, TX")

    st.divider()

    # Data Input
    col_a, col_b = st.columns(2)
    with col_a:
        st.subheader("👤 Employee Information")
        name = st.text_input("Employee Name", "Aaron Blake")
        salary = st.number_input("Annual Salary ($)", value=55000)
        fte = st.slider("FTE (Allocation)", 0.0, 1.0, 1.0)
        start = st.date_input("Grant Start Date", datetime(2026, 1, 1))
        end = st.date_input("Grant End Date", datetime(2026, 12, 31))

    with col_b:
        st.subheader("🛡️ Benefits (Alejandra's Logic)")
        ins_type = st.radio("Insurance Type", ["R - Regular & HMO", "C - CDHP"])
        med_cover = st.selectbox("Medical Cover Type", list(COSTOS_MEDICOS.keys()))
        den_cover = st.selectbox("Dental Cover Type", list(COSTOS_DENTALES.keys()))
        
        # Coding Logic: Extraction of codes like 'CH' and 'DD'
        med_code = med_cover.split(" - ")[0]
        den_code = den_cover.split(" - ")[0]
        combined_code = med_code + den_code
        st.success(f"Generated Insurance Code: **{combined_code}**")

    # --- CALCULATIONS ---
    days = (end - start).days
    pay_periods = days / 14 # Calculation based on bi-weekly periods
    
    if days > 0:
        # Adjusted salary logic
        sal_per_period = ((salary * (1 + cola)) / 26) * fte
        total_sal_grant = sal_per_period * pay_periods
        
        # Benefits logic from master spreadsheet
        med_total = COSTOS_MEDICOS[med_cover] * pay_periods
        den_total = COSTOS_DENTALES[den_cover] * pay_periods
        other_fringe = total_sal_grant * tax_rate
        grand_total = total_sal_grant + med_total + den_total + other_fringe
        
        # Dashboard Visuals
        st.write("---")
        r1, r2, r3, r4 = st.columns(4)
        r1.metric("Total Salary", f"${total_sal_grant:,.2f}")
        r2.metric("Medical Cost", f"${med_total:,.2f}")
        r3.metric("Dental Cost", f"${den_total:,.2f}")
        r4.metric("Grand Total", f"${grand_total:,.2f}")

        # Summary Dataframe
        df_res = pd.DataFrame({
            "Description": ["Base Salary (+COLA)", "Medical Insurance", "Dental Insurance", "Other Fringe (7.65%)"],
            "Code": ["N/A", med_code, den_code, "TAX"],
            "Total Amount ($)": [total_sal_grant, med_total, den_total, other_fringe]
        })
        st.table(df_res)

        # Excel Export logic
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
            df_res.to_excel(writer, index=False, sheet_name='Laredo_Forecast')
            workbook = writer.book
            worksheet = writer.sheets['Laredo_Forecast']
            money_fmt = workbook.add_format({'num_format': '$#,##0.00'})
            worksheet.set_column('C:C', 20, money_fmt)
        
        st.download_button(
            label="📥 Download Official Excel Report",
            data=buffer.getvalue(),
            file_name=f"Laredo_Report_{name}_{combined_code}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    else:
        st.error("Please verify that the End Date is after the Start Date.")

