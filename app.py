import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import base64
import os

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

bin_str = get_base64_of_bin_file('bg.jpeg.jpeg')

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
            background-color: rgba(255, 255, 255, 0.95);
            padding: 2rem;
            border-radius: 12px;
            margin-top: 1.5rem;
            box-shadow: 0px 4px 15px rgba(0, 0, 0, 0.1);
        }}
        div[data-testid="stFileUploader"] {{
            border: 2px dashed #3b82f6 !important;
            padding: 18px !important;
            border-radius: 12px !important;
            background: rgba(240, 248, 255, 0.5);
        }}
        .metric-card {{
            padding: 22px;
            border-radius: 12px 12px 0 0;
            color: white;
            font-family: sans-serif;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        }}
        .card-blue {{ background: linear-gradient(135deg, #0061ff 0%, #60efff 100%); }}
        .card-green {{ background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%); }}
        .card-orange {{ background: linear-gradient(135deg, #f12711 0%, #f5af19 100%); }}
        .card-purple {{ background: linear-gradient(135deg, #8e2de2 0%, #4a00e0 100%); }}
        
        .card-title {{ font-size: 16px; font-weight: 600; opacity: 0.95; margin-bottom: 5px; }}
        .card-value {{ font-size: 36px; font-weight: 800; }}

        div[data-testid="stButton"] button {{
            border-radius: 0 0 12px 12px !important;
            border-top: none !important;
            font-weight: 600 !important;
            box-shadow: 0 4px 10px rgba(0,0,0,0.08);
            transition: all 0.3s ease;
        }}
        div[data-testid="stButton"] button:hover {{
            transform: translateY(-2px);
        }}
        </style>
        """,
        unsafe_allow_html=True
    )

st.title("📊 Attendance Mispunch & Repeated Defaulter Intelligence")
st.markdown("---")

# -----------------------------------------------------
# SIDEBAR CONFIGURATIONS
# -----------------------------------------------------
def clean_id(val):
    try:
        return str(int(float(val))).strip()
    except:
        return str(val).strip().lower()

st.sidebar.header("⚙️ 7-Hours Configuration")
st.sidebar.info("Agar koi employee 7 hours par map nahi ho raha, toh uski ID yahan daal dein.")
manual_7_ids = st.sidebar.text_area("Paste 7-Hour Employee IDs (Comma separated)", placeholder="e.g., 204299912, 203875184")
manual_ids_list = [clean_id(x) for x in manual_7_ids.split(',')] if manual_7_ids else []

st.sidebar.markdown("---")
st.sidebar.header("🚫 Exclude / Ignore Employees")
st.sidebar.info("In logon ka data processing se bilkul nikal diya jayega (e.g. 10PM - 8AM shift wale).")
# Default IDs jo aapne screenshot mein di hain
exclude_ids_input = st.sidebar.text_area("Paste IDs to Ignore", value="203160008, 203073699, 204043092, 203160007, 113015344")
exclude_list = [clean_id(x) for x in exclude_ids_input.split(',')] if exclude_ids_input else []

col1, col2 = st.columns([3, 7])
with col1:
    selected_warehouse = st.selectbox("Warehouse", options=["AUH1", "DXB5", "DXB3"])
with col2:
    upload_mode = st.selectbox(
        "Shift / Mode", 
        options=["Full Day / 24 Hours Data", "Day Shift Only", "Night Shift Only", "Mid Shift Only"]
    )

attendance_file = st.file_uploader("Upload Daily Attendance File", type=["xlsx", "xls", "csv"])

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
                    if pd.isna(row.get(id_col)): continue
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

# MEMORY DATABASE LOGIC
HISTORY_FILE = 'offenders_history.csv'

def update_and_get_offenders_history(current_offenders_df):
    today_date = datetime.now().strftime("%Y-%m-%d")
    if os.path.exists(HISTORY_FILE):
        history_df = pd.read_csv(HISTORY_FILE, dtype=str)
    else:
        history_df = pd.DataFrame(columns=['Date', 'P.Soft ID', 'Employee Name', 'Issue Type'])

    new_records = current_offenders_df[['P.Soft ID', 'Employee Name', 'Issue Type']].copy()
    new_records['Date'] = today_date
    
    combined_df = pd.concat([history_df, new_records]).drop_duplicates(subset=['Date', 'P.Soft ID', 'Issue Type'])
    combined_df.to_csv(HISTORY_FILE, index=False)
    
    offense_counts = combined_df.groupby('P.Soft ID').size().reset_index(name='Total Offenses')
    return offense_counts

if attendance_file is not None:
    try:
        att_df = pd.read_excel(attendance_file, sheet_name=0, dtype=str)
    except:
        att_df = pd.read_csv(attendance_file, dtype=str)

    att_df.columns = [str(c).strip() for c in att_df.columns.tolist()]
    id_col = att_df.columns[0]
    name_col = att_df.columns[1]

    att_df['Clean_ID'] = att_df[id_col].apply(clean_id)

    # ==========================================
    # MAGIC FIX: EXCLUDE EMPLOYEES
    # ==========================================
    if exclude_list:
        att_df = att_df[~att_df['Clean_ID'].isin(exclude_list)].copy()
        att_df.reset_index(drop=True, inplace=True)

    if roster_hours_map:
        att_df['Working Hours'] = att_df['Clean_ID'].map(roster_hours_map).fillna("9 Hours")
    else:
        att_df['Working Hours'] = "9 Hours"

    if manual_ids_list:
        att_df.loc[att_df['Clean_ID'].isin(manual_ids_list), 'Working Hours'] = "7 Hours"
        
    att_df.loc[att_df['Clean_ID'] == '203875184', 'Working Hours'] = "7 Hours"

    ignore_keywords = ['id', 'name', 'psoft', 'employee', 'building', 'country', 'working hours', 'clean_id']
    punch_cols = [col for col in att_df.columns if not any(k in col.lower() for k in ignore_keywords)]
    if len(punch_cols) == 0 and len(att_df.columns) > 4:
        punch_cols = att_df.columns[4:].tolist()

    def parse_time(time_val):
        if pd.isna(time_val) or str(time_val).strip().lower() in ["nan", "none", ""]: return None
        for fmt in ["%H:%M:%S", "%H:%M", "%I:%M:%S %p", "%I:%M %p", "%H:%M:%S"]:
            try: return datetime.strptime(str(time_val).strip(), fmt).time()
            except: continue
        return None

    def analyze_row(row):
        punches = [parse_time(row.get(c)) for c in punch_cols]
        punches = [p for p in punches if p is not None]
        total_punches = len(punches)
        
        target_str = str(row.get('Working Hours', '9 Hours'))
        
        if '7' in target_str:
            min_mins = 408
            max_mins = 432
        else:
            min_mins = 528
            max_mins = 552

        if total_punches == 0:
            return pd.Series([0, target_str, "00:00", "OK", "Absent", "Clean"])
        if total_punches == 1:
            return pd.Series([1, target_str, "N/A", "Error", "Single Scan Only", "Mispunch"])

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
            if min_mins <= eff_mins <= max_mins:
                return pd.Series([total_punches, target_str, hours_str, "OK", "Complete Within Window", "Clean"])
            elif eff_mins < min_mins:
                return pd.Series([total_punches, target_str, hours_str, "Error", f"Under Time", "Defaulter Hours"])
            else:
                return pd.Series([total_punches, target_str, hours_str, "Error", f"Over Time", "Defaulter Hours"])
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
        'P.Soft ID': att_df[id_col].astype(str).str.replace(r'\.0$', '', regex=True).str.strip(),
        'Employee Name': att_df[name_col].astype(str).str.replace(r'\.0$', '', regex=True).str.strip()
    })
    
    temp_combined = pd.concat([base_info, analysis_df], axis=1)
    today_offenders = temp_combined[temp_combined['Issue Type'].isin(['Mispunch', 'Defaulter Hours'])]
    
    historical_counts = update_and_get_offenders_history(today_offenders)
    
    base_info = base_info.merge(historical_counts, on='P.Soft ID', how='left')
    base_info['Total Offenses'] = base_info['Total Offenses'].fillna(0).astype(int)
    
    final_df = pd.concat([base_info, analysis_df, punches_clean], axis=1)

    mispunches = final_df[final_df['Issue Type'] == "Mispunch"]
    defaulters = final_df[final_df['Issue Type'] == "Defaulter Hours"]
    repeated = final_df[final_df['Total Offenses'] > 1]

    if "selected_view" not in st.session_state:
        st.session_state.selected_view = "all"

    st.markdown("<br>", unsafe_allow_html=True)
    c1, c2, c3, c4 = st.columns(4)
    
    with c1:
        st.markdown(f'<div class="metric-card card-blue"><div class="card-title">📦 Total Records</div><div class="card-value">{len(final_df)}</div></div>', unsafe_allow_html=True)
        if st.button("👁️ View All Records ➔", key="btn_all", use_container_width=True): st.session_state.selected_view = "all"
        
    with c2:
        st.markdown(f'<div class="metric-card card-green"><div class="card-title">🔄 Repeated Offenders</div><div class="card-value">{len(repeated)}</div></div>', unsafe_allow_html=True)
        if st.button("🔄 View Offenders List ➔", key="btn_rep", use_container_width=True): st.session_state.selected_view = "repeated"
        
    with c3:
        st.markdown(f'<div class="metric-card card-orange"><div class="card-title">⚠️ Mispunches</div><div class="card-value">{len(mispunches)}</div></div>', unsafe_allow_html=True)
        if st.button("⚠️ View Mispunches ➔", key="btn_mis", use_container_width=True): st.session_state.selected_view = "mispunches"
        
    with c4:
        st.markdown(f'<div class="metric-card card-purple"><div class="card-title">⏰ Defaulter Hours</div><div class="card-value">{len(defaulters)}</div></div>', unsafe_allow_html=True)
        if st.button("⏰ View Defaulters ➔", key="btn_def", use_container_width=True): st.session_state.selected_view = "defaulters"

    display_df = final_df.copy()
    if st.session_state.selected_view == "mispunches":
        display_df = mispunches
        st.subheader(f"⚠️ Mispunches ({len(display_df)} Records)")
    elif st.session_state.selected_view == "defaulters":
        display_df = defaulters
        st.subheader(f"⏰ Defaulter Hours ({len(display_df)} Records)")
    elif st.session_state.selected_view == "repeated":
        display_df = repeated
        st.subheader(f"🔄 Repeated Offenders ({len(display_df)} Records)")
    else:
        st.subheader(f"📦 All Records ({len(display_df)} Records)")

    search = st.text_input("🔍 Search Employee by Name or ID...")
    
    if search:
        display_df = display_df[display_df['Employee Name'].str.contains(search, case=False, na=False) | display_df['P.Soft ID'].str.contains(search, case=False, na=False)]
    
    display_df = display_df.drop(columns=['Issue Type'])
    st.dataframe(display_df, use_container_width=True, hide_index=True)

    st.markdown("---")
    down_col1, down_col2 = st.columns(2)
    with down_col1:
        csv = final_df.drop(columns=['Issue Type']).to_csv(index=False).encode('utf-8')
        st.download_button("📥 Download Today's Report (CSV)", csv, f"Attendance_Report_{selected_warehouse}.csv", "text/csv", type="primary", use_container_width=True)
    with down_col2:
        if os.path.exists(HISTORY_FILE):
            hist_csv = pd.read_csv(HISTORY_FILE).to_csv(index=False).encode('utf-8')
            st.download_button("📂 Download Master Offenders History (Backup)", hist_csv, f"Master_Offenders_History.csv", "text/csv", use_container_width=True)
