import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import base64
import io

st.set_page_config(page_title="Attendance Mispunch Intelligence", layout="wide")

def get_base64_of_bin_file(bin_file):
    try:
        with open(bin_file, 'rb') as f:
            data = f.read()
        return base64.b64encode(data).decode()
    except:
        return ""

# Background and CSS
image_filename = 'bg.jpeg.jpeg'
bin_str = get_base64_of_bin_file(image_filename)
st.markdown(f"""
    <style>
    .stApp {{ background-image: url("data:image/jpeg;base64,{bin_str}"); background-size: cover; }}
    .block-container {{ background-color: rgba(255, 255, 255, 0.92); padding: 2rem; border-radius: 12px; }}
    </style>
""", unsafe_allow_html=True)

st.title("📊 Attendance Mispunch & Defaulter Analyzer")

attendance_file = st.file_uploader("Upload Attendance File", type=["xlsx", "xls", "csv"])

@st.cache_data
def load_permanent_roster():
    try:
        ros = pd.read_excel('HC.xlsx', sheet_name='Roster')
        ros.columns = [str(c).strip() for c in ros.columns.tolist()]
        return ros
    except:
        return None

ros_df = load_permanent_roster()

def parse_time(time_val):
    if pd.isna(time_val) or str(time_val).strip().lower() in ["nan", "none", ""]: return None
    time_str = str(time_val).strip()
    for fmt in ["%H:%M:%S", "%H:%M", "%I:%M:%S %p", "%I:%M %p", "%I:%M%p"]:
        try: return datetime.strptime(time_str, fmt).time()
        except ValueError: continue
    return None

if attendance_file is not None:
    att_df = pd.read_excel(attendance_file)
    att_df.columns = [str(c).strip() for c in att_df.columns.tolist()]
    
    # ID cleaning
    id_col = next((c for c in att_df.columns if 'psoft' in c.lower()), att_df.columns[1])
    att_df['Clean_ID'] = att_df[id_col].astype(str).str.replace(r'\.0$', '', regex=True).str.strip()
    
    # Roster Mapping
    shift_map = {}
    if ros_df is not None:
        ros_id_col = next((c for c in ros_df.columns if 'psoft' in c.lower()), ros_df.columns[1])
        shift_col = next((c for c in ros_df.columns if 'shift' in c.lower()), None)
        for _, r in ros_df.iterrows():
            r_id = str(r[ros_id_col]).replace('.0', '').strip()
            val = str(r[shift_col]).lower() if shift_col else ""
            shift_map[r_id] = "Night" if 'night' in val else "Mid" if 'mid' in val else "Day"
    
    df = att_df.copy()
    df['Shift_Roster'] = df['Clean_ID'].map(shift_map).fillna("Day")
    
    punch_cols = [c for c in att_df.columns if c.lower() not in ['psoft id', 'employee name', 'clean_id', 'shift', 'working hours', 'no of breaks ']]

    def analyze_row(row):
        punches = [parse_time(row.get(col)) for col in punch_cols if parse_time(row.get(col)) is not None]
        total_punches = len(punches)
        shift_val = row.get('Shift_Roster', 'Day')
        
        # Working hours logic
        target_hours = 7 if '7' in str(row.get('Working Hours', '9')).lower() else 9
        min_mins = 527 if target_hours == 9 else 407
        max_mins = 552 if target_hours == 9 else 432
        
        if total_punches == 0: return pd.Series([0, shift_val, "00:00", "Absent", "Clean"])
        
        if total_punches == 1:
            p = punches[0]
            p_mins = p.hour * 60 + p.minute
            # FIX: Night shift end (8 AM) is clean, not mispunch
            if shift_val == "Night" and (7 * 60 <= p_mins <= 9 * 60):
                return pd.Series([1, shift_val, "N/A", "Shift End (Clean)", "Clean"])
            return pd.Series([1, shift_val, "N/A", "Single Scan", "Mispunch"])

        # Duration Calc
        total_dur = 0
        for i in range(0, total_punches - (total_punches % 2), 2):
            s = datetime.combine(datetime(2026,1,1), punches[i])
            e = datetime.combine(datetime(2026,1,1), punches[i+1])
            if e < s: e += timedelta(days=1)
            total_dur += (e - s).total_seconds()
        
        eff_mins = (total_dur / 60) - int(str(row.get('No of breaks ', '0'))[:2])
        if total_punches % 2 != 0: return pd.Series([total_punches, shift_val, "N/A", "Incomplete", "Mispunch"])
        if min_mins <= eff_mins <= max_mins: return pd.Series([total_punches, shift_val, f"{int(total_dur//3600)}h", "Complete", "Clean"])
        return pd.Series([total_punches, shift_val, f"{int(total_dur//3600)}h", "Defaulter Hours", "Defaulter Hours"])

    analysis = df.apply(analyze_row, axis=1)
    analysis.columns = ['Total Punches', 'Shift', 'Hours', 'Status', 'Issue Type']
    final_df = pd.concat([df[[id_col]], analysis], axis=1)
    
    st.dataframe(final_df, use_container_width=True)
    
    # Download
    csv = final_df.to_csv(index=False).encode('utf-8')
    st.download_button("Download Report", data=csv, file_name="Report.csv")
