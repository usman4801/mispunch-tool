import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

st.set_page_config(page_title="Attendance Tool", layout="wide")

st.title("Attendance & Defaulter Tool")

# File Uploaders
att_file = st.file_uploader("Upload Attendance File", type=["xlsx", "csv"])
ros_file = st.file_uploader("Upload Roster (HC.xlsx)", type=["xlsx"])

if att_file and ros_file:
    # Load Files
    df = pd.read_excel(att_file) if att_file.name.endswith('.xlsx') else pd.read_csv(att_file)
    ros = pd.read_excel(ros_file)
    
    # Clean Column Names
    df.columns = df.columns.str.strip()
    ros.columns = ros.columns.str.strip()
    
    # Mapping Roster: ID -> Working Hours
    # Assuming P.Soft ID is 1st column, Hours is last column
    id_col = ros.columns[0]
    hours_col = ros.columns[-1]
    
    ros_map = {}
    for _, r in ros.iterrows():
        id_val = str(r[id_col]).replace('.0', '').strip()
        hours_val = str(r[hours_col]).lower()
        ros_map[id_val] = 7 if '7' in hours_val else 9

    # Add Target Hours to Attendance
    df['Clean_ID'] = df.iloc[:, 0].astype(str).str.replace('.0', '', regex=False).str.strip()
    df['Target_Hours'] = df['Clean_ID'].map(ros_map).fillna(9)

    # Function to calculate status
    def check_status(row):
        target = row['Target_Hours']
        # Assume columns 4 to end are punches
        punches = [pd.to_datetime(str(val), errors='coerce') for val in row.iloc[4:10] if pd.notna(val)]
        if len(punches) < 2: return "Mispunch"
        
        duration = (punches[1] - punches[0]).total_seconds() / 3600
        
        # Buffer logic: 12 mins = 0.2 hours
        lower_limit = target - 0.2
        upper_limit = target + 0.2
        
        if lower_limit <= duration <= upper_limit:
            return "Clean"
        else:
            return "Defaulter"

    df['Status'] = df.apply(check_status, axis=1)
    
    st.write("Analysis Result:")
    st.dataframe(df)

    # Download
    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button("Download Report", csv, "Report.csv", "text/csv")
