import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import base64
import os

st.set_page_config(
    page_title="Attendance Mispunch & Repeated Defaulter Intelligence", 
    layout="wide"
)

# --- CSS Styles ---
st.markdown("""
    <style>
    .metric-card { padding: 22px; border-radius: 12px 12px 0 0; color: white; box-shadow: 0 4px 12px rgba(0,0,0,0.15); }
    .card-blue { background: linear-gradient(135deg, #0061ff 0%, #60efff 100%); }
    .card-green { background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%); }
    .card-orange { background: linear-gradient(135deg, #f12711 0%, #f5af19 100%); }
    .card-purple { background: linear-gradient(135deg, #8e2de2 0%, #4a00e0 100%); }
    .card-title { font-size: 16px; font-weight: 600; }
    .card-value { font-size: 36px; font-weight: 800; }
    </style>
""", unsafe_allow_html=True)

st.title("📊 Attendance Mispunch & Repeated Defaulter Intelligence")
st.markdown("---")

# --- Helper Functions ---
def clean_id(val):
    try: return str(int(float(val))).strip()
    except: return str(val).strip().lower()

# --- Sidebar ---
st.sidebar.header("⚙️ Configuration")
seven_hours_default = "205854274, 206247771, 206930332, 206915012, 206065208, 206136723, 206200811, 205853892, 206192237, 206361774, 206348020, 206348027, 206348019, 206368537, 206348026, 206348045, 206348030, 206348048, 206348049, 206348041, 206368538, 206348029, 206348042, 205845552, 206348052, 206348054, 203875181, 203875184, 203875092, 203875089, 203875090, 203875180, 203875183, 112463068, 203875088, 203875091, 203875185, 203875186, 206868000, 206897671, 206897640, 206136735, 205231290, 205252357, 206192232, 206491343, 206128578, 206136722, 205252356, 205252538, 205199356, 206230579, 206491328, 206240253, 206930331, 206868288, 206897649, 206868005, 206239524, 206136718"
manual_7_ids = st.sidebar.text_area("7-Hour Employee IDs", value=seven_hours_default)
manual_ids_list = [clean_id(x) for x in manual_7_ids.split(',')] if manual_7_ids else []

# --- Layout ---
input_col1, input_col2 = st.columns(2)
attendance_file = None
active_date = datetime.now()

# --- Input Sections ---
with input_col1:
    st.markdown("##### 📥 Manual File Upload")
    uploaded_manual_file = st.file_uploader("Upload file", type=["xlsx", "xls", "csv"], label_visibility="collapsed")
    if uploaded_manual_file: attendance_file = uploaded_manual_file

with input_col2:
    st.markdown("##### 📅 Calendar Auto-Fetch from `daily_files`")
    selected_calendar_date = st.date_input("Select date", datetime.now(), label_visibility="collapsed")
    active_date = selected_calendar_date
    date_str = selected_calendar_date.strftime("%Y-%m-%d")
    
    file_path = os.path.join("daily_files", f"{date_str}.xlsx")
    
    if not uploaded_manual_file:
        if os.path.exists(file_path):
            attendance_file = file_path
            st.success(f"✅ File loaded: {date_str}.xlsx")
        else:
            st.warning(f"⚠️ File for {date_str} not found in 'daily_files' folder.")

# --- Processing Logic ---
if attendance_file:
    try:
        att_df = pd.read_excel(attendance_file) if str(attendance_file).endswith('.xlsx') else pd.read_csv(attendance_file)
        st.write("File processed successfully.")
        # ... (Include your processing logic here)
    except Exception as e:
        st.error(f"Error processing file: {e}")
