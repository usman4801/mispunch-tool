import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import base64

# Page Config
st.set_page_config(
    page_title="Attendance Mispunch & Repeated Defaulter Intelligence", 
    layout="wide"
)

# Function to encode PNG image file
def get_base64_of_bin_file(bin_file):
    with open(bin_file, 'rb') as f:
        data = f.read()
    return base64.b64encode(data).decode()

image_filename = 'bg.png' # Yahan apni nayi PNG file ka naam likhein

try:
    bin_str = get_base64_of_bin_file(image_filename)
    st.markdown(
        f"""
        <style>
        /* PROPERLY HIDE STREAMLIT TOP BAR, DECORATION & FOOTER */
        #MainMenu {{visibility: hidden !important;}}
        header {{visibility: hidden !important; display: none !important;}}
        footer {{visibility: hidden !important;}}
        .stDecoration {{display: none !important;}}

        .stApp {{
            background-image: url("data:image/png;base64,{bin_str}");
            background-size: cover;
            background-position: center;
            background-repeat: no-repeat;
            background-attachment: fixed;
        }}
        .block-container {{
            background-color: rgba(255, 255, 255, 0.92); /* Container ko white rakha hai taake text readable rahe */
            padding: 2rem;
            border-radius: 12px;
            margin-top: 1.0rem;
            box-shadow: 0px 4px 15px rgba(0, 0, 0, 0.1);
        }}
        
        /* WAREHOUSE BOX CUSTOM STYLING */
        div[data-baseweb="select"] {{
            border: 2px solid #000000 !important;
            border-radius: 6px !important;
            background-color: #ffffff !important;
            font-weight: bold !important;
        }}
        div[data-testid="stSelectbox"] label p {{
            font-size: 18px !important;
            font-weight: 800 !important;
            color: #000000 !important;
        }}

        div[data-testid="stDataFrame"] th {{
            white-space: pre-wrap !important;
            word-wrap: break-word !important;
        }}

        /* STYLISH COLORFUL FILE UPLOADER BOX WITH EXCEL ICON */
        div[data-testid="stFileUploader"] {{
            position: relative;
            background: linear-gradient(90deg, rgba(0, 97, 255, 0.04) 0%, rgba(96, 239, 255, 0.12) 50%, rgba(142, 45, 226, 0.06) 100%);
            border: 2px dashed #3b82f6 !important;
            padding: 18px !important;
            border-radius: 12px !important;
            box-shadow: 0 4px 15px rgba(0, 97, 255, 0.08);
            transition: all 0.3s ease;
        }}
        
        /* EXCEL ICON INJECTION ON RIGHT SIDE */
        div[data-testid="stFileUploader"]::after {{
            content: "";
            position: absolute;
            right: 25px;
            top: 50%;
            transform: translateY(-50%);
            width: 50px;
            height: 50px;
            background-image: url('data:image/svg+xml;utf8,<svg width="64" height="64" viewBox="0 0 64 64" xmlns="http://www.w3.org/2000/svg"><path d="M16 4h20l12 12v40a4 4 0 0 1-4 4H16a4 4 0 0 1-4-4V8a4 4 0 0 1 4-4z" fill="%23f8fafc" stroke="%2394a3b8" stroke-width="2"/><path d="M36 4v12h12" fill="none" stroke="%2394a3b8" stroke-width="2" stroke-linejoin="round"/><rect x="18" y="26" width="28" height="18" rx="2" fill="%2322c55e"/><path d="M18 32h28M18 38h28M27 26v18M37 26v18" stroke="%23fff" stroke-width="2"/><rect x="32" y="42" width="28" height="16" rx="4" fill="%238b5cf6"/><text x="46" y="53.5" fill="%23fff" font-size="11" font-family="sans-serif" font-weight="bold" text-anchor="middle">XLSX</text></svg>');
            background-size: contain;
            background-repeat: no-repeat;
            pointer-events: none;
        }}
        
        div[data-testid="stFileUploader"]:hover {{
            border-color: #8e2de2 !important;
            box-shadow: 0 6px 20px rgba(142, 45, 226, 0.15);
        }}
        div[data-testid="stFileUploader"] section {{
            background-color: transparent !important;
        }}
        div[data-testid="stFileUploader"] label p {{
            font-size: 16px !important;
            font-weight: 700 !important;
            color: #0e1117 !important;
        }}

        /* CUSTOM HEADER STYLING */
        .custom-header-container {{
            display: flex;
            align-items: center;
            gap: 15px;
            margin-bottom: 20px;
            font-family: sans-serif;
        }}
        .custom-icon-box {{
            width: 50px;
            height: 50px;
            background: linear-gradient(135deg, #0061ff 0%, #60efff 100%);
            border-radius: 12px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 24px;
            box-shadow: 0 4px 10px rgba(0,97,255,0.3);
        }}
        .custom-title-text {{
            font-size: 28px;
            font-weight: 800;
            color: #1e1e2f;
            line-height: 1.2;
        }}
        .custom-subtitle-text {{
            font-size: 14px;
            font-weight: 500;
            color: #6c757d;
            margin-top: 2px;
        }}
        </style>
        """,
        unsafe_allow_html=True
    )
except Exception:
    pass

# --- MAIN PAGE COLORFUL HEADER ---
st.markdown("""
    <div class="custom-header-container">
        <div class="custom-icon-box">📊</div>
        <div>
            <div class="custom-title-text">Attendance Mispunch & Repeated Defaulter Intelligence</div>
            <div class="custom-subtitle-text">Real-time insights and system performance overview</div>
        </div>
    </div>
""", unsafe_allow_html=True)

st.markdown("---")

# Warehouse Box
col_wh, col_space = st.columns([1.5, 8.5])
with col_wh:
    selected_warehouse = st.selectbox(
        "Warehouse",
        options=["AUH1", "DXB5", "DXB3"],
        index=0
    )

st.markdown("<br>", unsafe_allow_html=True)

uploaded_file = st.file_uploader("Upload Excel/CSV File", type=["xlsx", "xls", "csv"])

def parse_time(time_val):
    if pd.isna(time_val) or str(time_val).strip().lower() in ["nan", "none", ""]:
        return None
    time_str = str(time_val).strip()
    for fmt in ["%H:%M:%S", "%H:%M", "%I:%M:%S %p", "%I:%M %p", "%I:%M%p"]:
        try:
            return datetime.strptime(time_str, fmt).time()
        except ValueError:
            continue
    return None

def format_time_clean(time_val):
    t = parse_time(time_val)
    if t is not None:
        return t.strftime("%H:%M")
    return ""

def analyze_mispunches(row, punch_cols):
    punches = []
    actual_punch_positions = []
    
    for idx, col in enumerate(punch_cols):
        val = parse_time(row[col])
        if val is not None:
            punches.append(val)
            actual_punch_positions.append(idx)
            
    total_punches = len(punches)
    
    status = "OK"
    category = "Complete"
    working_hours_str = "N/A"
    issue_type = "Clean"
    
    is_last_punch_an_in = False
    if total_punches > 0:
        last_punch_col_index = actual_punch_positions[-1]
        if last_punch_col_index % 2 == 0:
            is_last_punch_an_in = True

    if total_punches % 2 != 0 or is_last_punch_an_in:
        status = "Error"
        working_hours_str = "N/A"
        issue_type = "Mispunch"
        
        if is_last_punch_an_in and total_punches % 2 == 0:
            category = "Shift END is IN (Missing Shift OUT)"
        elif total_punches == 1:
            category = "Single Scan Only"
        elif total_punches == 3:
            category = "Missing Break / Shift IN (3 Punches)"
        elif total_punches == 5:
            category = "Missing Break Return (5 Punches)"
        else:
            category = f"Missing Scan ({total_punches} Punches)"

    elif total_punches >= 7:
        status = "Error"
        working_hours_str = "N/A"
        category = "Extra Punches"
        issue_type = "Mispunch"

    elif total_punches in [2, 4, 6]:
        dummy_date = datetime(2026, 1, 1)
        total_seconds = 0
        
        for i in range(0, total_punches, 2):
            start_dt = datetime.combine(dummy_date, punches[i])
            end_dt = datetime.combine(dummy_date, punches[i+1])
            
            if end_dt < start_dt:
                end_dt += timedelta(days=1)
            
            total_seconds += (end_dt - start_dt).total_seconds()
        
        hours = int(total_seconds // 3600)
        minutes = int((total_seconds % 3600) // 60)
        
        working_hours_str = f"{hours:02d}:{minutes:02d}"
        
        min_allowed_seconds = (8 * 3600) + (50 * 60)
        max_allowed_seconds = (9 * 3600) + (10 * 60)
        
        if total_seconds < min_allowed_seconds:
            status = "Error"
            category = "Short Working Hours (< 08:50)"
            issue_type = "Defaulter Hours"
        elif total_seconds > max_allowed_seconds:
            status = "Error"
            category = "Overtime / Excessive Hours (> 09:10)"
            issue_type = "Defaulter Hours"
        else:
            status = "OK"
            category = "Complete"
            issue_type = "Clean"

    return pd.Series([total_punches, working_hours_str, status, category, issue_type])

if uploaded_file is not None:
    if uploaded_file.name.endswith('.csv'):
        df = pd.read_csv(uploaded_file)
    else:
        df = pd.read_excel(uploaded_file)
        
    col_names = df.columns.tolist()
    
    id_col = col_names[0]
    name_col = col_names[1]
    punch_cols = col_names[4:]
    
    # --- SECTION HEADER WITH ICON STYLE ---
    st.markdown("""
        <div class="custom-header-container" style="margin-top: 20px;">
            <div class="custom-icon-box" style="background: linear-gradient(135deg, #8e2de2 0%, #4a00e0 100%); width: 40px; height: 40px; font-size: 20px;">📋</div>
            <div>
                <div class="custom-title-text" style="font-size: 22px;">Processing Summary & Live Analysis</div>
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    analysis_df = df.apply(lambda row: analyze_mispunches(row, punch_cols), axis=1)
    analysis_df.columns = ['Total Punches', 'No. of\nWorking Hours', 'Status', 'Mispunch Category', 'Issue Type']
    
    renamed_punch_cols = {}
    punches_df_cleaned = pd.DataFrame()
    
    for idx, col in enumerate(punch_cols):
        pair_num = (idx // 2) + 1
        label = "IN" if idx % 2 == 0 else "OUT"
        col_label = label if pair_num == 1 else f"{label} ({pair_num})"
        
        renamed_punch_cols[col] = col_label
        punches_df_cleaned[col_label] = df[col].apply(format_time_clean)
    
    base_info_df = df[[id_col, name_col]].copy()
    base_info_df.columns = ['P.Soft ID', 'Employee Name']
    
    base_info_df['Repeated\nOffender'] = base_info_df.groupby('P.Soft ID').cumcount() + 1
    
    final_df = pd.concat([base_info_df, analysis_df, punches_df_cleaned], axis=1)
    
    cols_order = (
        ['P.Soft ID', 'Employee Name', 'Repeated\nOffender', 'No. of\nWorking Hours', 'Mispunch Category', 'Issue Type'] 
        + list(punches_df_cleaned.columns) 
        + ['Total Punches', 'Status']
    )
    final_df = final_df[cols_order]

    mispunches_only = final_df[final_df['Issue Type'] == "Mispunch"].copy()
    defaulter_hours_only = final_df[final_df['Issue Type'] == "Defaulter Hours"].copy()
    clean_records_only = final_df[final_df['Issue Type'] == "Clean"].copy()
    repeated_offenders_only = final_df[final_df['Repeated\nOffender'] > 1].copy()
    
    if "selected_view" not in st.session_state:
        st.session_state.selected_view = "mispunches"
        
    # --- STYLISH GRADIENT CARDS CSS & LAYOUT ---
    st.markdown("""
        <style>
        .metric-card {
            padding:
