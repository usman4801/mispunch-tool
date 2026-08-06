import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import base64

# Page Config
st.set_page_config(page_title="Attendance Intelligence", layout="wide")

def get_base64_of_bin_file(bin_file):
    with open(bin_file, 'rb') as f:
        data = f.read()
    return base64.b64encode(data).decode()

# (Styling remains the same for cleaner UI)
# ... [Keeping CSS same for brevity] ...

def parse_time(time_val):
    if pd.isna(time_val) or str(time_val).strip().lower() in ["nan", "none", ""]: return None
    time_str = str(time_val).strip()
    for fmt in ["%H:%M:%S", "%H:%M", "%I:%M:%S %p", "%I:%M %p", "%I:%M%p"]:
        try: return datetime.strptime(time_str, fmt).time()
        except ValueError: continue
    return None

def analyze_mispunches(row, punch_cols):
    punches = []
    for col in punch_cols:
        val = parse_time(row.get(col))
        if val is not None: punches.append(val)
            
    total_punches = len(punches)
    
    # NEW INTELLIGENCE:
    # 1. Agar sirf 1 punch hai, to ye "Shift Start" hai (Night Shift ka 1st punch), mispunch nahi.
    if total_punches == 1:
        return pd.Series([1, "N/A", "OK", "Shift Transition Start (Clean)", "Clean"])

    # 2. Agar 2 ya us se zyada punches hain, tabhi mispunch logic check karo
    if total_punches == 0:
        return pd.Series([0, "N/A", "OK", "No Punches / Absent", "Clean"])

    # Basic Mispunch check for 2+ punches
    if total_punches % 2 != 0:
        return pd.Series([total_punches, "N/A", "Error", f"Missing Scan ({total_punches} Punches)", "Mispunch"])

    # Working Hours Logic for full day/shift data
    dummy_date = datetime(2026, 1, 1)
    total_seconds = 0
    for i in range(0, total_punches, 2):
        start_dt = datetime.combine(dummy_date, punches[i])
        end_dt = datetime.combine(dummy_date, punches[i+1])
        if end_dt < start_dt: end_dt += timedelta(days=1)
        total_seconds += (end_dt - start_dt).total_seconds()
    
    hours = int(total_seconds // 3600)
    minutes = int((total_seconds % 3600) // 60)
    working_hours_str = f"{hours:02d}:{minutes:02d}"
    
    return pd.Series([total_punches, working_hours_str, "OK", "Complete", "Clean"])

# --- Main App Logic ---
if attendance_file is not None:
    # ... [Reading File Logic] ...
    
    # 1. Merge with Roster
    df = pd.merge(att_df, ros_df[['Psoft ID', 'Shift timings ']], left_on=att_id_col, right_on='Psoft ID', how='left')

    # 2. Apply the new Punch-Aware Logic
    analysis_df = df.apply(lambda row: analyze_mispunches(row, punch_cols), axis=1)
    analysis_df.columns = ['Total Punches', 'Working Hours', 'Status', 'Mispunch Category', 'Issue Type']
    
    # ... [Rest of the display logic] ...
