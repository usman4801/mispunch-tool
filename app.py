import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import base64
import os
import glob

st.set_page_config(
    page_title="Workforce Compliance Monitor", 
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ==========================================
# FORCE HIDE ALL STREAMLIT BADGES & ICONS
# ==========================================
st.markdown(
    """
    <style>
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    footer {visibility: hidden;}
    
    [data-testid="stToolbar"] {display: none !important; visibility: hidden !important;}
    [data-testid="stStatusWidget"] {display: none !important; visibility: hidden !important;}
    [data-testid="stDecoration"] {display: none !important; visibility: hidden !important;}
    [data-testid="collapsedControl"] {display: none !important; visibility: hidden !important;}
    .viewerBadge_container {display: none !important; visibility: hidden !important; opacity: 0 !important;}
    .viewerBadge_link {display: none !important; visibility: hidden !important;}
    #st-toolbar {display: none !important; visibility: hidden !important;}
    .stActionButton {display: none !important; visibility: hidden !important;}
    div[class^="viewerBadge"] {display: none !important;}
    
    /* STREAMLIT CLOUD BADGE & MANAGE APP BUTTON HIDE */
    #manage-app-button {display: none !important; visibility: hidden !important;}
    div[data-testid="manage-app-button"] {display: none !important; visibility: hidden !important;}
    [data-testid="stConnectionStatus"] {display: none !important; visibility: hidden !important;}
    .st-emotion-cache-12w0ip6 {display: none !important; visibility: hidden !important;}
    
    /* CLEAN PROFESSIONAL SOLID BACKGROUND */
    .stApp {
        background-color: #f8fafc;
    }
    
    /* SINGLE-PAGE COMPACT CONTAINER */
    .block-container {
        background: #ffffff !important;
        padding: 1.5rem 2rem !important;
        border-radius: 16px !important;
        margin-top: 0.5rem !important;
        box-shadow: 0 10px 25px rgba(0, 0, 0, 0.06) !important;
        border: 1px solid #e2e8f0 !important;
        max-width: 100% !important;
    }
    
    /* DIRECT HEADER IMAGE STYLING */
    .direct-header-img {
        width: 100%;
        border-radius: 16px;
        margin-bottom: 18px;
        box-shadow: 0 8px 25px rgba(168, 85, 247, 0.15);
        border: 1px solid rgba(216, 180, 254, 0.6);
        display: block;
    }

    /* FILTERS CONTAINER STYLING */
    div[data-testid="stSelectbox"] {
        border: none !important;
        padding: 0px !important;
        background: transparent !important;
    }
    div[data-testid="stSelectbox"] label p {
        font-weight: 800 !important;
        color: #000000 !important;
        font-size: 13px !important;
    }
    
    /* UPDATED: LIGHT ORANGE BORDER FOR DATE INPUT */
    div[data-testid="stDateInput"] {
        border: 2px dashed #ffb74d !important;
        padding: 6px 12px !important;
        border-radius: 12px !important;
        background: #fffdf5 !important;
    }
    div[data-testid="stDateInput"] label p {
        font-weight: 800 !important;
        color: #000000 !important;
        font-size: 13px !important;
        display: flex !important;
        justify-content: space-between !important;
        align-items: center !important;
        width: 100% !important;
    }
    div[data-testid="stDateInput"] label p::after {
        content: "📅";
        font-size: 16px;
    }

    /* BRANCH LOGO STYLING */
    .branch-logo {
        max-height: 45px;
        margin-top: 8px;
        border-radius: 8px;
        object-fit: contain;
    }

    /* FEATURE CARDS */
    .feature-card {
        padding: 16px;
        border-radius: 18px;
        height: 120px;
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        text-align: center;
        box-shadow: 0 4px 15px rgba(0,0,0,0.04);
        border: 1.5px solid;
    }
    .fc-blue { background: #f0f6ff; border-color: #d2e3fc; }
    .fc-orange { background: #fefce8; border-color: #fef08a; }
    .fc-green { background: #f0fdf4; border-color: #bbf7d0; }
    .fc-purple { background: #faf5ff; border-color: #f3e8ff; }
    
    .fc-title { font-size: 13px; font-weight: 800; color: #1e1b4b; margin-top: 6px; margin-bottom: 3px; }
    .fc-text { font-size: 10.5px; color: #475569; line-height: 1.3; font-weight: 500; }

    /* METRIC CARDS INSIDE DASHBOARD */
    .metric-card {
        padding: 22px;
        border-radius: 14px 14px 0 0;
        color: white;
        font-family: sans-serif;
        box-shadow: 0 6px 15px rgba(0,0,0,0.1);
    }
    .card-blue { background: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%); }
    .card-red { background: linear-gradient(135deg, #ef4444 0%, #b91c1c 100%); }
    .card-orange { background: linear-gradient(135deg, #f59e0b 0%, #b45309 100%); }
    .card-purple { background: linear-gradient(135deg, #8b5cf6 0%, #6d28d9 100%); }
    
    .card-title { font-size: 14px; font-weight: 600; opacity: 0.9; margin-bottom: 8px; text-transform: uppercase; letter-spacing: 0.5px; }
    .card-value { font-size: 32px; font-weight: 800; }
    </style>
    """,
    unsafe_allow_html=True
)

def get_base64_of_bin_file(bin_file):
    try:
        with open(bin_file, 'rb') as f:
            data = f.read()
        return base64.b64encode(data).decode()
    except:
        return ""

header_img_str = get_base64_of_bin_file('header_banner.png')

# ==========================================
# WELCOME / DASHBOARD SCREEN
# ==========================================
if header_img_str:
    st.markdown(f'<img src="data:image/png;base64,{header_img_str}" class="direct-header-img">', unsafe_allow_html=True)
else:
    st.warning("⚠️ Please upload 'header_banner.png' to GitHub repository.")

# Filter Section: Site on left, Calendar taking the remaining space
f_col1, f_col2 = st.columns([4, 8])
with f_col1:
    selected_warehouse = st.selectbox("📍 Site", options=["AUH1", "DXB5", "DXB3"])
    
    possible_logos = [f"{selected_warehouse}_logo.png", f"{selected_warehouse}_logo.jpeg", f"{selected_warehouse}_logo.jpg"]
    logo_path = next((p for p in possible_logos if os.path.exists(p)), None)
    
    if logo_path:
        logo_base64 = get_base64_of_bin_file(logo_path)
        mime_type = "image/jpeg" if logo_path.endswith((".jpeg", ".jpg")) else "image/png"
        st.markdown(f'<img src="data:{mime_type};base64,{logo_base64}" class="branch-logo">', unsafe_allow_html=True)

with f_col2:
    selected_dates_range = st.date_input("Select Date Range • Auto-Fetch (No File Required)", value=[])
    st.markdown("<p style='font-size: 12px; color: gray; font-weight: normal; margin-top: -12px;'>Weekly Refresh 10-08-2026 ✅</p>", unsafe_allow_html=True)

st.markdown("<div style='margin-top: 10px;'></div>", unsafe_allow_html=True)

def clean_id(val):
    try:
        return str(int(float(val))).strip()
    except:
        return str(val).strip().lower()

st.sidebar.header("⚙️ 7-Hours Configuration")
seven_hours_default = (
    "205854274, 206247771, 206930332, 206915012, 206065208, 206136723, 206200811, "
    "205853892, 206192237, 206361774, 206348020, 206348027, 206348019, 206368537, "
    "206348026, 206348045, 206348030, 206348048, 206348049, 206348041, 206368538, "
    "206348029, 206348042, 205845552, 206348052, 206348054, 203875181, 203875184, "
    "203875092, 203875089, 203875090, 203875180, 203875183, 112463068, 203875088, "
    "203875091, 203875185, 203875186, 206868000, 206897671, 206897640, 206136735, "
    "205231290, 205252357, 206192232, 206491343, 206128578, 206136722, 205252356, "
    "205252538, 205199356, 206230579, 206491328, 206240253, 206930331, 206868288, "
    "206897649, 206868005, 206239524, 206136718"
)
manual_7_ids = st.sidebar.text_area("Paste 7-Hour Employee IDs (Comma separated)", value=seven_hours_default)
manual_ids_list = [clean_id(x) for x in manual_7_ids.split(',')] if manual_7_ids else []

exclude_ids_input = st.sidebar.text_area("Paste IDs to Ignore", value="203160008, 203118578, 203073563, 204043092, 203052485, 203160007, 113015344, 203160009, 203118579, 203073561, 203052856, 203073425, 207574273, 202383469, 202383469, 203073699")
exclude_list = [clean_id(x) for x in exclude_ids_input.split(',')] if exclude_ids_input else []

@st.cache_data
def load_permanent_roster():
    roster_map = {}
    for filename in ['HC.xlsx', 'hc.xlsx', 'HC.XLSX', 'hc.XLSX']:
        if os.path.exists(filename):
            try:
                ros = pd.read_excel(filename, dtype=str)
                ros_cols = [str(c).strip().lower() for c in ros.columns.tolist()]
                ros.columns = ros_cols
                id_col = next((c for c in ros_cols if 'id' in c or 'psoft' in c or 'emp' in c or 'no' in c), ros_cols[0])
                for _, row in ros.iterrows():
                    if pd.isna(row.get(id_col)):
                        continue
                    cid = clean_id(row[id_col])
                    row_text = " ".join([str(v).lower() for v in row.values])
                    if '7 hour' in row_text or '7 hr' in row_text or '7hr' in row_text or ' 7 ' in row_text or '7.0' in row_text:
                        roster_map[cid] = '7 Hours'
                    else:
                        roster_map[cid] = '9 Hours'
                break
            except Exception:
                pass
    return roster_map

roster_hours_map = load_permanent_roster()

def parse_time(time_val):
    if pd.isna(time_val) or str(time_val).strip().lower() in ["nan", "none", ""]: return None
    for fmt in ["%H:%M:%S", "%H:%M", "%I:%M:%S %p", "%I:%M %p", "%H:%M:%S"]:
        try:
            return datetime.strptime(str(time_val).strip(), fmt).time()
        except:
            continue
    return None

temp_dfs = []
missing_files = []

if isinstance(selected_dates_range, tuple) and len(selected_dates_range) == 2:
    start_d, end_d = selected_dates_range
    delta = end_d - start_d
    date_list = [start_d + timedelta(days=i) for i in range(delta.days + 1)]
    
    for d in date_list:
        d_str = d.strftime("%Y-%m-%d")
        
        if selected_warehouse == "AUH1":
            possible_paths = [f"{d_str}.xlsx.xlsx", f"{d_str}.xlsx", f"{d_str}.xls"]
        elif selected_warehouse == "DXB5":
            possible_paths = [f"DXB5 {d_str}.xlsx.xlsx", f"DXB5 {d_str}.xlsx", f"DXB5 {d_str}.xls"]
        elif selected_warehouse == "DXB3":
            possible_paths = [f"DXB3 {d_str}.xlsx.xlsx", f"DXB3 {d_str}.xlsx", f"DXB3 {d_str}.xls"]
        else:
            possible_paths = [f"{d_str}.xlsx.xlsx", f"{d_str}.xlsx"]
            
        f_path = next((p for p in possible_paths if os.path.exists(p)), None)
        
        if f_path:
            try:
                tdf = pd.read_excel(f_path, sheet_name=0, dtype=str)
                tdf['Date'] = d_str
                temp_dfs.append(tdf)
            except:
                try:
                    tdf = pd.read_csv(f_path, dtype=str)
                    tdf['Date'] = d_str
                    temp_dfs.append(tdf)
                except:
                    missing_files.append(d_str)
        else:
            missing_files.append(d_str)

att_df = pd.concat(temp_dfs, ignore_index=True) if temp_dfs else pd.DataFrame()

if not att_df.empty:
    att_df.columns = [str(c).strip() for c in att_df.columns.tolist()]
    id_col = att_df.columns[0]
    name_col = att_df.columns[1]
    att_df['Clean_ID'] = att_df[id_col].apply(clean_id)

    if exclude_list:
        att_df = att_df[~att_df['Clean_ID'].isin(exclude_list)].copy()
        att_df.reset_index(drop=True, inplace=True)

    def determine_working_hours(row):
        cid = row['Clean_ID']
        if manual_ids_list and cid in manual_ids_list: return "7 Hours"
        if roster_hours_map and cid in roster_hours_map: return roster_hours_map[cid]
        return "9 Hours"

    att_df['Working Hours'] = att_df.apply(determine_working_hours, axis=1)
    ignore_keywords = ['id', 'name', 'psoft', 'employee', 'building', 'country', 'working hours', 'clean_id', 'date']
    punch_cols = [col for col in att_df.columns if not any(k in col.lower() for k in ignore_keywords)]
    if len(punch_cols) == 0 and len(att_df.columns) > 4:
        punch_cols = [c for c in att_df.columns[4:] if c != 'Date']

    def analyze_row(row):
        punches = [parse_time(row.get(c)) for c in punch_cols]
        punches = [p for p in punches if p is not None]
        total_punches = len(punches)
        target_str = str(row.get('Working Hours', '9 Hours'))
        min_mins = 408 if '7' in target_str else 528
        max_mins = 432 if '7' in target_str else 552

        if total_punches == 0: return pd.Series([0, target_str, "00:00", "OK", "Absent", "Clean"])
        if total_punches == 1: return pd.Series([1, target_str, "N/A", "Error", "Single Scan Only", "Mispunch"])

        dummy_date = datetime(2026, 1, 1)
        total_secs = 0
        for i in range(0, total_punches - (total_punches % 2), 2):
            s = datetime.combine(dummy_date, punches[i])
            e = datetime.combine(dummy_date, punches[i+1])
            if e < s: e += timedelta(days=1)
            total_secs += (e - s).total_seconds()
        eff_mins = total_secs / 60
        hours_str = f"{int(total_secs // 3600):02d}:{int((total_secs % 3600) // 60):02d}"
        
        if total_punches % 2 == 0:
            if min_mins <= eff_mins <= max_mins: return pd.Series([total_punches, target_str, hours_str, "OK", "Complete Within Window", "Clean"])
            elif eff_mins < min_mins: return pd.Series([total_punches, target_str, hours_str, "Error", "Under Time", "Defaulter Hours"])
            else: return pd.Series([total_punches, target_str, hours_str, "Error", "Over Time", "Defaulter Hours"])
        else:
            return pd.Series([total_punches, target_str, hours_str, "Error", "Incomplete Punches", "Mispunch"])

    analysis_df = att_df.apply(analyze_row, axis=1)
    analysis_df.columns = ['Total Punches', 'Assigned Target', 'Calculated Hours', 'Status', 'Mispunch Category', 'Issue Type']
    
    punches_clean = pd.DataFrame()
    for idx, col in enumerate(punch_cols):
        label = "IN" if idx % 2 == 0 else "OUT"
        num = (idx // 2) + 1
        punches_clean[f"{label} ({num})" if num > 1 else label] = att_df[col].apply(lambda x: parse_time(x).strftime("%H:%M") if parse_time(x) else "")

    base_info = pd.DataFrame({
        'Date': att_df['Date'],
        'P.Soft ID': att_df[id_col].astype(str).str.replace(r'\.0$', '', regex=True).str.strip(),
        'Employee Name': att_df[name_col].astype(str).str.replace(r'\.0$', '', regex=True).str.strip()
    })
    
    final_df = pd.concat([base_info, analysis_df, punches_clean], axis=1)

    # Strictly separate Mispunches and Defaulter Hours
    mispunches = final_df[final_df['Issue Type'] == "Mispunch"].copy()
    defaulters = final_df[final_df['Issue Type'] == "Defaulter Hours"].copy()
    
    # Calculate counts and repeated IDs strictly for each category independently
    mis_counts = mispunches['P.Soft ID'].value_counts()
    def_counts = defaulters['P.Soft ID'].value_counts()
    
    repeated_mis_ids = mis_counts[mis_counts > 1].index
    repeated_def_ids = def_counts[def_counts > 1].index
    
    repeated_mispunches = mispunches[mispunches['P.Soft ID'].isin(repeated_mis_ids)]
    repeated_defaulters = defaulters[defaulters['P.Soft ID'].isin(repeated_def_ids)]

    if "selected_view" not in st.session_state: st.session_state.selected_view = "all"

    st.markdown("<br>", unsafe_allow_html=True)
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(f'<div class="metric-card card-blue"><div class="card-title">⏳ Repeated Time Deficits</div><div class="card-value">{len(repeated_def_ids)}</div></div>', unsafe_allow_html=True)
        if st.button("⏳ View Rep. Deficits ➔", key="btn_rep_def", use_container_width=True): st.session_state.selected_view = "rep_defaulters"
    with c2:
        st.markdown(f'<div class="metric-card card-red"><div class="card-title">🔄 Repeated Mispunches</div><div class="card-value">{len(repeated_mis_ids)}</div></div>', unsafe_allow_html=True)
        if st.button("🔄 View Rep. Mispunches ➔", key="btn_rep_mis", use_container_width=True): st.session_state.selected_view = "rep_mispunches"
    with c3:
        st.markdown(f'<div class="metric-card card-orange"><div class="card-title">⚠️ Mispunches</div><div class="card-value">{len(mispunches)}</div></div>', unsafe_allow_html=True)
        if st.button("⚠️ View Mispunches ➔", key="btn_mis", use_container_width=True): st.session_state.selected_view = "mispunches"
    with c4:
        st.markdown(f'<div class="metric-card card-purple"><div class="card-title">⏰ Defaulter Hours</div><div class="card-value">{len(defaulters)}</div></div>', unsafe_allow_html=True)
        if st.button("⏰ View Defaulters ➔", key="btn_def", use_container_width=True): st.session_state.selected_view = "defaulters"

    display_df = final_df.copy()
    if st.session_state.selected_view == "rep_defaulters": display_df = repeated_defaulters
    elif st.session_state.selected_view == "rep_mispunches": display_df = repeated_mispunches
    elif st.session_state.selected_view == "mispunches": display_df = mispunches
    elif st.session_state.selected_view == "defaulters": display_df = defaulters

    st.subheader(f"📊 Results View ({len(display_df)} Records)")
    search = st.text_input("🔍 Search Employee by Name or ID...")
    if search:
        display_df = display_df[display_df['Employee Name'].str.contains(search, case=False, na=False) | display_df['P.Soft ID'].str.contains(search, case=False, na=False)]
    
    st.dataframe(display_df.drop(columns=['Issue Type']), use_container_width=True, hide_index=True)

    if missing_files:
        st.warning(f"⚠️ **Note:** Following dates have no data file reflected for **{selected_warehouse}**: {', '.join(missing_files)}")

else:
    if isinstance(selected_dates_range, tuple) and len(selected_dates_range) == 2:
        st.info(f"📂 **No data reflected:** No attendance files found for **{selected_warehouse}** in the selected date range.")
    else:
        st.markdown("<div style='margin-top: 15px;'></div>", unsafe_allow_html=True)
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.markdown('<div class="feature-card fc-blue"><div style="font-size:22px;">📊</div><div class="fc-title">Accurate Attendance Tracking</div><div class="fc-text">Detect mispunches and anomalies in real time</div></div>', unsafe_allow_html=True)
        with c2:
            st.markdown('<div class="feature-card fc-orange"><div style="font-size:22px;">🛡️</div><div class="fc-title">Stronger Policy Compliance</div><div class="fc-text">Ensure workforce discipline with smarter insights</div></div>', unsafe_allow_html=True)
        with c3:
            st.markdown('<div class="feature-card fc-green"><div style="font-size:22px;">📈</div><div class="fc-title">Data-Driven Decisions</div><div class="fc-text">Turn attendance data into actionable intelligence</div></div>', unsafe_allow_html=True)
        with c4:
            st.markdown('<div class="feature-card fc-purple"><div style="font-size:22px;">👥</div><div class="fc-title">Empowered Workforce</div><div class="fc-text">Build a reliable and productive work environment</div></div>', unsafe_allow_html=True)

    st.markdown("<hr style='border: none; border-top: 1px solid #e2e8f0; margin: 15px 0 10px 0;'>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #64748b; font-size: 11px; font-weight: 600; margin: 0;'>Built for a smarter, stronger and compliant workplace</p>", unsafe_allow_html=True)
