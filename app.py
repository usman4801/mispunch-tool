import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import base64
import os

st.set_page_config(
    page_title="Attendance Mispunch & Repeated Defaulter Intelligence", 
    layout="wide"
)

# Helper to get background
def get_base64_of_bin_file(bin_file):
    try:
        with open(bin_file, 'rb') as f:
            data = f.read()
        return base64.b64encode(data).decode()
    except:
        return ""

bin_str = get_base64_of_bin_file('bg.jpeg.jpeg')

# CSS Styling
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
    }}
    </style>
    """,
    unsafe_allow_html=True
)

st.title("📊 Attendance Mispunch & Repeated Defaulter Intelligence")
st.markdown("---")

# ID Cleaner
def clean_id(val):
    try: return str(int(float(val))).strip()
    except: return str(val).strip().lower()

# Sidebar Setup
st.sidebar.header("⚙️ Configuration")
manual_7_ids = st.sidebar.text_area("Paste 7-Hour IDs", placeholder="e.g., 204299912")
manual_ids_list = [clean_id(x) for x in manual_7_ids.split(',')] if manual_7_ids else []

# Excluded Employees List (Ab isme naya banda bhi shamil hai)
exclude_list = ['203160008', '204043092', '203160007', '113015344', '203073699']

attendance_file = st.file_uploader("Upload Daily Attendance File", type=["xlsx", "xls", "csv"])

@st.cache_data
def load_permanent_roster():
    roster_map = {}
    if os.path.exists('HC.xlsx'):
        try:
            ros = pd.read_excel('HC.xlsx', dtype=str)
            ros.columns = [str(c).strip().lower() for c in ros.columns.tolist()]
            id_col = next((c for c in ros.columns if 'id' in c or 'emp' in c), ros.columns[0])
            for _, row in ros.iterrows():
                cid = clean_id(row[id_col])
                if '7' in " ".join([str(v).lower() for v in row.values]): roster_map[cid] = '7 Hours'
                else: roster_map[cid] = '9 Hours'
        except: pass
    return roster_map

roster_hours_map = load_permanent_roster()

# History Database
HISTORY_FILE = 'offenders_history.csv'
def update_history(current_offenders_df):
    today = datetime.now().strftime("%Y-%m-%d")
    hist = pd.read_csv(HISTORY_FILE, dtype=str) if os.path.exists(HISTORY_FILE) else pd.DataFrame(columns=['Date', 'P.Soft ID', 'Issue Type'])
    new_rec = current_offenders_df[['P.Soft ID', 'Issue Type']].copy()
    new_rec['Date'] = today
    combined = pd.concat([hist, new_rec]).drop_duplicates(subset=['Date', 'P.Soft ID', 'Issue Type'])
    combined.to_csv(HISTORY_FILE, index=False)
    return combined.groupby('P.Soft ID').size().reset_index(name='Total Offenses')

if attendance_file:
    att_df = pd.read_excel(attendance_file, sheet_name=0, dtype=str) if '.xls' in attendance_file.name else pd.read_csv(attendance_file, dtype=str)
    att_df.columns = [str(c).strip() for c in att_df.columns.tolist()]
    att_df['Clean_ID'] = att_df[att_df.columns[0]].apply(clean_id)

    # MAGIC FIX: Exclude here
    att_df = att_df[~att_df['Clean_ID'].isin(exclude_list)].copy()

    att_df['Working Hours'] = att_df['Clean_ID'].map(roster_hours_map).fillna("9 Hours")
    att_df.loc[att_df['Clean_ID'].isin(manual_ids_list), 'Working Hours'] = '7 Hours'
    att_df.loc[att_df['Clean_ID'] == '203875184', 'Working Hours'] = '7 Hours'

    punch_cols = [c for c in att_df.columns if not any(k in c.lower() for k in ['id', 'name', 'psoft', 'working'])]
    
    def analyze(row):
        punches = [datetime.strptime(str(row[c]).strip(), "%H:%M:%S").time() for c in punch_cols if pd.notna(row[c])]
        target = '7' in str(row.get('Working Hours', '9'))
        min_m = 408 if target else 528
        max_m = 432 if target else 552
        if len(punches) == 0: return pd.Series([0, 'Absent', 'Clean'])
        if len(punches) % 2 != 0: return pd.Series([len(punches), 'Mispunch', 'Mispunch'])
        
        total_m = sum([(datetime.combine(datetime(2026,1,1), punches[i+1]) - datetime.combine(datetime(2026,1,1), punches[i])).total_seconds()/60 for i in range(0, len(punches), 2)])
        if min_m <= total_m <= max_m: return pd.Series([len(punches), 'Complete', 'Clean'])
        return pd.Series([len(punches), 'Defaulter', 'Defaulter Hours'])

    results = att_df.apply(analyze, axis=1)
    att_df[['Total', 'Status', 'Issue Type']] = results
    
    # History Merge
    history_counts = update_history(att_df[att_df['Issue Type'].isin(['Mispunch', 'Defaulter Hours'])])
    att_df = att_df.merge(history_counts, on='Clean_ID', how='left').fillna(0)

    # Views
    mispunches = att_df[att_df['Issue Type'] == 'Mispunch']
    defaulters = att_df[att_df['Issue Type'] == 'Defaulter Hours']
    repeated = att_df[att_df['Total Offenses'] > 1]
    
    # Dashboard
    c1, c2, c3, c4 = st.columns(4)
    if c1.button("👁️ View All", use_container_width=True): st.session_state.v = "all"
    if c2.button("🔄 Repeated", use_container_width=True): st.session_state.v = "repeated"
    if c3.button("⚠️ Mispunches", use_container_width=True): st.session_state.v = "mispunch"
    if c4.button("⏰ Defaulters", use_container_width=True): st.session_state.v = "defaulter"
    
    view = st.session_state.get("v", "all")
    final = {'all': att_df, 'repeated': repeated, 'mispunch': mispunches, 'defaulter': defaulters}[view]
    st.dataframe(final, use_container_width=True)
