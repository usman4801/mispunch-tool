import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import base64
import io

st.set_page_config(page_title="Attendance Tool", layout="wide")

# ... (CSS code wahi purana rakhen)

# 1. Roster load karte waqt hi header clean kar dein
@st.cache_data
def load_permanent_roster():
    try:
        ros = pd.read_excel('HC.xlsx', sheet_name='Roster')
        ros.columns = [str(c).strip() for c in ros.columns.tolist()] # Spaces khatam
        return ros
    except:
        return None

ros_df = load_permanent_roster()

# 2. Shift mapping function ko direct merge ki zaroorat nahi, 
# hum yahan dictionary bana kar lookup karenge
def get_shift_from_roster(psoft_id, ros_df):
    if ros_df is None: return "Day"
    # Psoft ID ko string bana kar match karein
    match = ros_df[ros_df['Psoft ID'].astype(str) == str(psoft_id)]
    if not match.empty:
        # Check karein 'Shift timings' ya 'Shift' jo bhi column ho
        for col in ['Shift timings', 'Shift timings ', 'Shift']:
            if col in match.columns:
                val = str(match.iloc[0][col]).lower()
                if 'night' in val: return "Night"
                if 'mid' in val: return "Mid"
                if 'day' in val: return "Day"
    return "Day"

# ... (parse_time function wahi rahay ga)

# 3. Mispunch analysis mein direct lookup
def analyze_mispunches(row, punch_cols, mode, ros_df):
    # Shift detection lookup
    psoft_val = row.get('Psoft ID') # Apni file ka ID column
    shift_val = get_shift_from_roster(psoft_val, ros_df)
    
    # Baaki logic same...
    # (Punches calculation code)
    # ...
    return pd.Series([total_punches, shift_val, ...])

# Main processing block mein:
# df['Shift'] = df.apply(lambda row: get_shift_from_roster(row['Psoft ID'], ros_df), axis=1)
