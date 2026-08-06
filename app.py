import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import base64

# Page Config
st.set_page_config(page_title="Attendance Intelligence", layout="wide")

# (Styling remains the same for cleaner UI)
# ... [Keeping CSS same for brevity] ...

def get_base64_of_bin_file(bin_file):
    with open(bin_file, 'rb') as f:
        data = f.read()
    return base64.b64encode(data).decode()

# ... [Loading Background Logic] ...

# --- Shift Detection Helper ---
def get_shift_type(shift_timing_raw):
    s = str(shift_timing_raw).lower()
    if any(x in s for x in ['night', '18:00', '19:00', 'pm']): return "Night"
    if any(x in s for x in ['mid', '12:00', '13:00']): return "Mid"
    return "Day"

def analyze_mispunches(row, punch_cols, mode):
    punches = []
    actual_punch_positions = []
    for idx, col in enumerate(punch_cols):
        val = parse_time(row.get(col))
        if val is not None:
            punches.append(val)
            actual_punch_positions.append(idx)
            
    total_punches = len(punches)
    shift_raw = str(row.get('Shift timings ', ''))
    shift_val = get_shift_type(shift_raw)
    
    # Logic for Mispunch Check
    if total_punches == 0:
        return pd.Series([0, shift_val, "N/A", "OK", "No Punches / Absent", "Clean"])

    # Single Scan Intelligence
    if total_punches == 1:
        single_punch = punches[0]
        punch_total_mins = single_punch.hour * 60 + single_punch.minute
        
        # If Night Shift or evening timing (17:00+) - Ignore as Shift Start
        if punch_total_mins >= 17 * 60:
            return pd.Series([1, shift_val, "N/A", "OK", "Shift Start (Clean)", "Clean"])
        else:
            return pd.Series([1, shift_val, "N/A", "Error", "Single Scan Only", "Mispunch"])

    # Basic multi-punch mispunch check
    is_last_punch_an_in = (actual_punch_positions[-1] % 2 == 0)
    
    if total_punches % 2 != 0 or is_last_punch_an_in:
        return pd.Series([total_punches, shift_val, "N/A", "Error", f"Missing Scan ({total_punches})", "Mispunch"])

    # Calculate Working Hours
    dummy_date = datetime(2026, 1, 1)
    total_seconds = sum((datetime.combine(dummy_date, punches[i+1]) - datetime.combine(dummy_date, punches[i])).total_seconds() 
                        for i in range(0, total_punches, 2))
    hours_str = f"{int(total_seconds // 3600):02d}:{int((total_seconds % 3600) // 60):02d}"
    
    return pd.Series([total_punches, shift_val, hours_str, "OK", "Complete", "Clean"])

# --- Main App Logic ---
if attendance_file is not None:
    # ... [Reading & Merging Logic] ...
    
    # Apply Analysis
    analysis_df = df.apply(lambda row: analyze_mispunches(row, punch_cols, upload_mode), axis=1)
    analysis_df.columns = ['Total Punches', 'Shift', 'No. of\nWorking Hours', 'Status', 'Mispunch Category', 'Issue Type']
    
    # RE-ORDER COLUMNS FOR CLEAN VIEW:
    # We want: P.Soft ID, Name, Total Punches, Shift, Status, Mispunch Category, [Punches...], Issue Type (End)
    
    # ... (Concatenation Logic) ...
    
    # Final cleanup of columns order for Display
    display_cols = ['P.Soft ID', 'Employee Name', 'Total Punches', 'Shift', 'Status', 'Mispunch Category'] + list(punches_df_cleaned.columns) + ['Issue Type']
    final_df = final_df[display_cols]
    
    # Now display with the new order
    st.dataframe(active_display_df[display_cols], use_container_width=True)
