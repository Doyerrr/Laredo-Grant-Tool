import streamlit as st
import sqlite3
import pandas as pd
import hashlib
import io
from datetime import datetime

# 1. --- DATABASE CONFIGURATION (Persistence & Security) ---
def init_db():
    conn = sqlite3.connect('laredo_vault.db')
    c = conn.cursor()
    # User table for authentication
    c.execute('''CREATE TABLE IF NOT EXISTS users 
                 (username TEXT PRIMARY KEY, password TEXT)''')
    # Default admin user (Password: laredo123)
    hashed_pw = hashlib.sha256("laredo123".encode()).hexdigest()
    c.execute("INSERT OR IGNORE INTO users VALUES (?, ?)", ('admin', hashed_pw))
    conn.commit()
    conn.close()

init_db()

# 2. --- SESSION MANAGEMENT & LOGIN ---
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False

if not st.session_state['logged_in']:
    st.set_page_config(page_title="Laredo - Login", page_icon="🔐")
    st.title("🔐 Payroll System Access")
    st.markdown("### Project 8: City of Laredo Grant Planning")
    
    user_input = st.text_input("Username")
    pw_input = st.text_input("Password", type="password")
    
    if st.button("Login"):
        hashed_attempt = hashlib.sha256(pw_input.encode()).hexdigest()
        conn = sqlite3.connect('laredo_vault.db')
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE username = ? AND password = ?", (user_input, hashed_attempt))
        if c.fetchone():
            st.session_state['logged_in'] = True
            st.rerun()
        else:
            st.error("Invalid credentials. Please try again.")
else:
    # 3. --- MAIN CALCULATOR & BUSINESS LOGIC ---
    st.set_page_config(page_title="Forecasting Tool", page_icon="💰", layout="wide")
    
    # Sidebar for logout and settings
    with st.sidebar:
        if st.button("Logout"):
            st.session_state['logged_in'] = False
            st.rerun()
        
        st.header("⚙️ Settings")
        # Requirement: Configurable cost assumptions
        cola = st.number_input("COLA Rate (%)", value=4.0, step=0.1) / 100
        fringe_a = st.number_input("Fringe Rate Grade A (%)", value=35.0, step=0.1) / 100
        fringe_b = st.number_input("Fringe Rate Grade B (%)", value=25.0, step=0.1) / 100
        fringe_map = {"Grade A": fringe_a, "Grade B": fringe_b}

    st.title("💰 Salary & Fringe Cost Forecasting Tool")
    st.info("Official Grant Planning Tool - City of Laredo, TX")

    # Data Input (Requirement: Grade, FTE, and grant dates)
    st.subheader("📋 Scenario Input")
    col1, col2 = st.columns(2)
    
    with col1:
        emp_name = st.text_input("Employee Name", "Daniel Oyervidez")
        grade = st.selectbox("Employee Grade", ["Grade A", "Grade B"])
        annual_salary = st.number_input("Annual Base Salary ($)", value=60000)

    with col2:
        start_date = st.date_input("Grant Start Date", datetime(2026, 1, 1))
        end_date = st.date_input("Grant End Date", datetime(2026, 12, 31))
        fte = st.slider("FTE (Full-Time Equivalent)", 0.0, 1.0, 1.0)

    # Calculation Logic (Requirement: Support full and partial grant terms)
    total_days = (end_date - start_date).days
    
    if total_days < 0:
        st.error("Error: End date must be after the start date.")
    else:
        # Pro-rated month calculation
        months = total_days / 30.44
        adjusted_salary = annual_salary * (1 + cola)
        salary_cost = (adjusted_salary / 12) * months * fte
        fringe_cost = salary_cost * fringe_map[grade]
        total_estimate = salary_cost + fringe_cost

        # 4. --- RESULTS & EXPORT ---
        st.divider()
        res1, res2, res3 = st.columns(3)
        res1.metric("Salary Cost", f"${salary_cost:,.2f}")
        res2.metric("Fringe Cost", f"${fringe_cost:,.2f}")
        res3.metric("Project Total", f"${total_estimate:,.2f}")

        # Summary Table (Requirement: Generate summary totals)
        summary_df = pd.DataFrame({
            "Description": ["Adjusted Salary", "Fringe Benefits", "Grand Total"],
            "Amount ($)": [round(salary_cost, 2), round(fringe_cost, 2), round(total_estimate, 2)]
        })
        st.table(summary_df)

        # Excel Generation (Requirement: Export results to Excel)
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
            summary_df.to_excel(writer, index=False, sheet_name='Grant_Forecast')
            # Formatting (Optional but professional)
            workbook  = writer.book
            worksheet = writer.sheets['Grant_Forecast']
            money_fmt = workbook.add_format({'num_format': '$#,##0.00'})
            worksheet.set_column('B:B', 20, money_fmt)
        
        st.download_button(
            label="📥 Download Excel Report (.xlsx)",
            data=buffer.getvalue(),
            file_name=f"Forecast_Report_{emp_name}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )