import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import base64

# Page Config
st.set_page_config(
    page_title="Attendance Mispunch & Repeated Defaulter Intelligence", 
    layout="wide"
)

def get_base64_of_bin_file(bin_file):
    with open(bin_file, 'rb') as f:
        data = f.read()
    return base64.b64encode(data).decode()

image_filename = 'bg.jpeg.jpeg'

try:
    bin_str = get_base64_of_bin_file(image_filename)
    st.markdown(
        f"""
        <style>
        #MainMenu {{visibility: hidden;}}
        header {{visibility: hidden;}}
        footer {{visibility: hidden;}}

        .stApp {{
            background-image: url("data:image/jpeg;base64,{bin_str}");
            background-size: cover;
            background-position: center;
            background-repeat: no-repeat;
            background-attachment: fixed;
        }}
        .block-container {{
            background-color: rgba(255, 255, 255, 0.92);
            padding: 2rem;
            border-radius: 12px;
            margin-top: 1.5rem;
            box-shadow: 0px 4px 15px rgba(0, 0, 0, 0.1);
        }}
        div[data-baseweb="select"] {{
            border: 2px solid #000000 !important;
            border-radius: 6px !important;
            background-color: #ffffff !important;
            font-weight: bold !important;
        }}
        div[data-testid="stSelectbox"] label p {{
            font-size: 16px !important;
            font-weight: 800 !important;
            color: #000000 !important;
        }}
        div[data-testid="stDataFrame"] th {{
            white-space: pre-wrap !important;
            word-wrap: break-word !important;
        }}
        div[data-testid="stFileUploader"] {{
            position: relative;
            background: linear-gradient(90deg, rgba(0, 97, 255, 0.04) 0%, rgba(96, 239, 255, 0.12) 50%, rgba(142, 45, 226, 0.06) 100%);
            border: 2px dashed #3b82f6 !important;
            padding: 18px !important;
            border-radius: 12px !important;
            box-shadow: 0 4px 15px rgba(0, 97, 255, 0.08);
        }}
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

st.markdown("""
    <div class="custom-header-container">
        <div class="custom-icon-box">📊</div>
        <div>
            <div class="custom-title-text">Attendance Mispunch & Repeated Defaulter Intelligence</div>
            <div class="custom-subtitle-text">Master Roster & Clean Shift-Mode Analyzer</div>
        </div>
    </div>
""", unsafe_allow_html=True)

st.markdown("---")

col_wh, col_mode, col_space = st.columns([2, 4, 4])
with col_wh:
    selected_warehouse = st.selectbox("Warehouse", options=["AUH1", "DXB5", "DXB3"], index=0)

with col_mode:
    upload_mode = st.selectbox(
        "Select Uploaded Data Shift / Mode", 
        options=[
            "Full Day / 24 Hours Data", 
            "Day Shift Only (e.g., 08:00 AM - 06:00 PM)", 
            "Night Shift Only (e.g., 06:10 PM - 04:10 AM)",
            "Mid Shift Only"
        ], 
        index=1
    )

st.markdown("<br>", unsafe_allow_html=True)

attendance_file = st.file_uploader("Upload Daily Attendance / Punches File", type=["xlsx", "xls", "csv"])

@st.cache_data
def load_permanent_roster():
    try:
        return pd.read_excel('HC.xlsx', sheet_name='Roster')
    except Exception:
        return None

ros_df = load_permanent_roster()

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

def analyze_mispunches(row, punch_cols, mode):
    punches = []
    actual_punch_positions = []
    
    for idx, col in enumerate(punch_cols):
        val = parse_time(row.get(col))
        if val is not None:
            punches.append(val)
            actual_punch_positions.append(idx)
            
    total_punches = len(punches)
    
    working_hours_raw = str(row.get('Working Hours', '9 Hours')).strip().lower()
    target_hours = 7 if '7' in working_hours_raw else 9

    if total_punches == 0:
        return pd.Series([0, "N/A", "OK", "No Punches / Absent", "Clean"])

    # BALANCED SINGLE SCAN INTELLIGENCE:
    if total_punches == 1:
        single_punch = punches[0]
        punch_total_mins = single_punch.hour * 60 + single_punch.minute
        
        # If Day Shift mode is selected:
        if "Day Shift Only" in mode:
            # If a single punch is around evening/night (17:00 onwards, like 17:57), it is a Night Shift start -> IGNORE (Clean)
            if punch_total_mins >= 17 * 60:
                return pd.Series([1, "N/A", "OK", "Night Shift Start Check-in (Ignored)", "Clean"])
            else:
                # If it's during morning hours (e.g. 8:05 AM) with only 1 punch, THEN it's a genuine Day Shift Mispunch!
                return pd.Series([1, "N/A", "Error", "Single Scan Only (Missing Shift OUT/Breaks)", "Mispunch"])
                
        # If Night Shift mode is selected:
        elif "Night Shift Only" in mode:
            # If single punch is during morning (06:00 to 12:00), it's a Day shift start -> IGNORE (Clean)
            if 6 * 60 <= punch_total_mins <= 12 * 60:
                return pd.Series([1, "N/A", "OK", "Day Shift Start Check-in (Ignored)", "Clean"])
            else:
                return pd.Series([1, "N/A", "Error", "Single Scan Only (Missing Shift OUT/Breaks)", "Mispunch"])
        
        # For Full Day data: single scans are treated as potential mispunches
        return pd.Series([1, "N/A", "Error", "Single Scan Only (Missing Shift OUT/Breaks)", "Mispunch"])

    is_last_punch_an_in = False
    if total_punches > 0:
        if actual_punch_positions[-1] % 2 == 0:
            is_last_punch_an_in = True

    status = "OK"
    category = "Complete"
    working_hours_str = "N/A"
    issue_type = "Clean"

    if total_punches % 2 != 0 or is_last_punch_an_in:
        status = "Error"
        issue_type = "Mispunch"
        if is_last_punch_an_in and total_punches % 2 == 0:
            category = "Shift END is IN (Missing Shift OUT)"
        else:
            category = f"Missing Scan ({total_punches} Punches)"
    else:
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
        
        min_allowed_seconds = (6 * 3600) + (50 * 60) if target_hours == 7 else (8 * 3600) + (50 * 60)
        max_allowed_seconds = (7 * 3600) + (20 * 60) if target_hours == 7 else (9 * 3600) + (10 * 60)
        
        if total_seconds < min_allowed_seconds:
            status = "Error"
            category = f"Short Working Hours (< {target_hours}h target)"
            issue_type = "Defaulter Hours"
        elif total_seconds > max_allowed_seconds:
            status = "Error"
            category = f"Overtime / Excessive Hours (> {target_hours}h target)"
            issue_type = "Defaulter Hours"
        else:
            status = "OK"
            category = "Complete"
            issue_type = "Clean"

    return pd.Series([total_punches, working_hours_str, status, category, issue_type])

if attendance_file is not None:
    try:
        att_xls = pd.ExcelFile(attendance_file)
        att_df = pd.read_excel(attendance_file, sheet_name=att_xls.sheet_names[0])
    except Exception:
        att_df = pd.read_csv(attendance_file) if attendance_file.name.endswith('.csv') else pd.read_excel(attendance_file)

    att_df.columns = [str(c).strip() for c in att_df.columns.tolist()]

    if ros_df is not None:
        att_id_col = next((c for c in att_df.columns if 'psoft' in c.lower() or 'id' in c.lower()), att_df.columns[0])
        ros_id_col = next((c for c in ros_df.columns if 'psoft' in c.lower() or 'id' in c.lower()), ros_df.columns[1])
        
        df = pd.merge(att_df, ros_df[['Psoft ID', 'Working Hours', 'No of breaks ', 'Shift timings ']], left_on=att_id_col, right_on=ros_id_col, how='left')
    else:
        df = att_df

    col_names = df.columns.tolist()

    id_col = None
    name_col = None

    for col in col_names:
        col_l = col.lower()
        if ('psoft' in col_l or 'p.soft' in col_l) and id_col is None:
            id_col = col
        elif ('name' in col_l or 'employee' in col_l) and name_col is None:
            name_col = col

    if id_col is None:
        id_col = col_names[1] if len(col_names) > 1 else col_names[0]
    if name_col is None:
        name_col = col_names[3] if len(col_names) > 3 else col_names[0]

    ignore_list = [id_col.lower(), name_col.lower(), 'sr', 'amazonid', 'amazon id', 'employment type', 'country', 'building', 'lob', 'cost center', 'shift', 'shift difference', 'off1', 'off2', 'working hours', 'no of breaks', 'no of breaks ', 'shift timings', 'shift timings ']
    
    punch_cols = []
    for col in col_names:
        c_low = col.lower()
        if c_low not in ignore_list and not any(ign in c_low for ign in ['psoft', 'amazon', 'employee', 'building', 'country', 'shift', 'break', 'off']):
            punch_cols.append(col)

    if len(punch_cols) == 0 and len(col_names) > 4:
        punch_cols = col_names[4:]

    st.markdown("""
        <div class="custom-header-container" style="margin-top: 20px;">
            <div class="custom-icon-box" style="background: linear-gradient(135deg, #8e2de2 0%, #4a00e0 100%); width: 40px; height: 40px; font-size: 20px;">📋</div>
            <div>
                <div class="custom-title-text" style="font-size: 22px;">Processing Summary & Live Analysis</div>
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    analysis_df = df.apply(lambda row: analyze_mispunches(row, punch_cols, upload_mode), axis=1)
    analysis_df.columns = ['Total Punches', 'No. of\nWorking Hours', 'Status', 'Mispunch Category', 'Issue Type']
    
    punches_df_cleaned = pd.DataFrame()
    for idx, col in enumerate(punch_cols):
        pair_num = (idx // 2) + 1
        label = "IN" if idx % 2 == 0 else "OUT"
        col_label = label if pair_num == 1 else f"{label} ({pair_num})"
        punches_df_cleaned[col_label] = df[col].apply(format_time_clean)
    
    raw_ids = df[id_col]
    raw_names = df[name_col]

    cleaned_ids = raw_ids.astype(str).str.replace(r'\.0$', '', regex=True)
    cleaned_names = raw_names.astype(str)

    if cleaned_ids.str.contains(',').any() or cleaned_ids.str.contains(r'[a-zA-Z]').any():
        temp = cleaned_ids
        cleaned_ids = cleaned_names.str.replace(r'\.0$', '', regex=True)
        cleaned_names = temp

    base_info_df = pd.DataFrame({
        'P.Soft ID': cleaned_ids,
        'Employee Name': cleaned_names
    })
    
    for opt_col in ['Shift', 'Working Hours', 'No of breaks ', 'Shift timings ']:
        if opt_col in df.columns:
            base_info_df[opt_col] = df[opt_col]
        
    base_info_df['Repeated\nOffender'] = base_info_df.groupby('P.Soft ID').cumcount() + 1
    
    final_df = pd.concat([base_info_df, analysis_df, punches_df_cleaned], axis=1)

    mispunches_only = final_df[final_df['Issue Type'] == "Mispunch"].copy()
    defaulter_hours_only = final_df[final_df['Issue Type'] == "Defaulter Hours"].copy()
    clean_records_only = final_df[final_df['Issue Type'] == "Clean"].copy()
    repeated_offenders_only = final_df[final_df['Repeated\nOffender'] > 1].copy()
    
    if "selected_view" not in st.session_state:
        st.session_state.selected_view = "mispunches"
        
    st.markdown("""
        <style>
        .metric-card {
            padding: 22px;
            border-radius: 12px 12px 0 0;
            color: white;
            font-family: sans-serif;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        }
        .card-blue { background: linear-gradient(135deg, #0061ff 0%, #60efff 100%); }
        .card-green { background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%); }
        .card-orange { background: linear-gradient(135deg, #f12711 0%, #f5af19 100%); }
        .card-purple { background: linear-gradient(135deg, #8e2de2 0%, #4a00e0 100%); }
        
        .card-title { font-size: 16px; font-weight: 600; opacity: 0.95; margin-bottom: 5px; }
        .card-value { font-size: 36px; font-weight: 800; }

        div[data-testid="stButton"] button {
            border-radius: 0 0 12px 12px !important;
            border-top: none !important;
            font-weight: 600 !important;
            box-shadow: 0 4px 10px rgba(0,0,0,0.08);
            transition: all 0.3s ease;
        }
        div[data-testid="stButton"] button:hover {
            transform: translateY(-2px);
        }
        </style>
    """, unsafe_allow_html=True)

    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f"""
            <div class="metric-card card-blue">
                <div class="card-title">📦 Total Records</div>
                <div class="card-value">{len(final_df)}</div>
            </div>
        """, unsafe_allow_html=True)
        if st.button("👁️ View All Records ➔", key="btn_all", use_container_width=True):
            st.session_state.selected_view = "all"
            
    with col2:
        st.markdown(f"""
            <div class="metric-card card-green">
                <div class="card-title">🔄 Repeated Offenders</div>
                <div class="card-value">{len(repeated_offenders_only)}</div>
            </div>
        """, unsafe_allow_html=True)
        if st.button("🔄 View Offenders List ➔", key="btn_repeated", use_container_width=True):
            st.session_state.selected_view = "repeated"
            
    with col3:
        st.markdown(f"""
            <div class="metric-card card-orange">
                <div class="card-title">⚠️ Mispunches</div>
                <div class="card-value">{len(mispunches_only)}</div>
            </div>
        """, unsafe_allow_html=True)
        if st.button("⚠️ View Mispunches ➔", key="btn_mispunch", type="primary", use_container_width=True):
            st.session_state.selected_view = "mispunches"
            
    with col4:
        st.markdown(f"""
            <div class="metric-card card-purple">
                <div class="card-title">⏰ Defaulter Hours</div>
                <div class="card-value">{len(defaulter_hours_only)}</div>
            </div>
        """, unsafe_allow_html=True)
        if st.button("⏰ View Defaulters ➔", key="btn_defaulters", use_container_width=True):
            st.session_state.selected_view = "defaulters"
            
    st.markdown("---")

    search_col1, search_col2 = st.columns([4, 6])
    with search_col1:
        search_query = st.text_input("🔍 Search Employee", placeholder="Type name or P.Soft ID...")

    if st.session_state.selected_view == "defaulters":
        active_display_df = defaulter_hours_only.drop(columns=['Issue Type'])
        current_title = f"⏰ Defaulter Working Hours List"
    elif st.session_state.selected_view == "mispunches":
        active_display_df = mispunches_only.drop(columns=['Issue Type', 'No. of\nWorking Hours'])
        current_title = f"⚠️ Missing & Extra Punches List"
    elif st.session_state.selected_view == "repeated":
        active_display_df = repeated_offenders_only.drop(columns=['Issue Type'])
        current_title = f"🔄 Repeated Offenders List"
    elif st.session_state.selected_view == "clean":
        active_display_df = clean_records_only.drop(columns=['Issue Type'])
        current_title = f"✅ Clean Employee Records"
    else:
        active_display_df = final_df.drop(columns=['Issue Type'])
        current_title = f"📊 All Employee Records"

    if search_query:
        query_lower = search_query.lower()
        active_display_df = active_display_df[
            active_display_df['Employee Name'].astype(str).str.lower().str.contains(query_lower) |
            active_display_df['P.Soft ID'].astype(str).str.lower().str.contains(query_lower)
        ]

    column_config_settings = {
        "Repeated\nOffender": st.column_config.NumberColumn("Repeated\nOffender", width="medium", format="%d"),
        "Total Punches": st.column_config.NumberColumn("Total\nPunches", width="small"),
        "No. of\nWorking Hours": st.column_config.TextColumn("No. of\nWorking Hours", width="medium"),
        "Status": st.column_config.TextColumn("Status", width="small")
    }

    st.subheader(f"{current_title} ({len(active_display_df)} Records)")
    st.dataframe(active_display_df, column_config=column_config_settings, use_container_width=True, hide_index=True)
