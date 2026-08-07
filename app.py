import streamlit as st
import pandas as pd
from datetime import datetime
import base64
import os

st.set_page_config(
    page_title="Attendance Mispunch & Repeated Defaulter Intelligence", 
    layout="wide"
)

# --- Background Image & Hide Default Menu ---
def add_bg_from_local(image_file):
    try:
        with open(image_file, "rb") as file:
            encoded_string = base64.b64encode(file.read()).decode()
        st.markdown(
        f"""
        <style>
        .stApp {{
            background-image: url(data:image/jpeg;base64,{encoded_string});
            background-size: cover;
            background-position: center;
        }}
        </style>
        """,
        unsafe_allow_html=True
        )
    except Exception as e:
        pass 

add_bg_from_local('bg.jpeg.jpeg')

# --- CSS Styles (Original Block Design & Blue Borders) ---
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    footer {visibility: hidden;}
    
    [data-testid="stFileUploadDropzone"] {
        border: 2px dashed #0061ff !important;
        background-color: rgba(255, 255, 255, 0.7);
        border-radius: 10px;
        padding: 20px;
    }
    
    /* Solid Block Design */
    .metric-card { 
        padding: 22px; 
        border-radius: 12px; 
        color: white; 
        box-shadow: 0 4px 12px rgba(0,0,0,0.15); 
        margin-bottom: 20px;
    }
    .card-blue { background: #0061ff; } /* Original Block Colors */
    .card-orange { background: #f5af19; }
    .card-purple { background: #8e2de2; }
    .card-green { background: #11998e; }
    
    .card-title { font-size: 18px; font-weight: 600; margin-bottom: 10px; }
    .card-value { font-size: 38px; font-weight: 800; }
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

with input_col1:
    st.markdown("##### 📥 Manual File Upload")
    uploaded_manual_file = st.file_uploader("Upload file", type=["xlsx", "xls", "csv"], label_visibility="collapsed")
    if uploaded_manual_file: attendance_file = uploaded_manual_file

with input_col2:
    st.markdown("##### 📅 Calendar Auto-Fetch")
    selected_calendar_date = st.date_input("Select date", datetime.now(), label_visibility="collapsed")
    date_str = selected_calendar_date.strftime("%Y-%m-%d")
    
    file_path = f"{date_str}.xlsx.xlsx"
    
    if not uploaded_manual_file:
        if os.path.exists(file_path):
            attendance_file = file_path
            st.success(f"✅ Auto-fetched: {file_path}")
        else:
            st.warning(f"⚠️ File '{file_path}' not found in the main repository folder.")

# --- Processing Logic & Block Design ---
if attendance_file:
    try:
        file_name = attendance_file if isinstance(attendance_file, str) else attendance_file.name
        if file_name.endswith('.csv'):
            att_df = pd.read_csv(attendance_file)
        else:
            att_df = pd.read_excel(attendance_file)
            
        st.markdown("---")
        
        # ----- METRICS CALCULATIONS -----
        # Note: In variables ko apni sheet ke column names ke mutabiq theek kar lein
        total_records = len(att_df)
        
        # Misaal ke tor par, agar "Status" column mein Mispunch likha hai:
        # mispunches_count = len(att_df[att_df['Status'].astype(str).str.contains('Mispunch', case=False, na=False)])
        mispunches_count = 0 # Apni calculation yahan dalein
        
        pending_items_count = 0 # Apni calculation yahan dalein
        
        # 7 Hrs Defaulters count ID ki list se check kar ke:
        # defaulters_count = len(att_df[att_df['Employee ID'].astype(str).isin(manual_ids_list)])
        defaulters_count = 0 # Apni calculation yahan dalein
        
        # ----- TILES / CARDS LAYOUT -----
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.markdown(f'''
                <div class="metric-card card-blue">
                    <div class="card-title">Total Records</div>
                    <div class="card-value">{total_records}</div>
                </div>
            ''', unsafe_allow_html=True)
            
        with col2:
            st.markdown(f'''
                <div class="metric-card card-orange">
                    <div class="card-title">Pending Items</div>
                    <div class="card-value">{pending_items_count}</div>
                </div>
            ''', unsafe_allow_html=True)
            
        with col3:
            st.markdown(f'''
                <div class="metric-card card-purple">
                    <div class="card-title">Mispunches</div>
                    <div class="card-value">{mispunches_count}</div>
                </div>
            ''', unsafe_allow_html=True)
            
        with col4:
            st.markdown(f'''
                <div class="metric-card card-green">
                    <div class="card-title">7-Hrs Defaulters</div>
                    <div class="card-value">{defaulters_count}</div>
                </div>
            ''', unsafe_allow_html=True)
            
        st.markdown("#### 📋 Detailed Data (By Agency & Shift)")
        st.dataframe(att_df, use_container_width=True)
        
    except Exception as e:
        st.error(f"Error processing file: {e}")
