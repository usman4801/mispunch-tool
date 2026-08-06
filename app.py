import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import base64
import io

st.set_page_config(
    page_title="Attendance Mispunch & Repeated Defaulter Intelligence", 
    layout="wide"
)

def get_base64_of_bin_file(bin_file):
    try:
        with open(bin_file, 'rb') as f:
            data = f.read()
        return base64.b64encode(data).decode()
    except:
        return ""

image_filename = 'bg.jpeg.jpeg'
bin_str = get_base64_of_bin_file(image_filename)

if bin_str:
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

st.markdown("""
    <div class="custom-header-container">
        <div class="custom-icon-box">📊</div>
        <div>
            <div class="custom-title-text">Attendance Mispunch & Repeated Defaulter Intelligence</div>
            <div class="custom-subtitle-text">Master Roster & Cross-Midnight Shift Analyzer</div>
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
        index=0
    )

st.markdown("<br>", unsafe_allow_html=True)

attendance_file = st.file_uploader("Upload Daily Attendance / Punches File", type=["xlsx", "xls", "csv"])

# POLISHED ROSTER LOADER WITH STRICT CLEANING
@st.cache_data
def load_permanent_roster():
    try:
        ros = pd.read_excel('HC.xlsx', sheet_name='Roster')
        ros.columns = [str(c).strip() for c in ros.columns.tolist()]
        return ros
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

if attendance_file is not None:
    try:
        att_xls = pd.ExcelFile(attendance_file)
        att_df = pd.read_excel(attendance_file, sheet_name=att_xls.sheet_names[0])
    except Exception:
        att_df = pd.read_csv(attendance_file) if attendance_file.name.endswith('.csv') else pd.read_excel(attendance_file)

    att_df.columns = [str(c).strip() for c in att_df.columns.tolist()]
    col_names = att_df.columns.tolist()

    id_col = col_names[0]
    name_col = col_names[1]

    att_df['Clean_ID'] = att_df[id_col].astype(str).str.replace(r'\.0$', '', regex=True).str.strip()

    shift_map = {}
    hours_map = {}
    breaks_map = {}
    timings_map = {}

    if ros_df is not None:
        ros_id_col = next((c for c in ros_df.columns if 'psoft' in c.lower() or 'id' in c.lower()), ros_df.columns[1])
        shift_col = next((c for c in ros_df.columns if 'shift' in c.lower() and 'timing' not in c.lower()), None)
        hours_col = next((c for c in ros_df.columns if 'working' in c.lower() or 'hour' in c.lower()), None)
        breaks_col = next((c for c in ros_df.columns if 'break' in c.lower()), None)
        timings_col = next((c for c in ros_df.columns if 'timing' in c.lower()), None)

        for _, r in ros_df.iterrows():
            r_id = str(r[ros_id_col]).replace('.0', '').strip()
            if shift_col:
                s_val = str(r[shift_col]).strip().lower()
                if 'night' in s_val: shift_map[r_id] = "Night"
                elif 'mid' in s_val: shift_map[r_id] = "Mid"
                else: shift_map[r_id] = "Day"
            if hours_col:
                hours_map[r_id] = str(r[hours_col]).strip()
            if breaks_col:
                breaks_map[r_id] = str(r[breaks_col]).strip()
            if timings_col:
                timings_map[r_id] = str(r[timings_col]).strip()

    df = att_df.copy()
    df['Shift_Roster'] = df['Clean_ID'].map(shift_map)
    df['Working Hours'] = df['Clean_ID'].map(hours_map).fillna("9 Hours")
    df['No of breaks '] = df['Clean_ID'].map(breaks_map).fillna("0")
    df['Shift Timings'] = df['Clean_ID'].map(timings_map).fillna("")

    ignore_list = [str(id_col).lower(), str(name_col).lower(), 'clean_id', 'sr', 'amazonid', 'amazon id', 'employment type', 'country', 'building', 'lob', 'cost center', 'shift', 'shift difference', 'off1', 'off2', 'working hours', 'no of breaks', 'no of breaks ', 'shift timings', 'shift timings ']
    
    punch_cols = []
    for col in col_names:
        c_low = col.lower()
        if c_low not in ignore_list and not any(ign in c_low for ign in ['psoft', 'amazon', 'employee', 'building', 'country', 'shift', 'break', 'off', 'clean_id']):
            punch_cols.append(col)

    if len(punch_cols) == 0 and len(col_names) > 4:
        punch_cols = col_names[4:]

    def analyze_row(row):
        punches = []
        for col in punch_cols:
            val = parse_time(row.get(col))
            if val is not None:
                punches.append(val)
                
        total_punches = len(punches)
        
        shift_val = row.get('Shift_Roster')
        shift_timing_str = str(row.get('Shift Timings', '')).lower()
        
        if pd.isna(shift_val):
            if total_punches > 0:
                first_p_hour = punches[0].hour
                if first_p_hour >= 16 or first_p_hour < 5:
                    shift_val = "Night"
                elif 11 <= first_p_hour < 16:
                    shift_val = "Mid"
                else:
                    shift_val = "Day"
            else:
                shift_val = "Day"

        working_hours_raw = str(row.get('Working Hours', '9')).strip()
        
        # POLISHED & BULLETPROOF 12-MINUTE BUFFER LOGIC FOR BOTH 7 AND 9 HOURS
        if working_hours_raw.startswith('7') or '7' in working_hours_raw:
            target_hours = 7
            min_allowed_mins = (7 * 60) - 12  # Exactly 6h 48m (408 mins)
            max_allowed_mins = (7 * 60) + 12  # Exactly 7h 12m (432 mins)
        else:
            target_hours = 9
            min_allowed_mins = (9 * 60) - 12  # Exactly 8h 48m (528 mins)
            max_allowed_mins = (9 * 60) + 12  # Exactly 9h 12m (552 mins)

        breaks_raw = str(row.get('No of breaks ', '0')).strip()
        try:
            break_mins = int(''.join(filter(str.isdigit, breaks_raw)))
        except:
            break_mins = 0

        if total_punches == 0:
            return pd.Series([0, shift_val, "00:00", "OK", "Absent", "Clean"])

        if total_punches == 1:
            single_punch = punches[0]
            punch_total_mins = single_punch.hour * 60 + single_punch.minute
            
            is_cross_midnight = "next day" in shift_timing_str or shift_val == "Night"
            
            if is_cross_midnight and (punch_total_mins <= 9 * 60 or punch_total_mins >= 21 * 60):
                return pd.Series([1, shift_val, "N/A", "OK", "Cross-Midnight Log (Clean)", "Clean"])
            elif "Day Shift Only" in upload_mode and punch_total_mins >= 17 * 60:
                return pd.Series([1, shift_val, "N/A", "OK", "Shift Start (Clean)", "Clean"])
            elif "Night Shift Only" in upload_mode and 6 * 60 <= punch_total_mins <= 12 * 60:
                return pd.Series([1, shift_val, "N/A", "OK", "Shift Start (Clean)", "Clean"])
                
            return pd.Series([1, shift_val, "N/A", "Error", "Single Scan Only", "Mispunch"])

        dummy_date = datetime(2026, 1, 1)
        total_duration_seconds = 0
        for i in range(0, total_punches - (total_punches % 2), 2):
            s = datetime.combine(dummy_date, punches[i])
            e = datetime.combine(dummy_date, punches[i+1])
            if e < s: 
                e += timedelta(days=1)
            total_duration_seconds += (e - s).total_seconds()
        
        effective_seconds = total_duration_seconds - (break_mins * 60)
        effective_mins = effective_seconds / 60
        hours_str = f"{int(total_duration_seconds // 3600):02d}:{int((total_duration_seconds % 3600) // 60):02d}"
        
        if total_punches % 2 == 0:
            if min_allowed_mins <= effective_mins <= max_allowed_mins:
                return pd.Series([total_punches, shift_val, hours_str, "OK", "Complete Within Window", "Clean"])
            elif effective_mins < min_allowed_mins:
                return pd.Series([total_punches, shift_val, hours_str, "Error", f"Under Time (< {target_hours}h)", "Defaulter Hours"])
            else:
                return pd.Series([total_punches, shift_val, hours_str, "Error", f"Over Time (> {target_hours}h)", "Defaulter Hours"])
        else:
            return pd.Series([total_punches, shift_val, hours_str, "Error", "Incomplete Punches", "Mispunch"])

    st.markdown("""
        <div class="custom-header-container" style="margin-top: 20px;">
            <div class="custom-icon-box" style="background: linear-gradient(135deg, #8e2de2 0%, #4a00e0 100%); width: 40px; height: 40px; font-size: 20px;">📋</div>
            <div>
                <div class="custom-title-text" style="font-size: 22px;">Processing Summary & Live Analysis</div>
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    analysis_df = df.apply(analyze_row, axis=1)
    analysis_df.columns = ['Total Punches', 'Shift', 'No. of\nWorking Hours', 'Status', 'Mispunch Category', 'Issue Type']
    
    punches_df_cleaned = pd.DataFrame()
    for idx, col in enumerate(punch_cols):
        pair_num = (idx // 2) + 1
        label = "IN" if idx % 2 == 0 else "OUT"
        col_label = label if pair_num == 1 else f"{label} ({pair_num})"
        punches_df_cleaned[col_label] = df[col].apply(format_time_clean)
    
    base_info_df = pd.DataFrame({
        'P.Soft ID': df['Clean_ID'],
        'Employee Name': df[name_col].astype(str).str.replace(r'\.0$', '', regex=True).str.strip()
    })
    
    base_info_df['Repeated\nOffender'] = base_info_df.groupby('P.Soft ID').cumcount() + 1
    
    temp_combined_df = pd.concat([base_info_df, analysis_df, punches_df_cleaned], axis=1)

    base_cols_ordered = ['P.Soft ID', 'Employee Name', 'Repeated\nOffender', 'Total Punches', 'Shift', 'No. of\nWorking Hours', 'Status', 'Mispunch Category']
    punch_cols_ordered = list(punches_df_cleaned.columns)
    end_cols_ordered = ['Issue Type']
    
    final_df = temp_combined_df[base_cols_ordered + punch_cols_ordered + end_cols_ordered]

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
        "P.Soft ID": st.column_config.TextColumn("P.Soft ID", width="medium"),
        "Employee Name": st.column_config.TextColumn("Employee Name", width="large"),
        "Repeated\nOffender": st.column_config.NumberColumn("Repeated\nOffender", width="medium", format="%d"),
        "Total Punches": st.column_config.NumberColumn("Total\nPunches", width="small"),
        "No. of\nWorking Hours": st.column_config.TextColumn("No. of\nWorking Hours", width="medium"),
        "Status": st.column_config.TextColumn("Status", width="small")
    }

    st.subheader(f"{current_title} ({len(active_display_df)} Records)")
    st.dataframe(active_display_df, column_config=column_config_settings, use_container_width=True, hide_index=True)

    st.markdown("<br>", unsafe_allow_html=True)
    
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        final_df.drop(columns=['Issue Type']).to_excel(writer, index=False, sheet_name='Attendance_Analysis')
    processed_data = output.getvalue()

    st.download_button(
        label="📥 Download Full Analyzed Report (Excel)",
        data=processed_data,
        file_name=f"Attendance_Analysis_{selected_warehouse}_{datetime.now().strftime('%Y-%m-%d')}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        type="primary"
    )
