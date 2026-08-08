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
        font-size: 12px !important;
    }
    div[data-testid="stDateInput"] {
        border: 2px dashed #c084fc !important;
        padding: 6px 12px !important;
        border-radius: 12px !important;
        background: #faf5ff !important;
    }
    div[data-testid="stDateInput"] label p {
        font-weight: 800 !important;
        color: #000000 !important;
        font-size: 12px !important;
        display: flex !important;
        justify-content: space-between !important;
        align-items: center !important;
        width: 100% !important;
    }
    div[data-testid="stDateInput"] label p::after {
        content: "📅";
        font-size: 16px;
    }

    /* PURPLE VIEW DASHBOARD BUTTON */
    div.stButton > button {
        background: linear-gradient(135deg, #8b5cf6 0%, #6d28d9 100%) !important;
        color: white !important;
        border-radius: 12px !important;
        font-weight: 700 !important;
        padding: 0.6rem 1.2rem !important;
        border: none !important;
        box-shadow: 0 4px 15px rgba(109, 40, 217, 0.3) !important;
        transition: all 0.3s ease;
    }
    div.stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(109, 40, 217, 0.4) !important;
    }

    /* FEATURE CARDS */
    .feature-card {
        padding: 14px;
        border-radius: 14px;
        height: 110px;
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        text-align: center;
        box-shadow: 0 3px 10px rgba(0,0,0,0.03);
        border: 1px solid rgba(0,0,0,0.04);
    }
    .fc-blue { background: #eff6ff; border-color: #dbeafe; }
    .fc-orange { background: #fffbeb; border-color: #fef3c7; }
    .fc-green { background: #f0fdf4; border-color: #dcfce7; }
    .fc-purple { background: #faf5ff; border-color: #f3e8ff; }
    
    .fc-title { font-size: 13px; font-weight: 700; color: #1e293b; margin-top: 4px; margin-bottom: 2px; }
    .fc-text { font-size: 10px; color: #64748b; line-height: 1.2; }

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

# Initialize session state for navigation
if "page_mode" not in st.session_state:
    st.session_state.page_mode = "welcome"

# ==========================================
# WELCOME SCREEN
# ==========================================
if st.session_state.page_mode == "welcome":
    
    # Display the direct header image
    if header_img_str:
        st.markdown(f'<img src="data:image/png;base64,{header_img_str}" class="direct-header-img">', unsafe_allow_html=True)
    else:
        st.warning("⚠️ Please upload 'header_banner.png' to GitHub repository.")

    # Filter Section (Aligned in 1 row)
    f_col1, f_col2, f_col3 = st.columns([3, 4, 4])
    with f_col1:
        selected_warehouse = st.selectbox("📍 Site", options=["AUH1", "DXB5", "DXB3"])
    with f_col2:
        upload_mode = st.selectbox("🕒 Shift / Mode", options=["Full Day / 24 Hours Data", "Day Shift Only", "Night Shift Only", "Mid Shift Only"])
    with f_col3:
        selected_dates_range = st.date_input("📅 Calendar Auto-Fetch (Select Date Range)", value=[])

    st.markdown("<div style='margin-top: 10px;'></div>", unsafe_allow_html=True)

    # Center View Dashboard Button
    _, btn_col, _ = st.columns([3, 3, 3])
    with btn_col:
        if st.button("🔍 View Dashboard ➔", use_container_width=True):
            st.session_state.page_mode = "dashboard"
            st.rerun()

    st.markdown("<div style='margin-top: 10px;'></div>", unsafe_allow_html=True)

    # Bottom 4 Feature Cards
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown('<div class="feature-card fc-blue"><div style="font-size:20px;">📊</div><div class="fc-title">Accurate Attendance Tracking</div><div class="fc-text">Detect mispunches and anomalies in real time</div></div>', unsafe_allow_html=True)
    with c2:
        st.markdown('<div class="feature-card fc-orange"><div style="font-size:20px;">🛡️</div><div class="fc-title">Stronger Policy Compliance</div><div class="fc-text">Ensure workforce discipline with smarter insights</div></div>', unsafe_allow_html=True)
    with c3:
        st.markdown('<div class="feature-card fc-green"><div style="font-size:20px;">📈</div><div class="fc-title">Data-Driven Decisions</div><div class="fc-text">Turn attendance data into actionable intelligence</div></div>', unsafe_allow_html=True)
    with c4:
        st.markdown('<div class="feature-card fc-purple"><div style="font-size:20px;">👥</div><div class="fc-title">Empowered Workforce</div><div class="fc-text">Build a reliable and productive work environment</div></div>', unsafe_allow_html=True)

    st.markdown("<hr style='border: none; border-top: 1px solid #e2e8f0; margin: 12px 0 8px 0;'>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #64748b; font-size: 11px; font-weight: 600; margin: 0;'>Built for a smarter, stronger and compliant workplace</p>", unsafe_allow_html=True)


# ==========================================
# MAIN DASHBOARD SCREEN (AFTER CLICKING VIEW)
# ==========================================
else:
    if st.button("⬅️ Back to Welcome Page"):
        st.session_state.page_mode = "welcome"
        st.rerun()

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

    exclude_ids_input = st.sidebar.text_area("Paste IDs to Ignore", value="203160008, 203073699, 204043092, 203160007, 113015344")
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
    HISTORY_FILE = 'offenders_history.csv'

    def parse_time(time_val):
        if pd.isna(time_val) or str(time_val).strip().lower() in ["nan", "none", ""]: return None
        for fmt in ["%H:%M:%S", "%H:%M", "%I:%M:%S %p", "%I:%M %p", "%H:%M:%S"]:
            try:
                return datetime.strptime(str(time_val).strip(), fmt).time()
            except:
                continue
        return None

    def rebuild_all_history():
        all_records = []
        all_files = glob.glob("2026-08-*.xlsx.xlsx") + glob.glob("2026-08-*.csv") + glob.glob("2026-08-*.xls")
        for fpath in all_files:
            f_date = os.path.basename(fpath).split(".")[0]
            try:
                df = pd.read_excel(fpath, sheet_name=0, dtype=str)
            except:
                try:
                    df = pd.read_csv(fpath, dtype=str)
                except:
                    continue
            df.columns = [str(c).strip() for c in df.columns.tolist()]
            if len(df.columns) < 2: continue
            id_c, name_c = df.columns[0], df.columns[1]
            ignore_kw = ['id', 'name', 'psoft', 'employee', 'building', 'country', 'working hours', 'clean_id']
            p_cols = [c for c in df.columns if not any(k in c.lower() for k in ignore_kw)]
            if len(p_cols) == 0 and len(df.columns) > 4:
                p_cols = df.columns[4:].tolist()
            for _, row in df.iterrows():
                cid = clean_id(row[id_c])
                if exclude_list and cid in exclude_list: continue
                cname = str(row[name_c]).strip()
                punches = [parse_time(row.get(c)) for c in p_cols]
                punches = [p for p in punches if p is not None]
                tp = len(punches)
                is_7hr = (manual_ids_list and cid in manual_ids_list) or (roster_hours_map.get(cid) == '7 Hours')
                min_m = 408 if is_7hr else 528
                max_m = 432 if is_7hr else 552
                issue = None
                if tp == 1:
                    issue = "Mispunch"
                elif tp >= 2 and tp % 2 == 0:
                    dummy_d = datetime(2026, 1, 1)
                    t_sec = 0
                    for i in range(0, tp, 2):
                        s = datetime.combine(dummy_d, punches[i])
                        e = datetime.combine(dummy_d, punches[i+1])
                        if e < s: e += timedelta(days=1)
                        t_sec += (e - s).total_seconds()
                    eff_m = t_sec / 60
                    if not (min_m <= eff_m <= max_m):
                        issue = "Defaulter Hours"
                elif tp > 0 and tp % 2 != 0:
                    issue = "Mispunch"
                if issue:
                    all_records.append({'Date': f_date, 'P.Soft ID': cid, 'Employee Name': cname, 'Issue Type': issue})
        if all_records:
            hist_df = pd.DataFrame(all_records).drop_duplicates(subset=['Date', 'P.Soft ID', 'Issue Type'])
            hist_df.to_csv(HISTORY_FILE, index=False)

    rebuild_all_history()

    all_repo_files = glob.glob("2026-08-*.xlsx.xlsx") + glob.glob("2026-08-*.csv") + glob.glob("2026-08-*.xls")
    temp_dfs = []
    for fpath in all_repo_files:
        f_date = os.path.basename(fpath).split(".")[0]
        try:
            tdf = pd.read_excel(fpath, sheet_name=0, dtype=str)
            tdf['Date'] = f_date
            temp_dfs.append(tdf)
        except:
            try:
                tdf = pd.read_csv(fpath, dtype=str)
                tdf['Date'] = f_date
                temp_dfs.append(tdf)
            except:
                pass

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
        
        if os.path.exists(HISTORY_FILE):
            hist_df = pd.read_csv(HISTORY_FILE, dtype=str)
            historical_counts = hist_df.groupby('P.Soft ID').size().reset_index(name='Total Offenses')
        else:
            historical_counts = pd.DataFrame(columns=['P.Soft ID', 'Total Offenses'])

        base_info = base_info.merge(historical_counts, on='P.Soft ID', how='left')
        base_info['Total Offenses'] = base_info['Total Offenses'].fillna(0).astype(int)
        final_df = pd.concat([base_info, analysis_df, punches_clean], axis=1)

        mispunches = final_df[final_df['Issue Type'] == "Mispunch"]
        defaulters = final_df[final_df['Issue Type'] == "Defaulter Hours"]
        repeated_mispunches = final_df[(final_df['Total Offenses'] > 1) & (final_df['Issue Type'] == "Mispunch")]
        repeated_defaulters = final_df[(final_df['Total Offenses'] > 1) & (final_df['Issue Type'] == "Defaulter Hours")]

        if "selected_view" not in st.session_state: st.session_state.selected_view = "all"

        st.markdown("<br>", unsafe_allow_html=True)
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.markdown(f'<div class="metric-card card-blue"><div class="card-title">⏳ Repeated Time Deficits</div><div class="card-value">{len(repeated_defaulters)}</div></div>', unsafe_allow_html=True)
            if st.button("⏳ View Rep. Deficits ➔", key="btn_rep_def", use_container_width=True): st.session_state.selected_view = "rep_defaulters"
        with c2:
            st.markdown(f'<div class="metric-card card-red"><div class="card-title">🔄 Repeated Mispunches</div><div class="card-value">{len(repeated_mispunches)}</div></div>', unsafe_allow_html=True)
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
