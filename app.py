import streamlit as st
import pandas as pd

st.set_page_config(page_title="Mispunch Automation Tool", layout="wide")

st.title("📊 Attendance Mispunch Automation")
st.write("Apni attendance Excel/CSV file upload karein aur automated mispunch status hasil karein.")

uploaded_file = st.file_uploader("Upload Attendance File (Excel / CSV)", type=["xlsx", "csv"])

if uploaded_file is not None:
    try:
        if uploaded_file.name.endswith('.csv'):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file)
            
        st.success("File Successfully Uploaded!")
        
        st.subheader("📋 Preview Data")
        st.dataframe(df.head())
        
        st.subheader("⚙️ Data Summary")
        st.write(f"Total Records: {len(df)}")
        
        st.download_button(
            label="📥 Download Processed File",
            data=uploaded_file.getvalue(),
            file_name="processed_attendance.xlsx",
            mime="application/vnd.ms-excel"
        )
        
    except Exception as e:
        st.error(f"Error reading file: {e}")
