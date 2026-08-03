import streamlit as st
import pandas as pd
import numpy as np

st.set_page_config(page_title="Attendance Mispunch Automation Tool", layout="wide")

st.title("📊 Attendance Mispunch Detection System")
st.write("Apni attendance Excel file upload karein taake Mispunches (Missing IN/OUT) auto-detect ho sakein.")

uploaded_file = st.file_uploader("Upload Excel File", type=["xlsx", "xls", "csv"])

def process_attendance(df):
    # Punch columns list
    punch_cols = [col for col in df.columns if 'punch' in col.lower()]
    
    # 1. Total Punches Count
    df['Total_Punches'] = df[punch_cols].notna().sum(axis=1)
    
    # 2. Mispunch Logic (Odd counts = Mispunch, Even = Complete)
    df['Status'] = np.where(df['Total_Punches'] % 2 != 0, 'Mispunch (Missing IN/OUT)', 'Complete')
    
    # 3. Shift Detection (Based on 1st Punch)
    if len(punch_cols) > 0:
        first_punch = pd.to_datetime(df[punch_cols[0]], errors='coerce')
        hour = first_punch.dt.hour
        
        # Day Shift: 8 AM to 6 PM (8-18), Night Shift: 6 PM to 4 AM
        df['Shift_Type'] = np.where((hour >= 8) & (hour < 18), 'Day Shift', 'Night Shift')
    
    return df

if uploaded_file is not None:
    try:
        if uploaded_file.name.endswith('.csv'):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file)
            
        st.success("File Successfully Uploaded!")
        
        # Process Data
        processed_df = process_attendance(df)
        
        # Display Mispunch Summary
        mispunch_count = len(processed_df[processed_df['Status'].str.contains('Mispunch')])
        total_records = len(processed_df)
        
        col1, col2 = st.columns(2)
        col1.metric("Total Records", total_records)
        col2.metric("Total Mispunches Detected", mispunch_count, delta_color="inverse")
        
        st.subheader("📋 Processed Data Preview")
        st.dataframe(processed_df.head(10))
        
        # Export to Excel
        output_name = "Processed_Attendance.xlsx"
        processed_df.to_excel(output_name, index=False)
        
        with open(output_name, "rb") as file:
            st.download_button(
                label="📥 Download Processed Excel File",
                data=file,
                file_name=output_name,
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
            
    except Exception as e:
        st.error(f"Error processing file: {e}")
