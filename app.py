import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

# Page Config
st.set_page_config(page_title="Attendance Mispunch Automation Tool", layout="wide")

# ==========================================
# BACKGROUND IMAGE CONFIGURATION
# Yahan quotes (" ") ke andar apni GitHub raw image ka link paste karein
# ==========================================
bg_image_url = "https://raw.githubusercontent.com/usman4801/mispunch-tool/main/bg.jpg"

st.markdown(
    f"""
    <style>
    /* Background Image setup */
    .stApp {{
        background-image: url("{bg_image_url}");
        background-size: cover;
        background-position: center;
        background-repeat: no-repeat;
        background-attachment: fixed;
    }}

    /* Card background for readable text */
    .block-container {{
        background-color: rgba(255, 255, 255, 0.90);
        padding: 2rem;
        border-radius: 12px;
        margin-top: 2rem;
        box-shadow: 0px 4px 15px rgba(0, 0, 0, 0.1);
    }}
    </style>
    """,
    unsafe_allow_html=True
)

# Main UI Header
st.title("📊 Attendance Mispunch Detection & Automation System")
st.write("Apni attendance Excel/CSV file upload karein taake Mispunches, Missing Breaks, aur Duplicate Scans auto-detect ho sakein.")

uploaded_file = st.file_uploader("Upload Excel/CSV File", type=["xlsx", "xls", "csv"])

def parse_time(time_val):
    if pd.isna(time_val) or str(time_val).strip().lower() in ["nan", "none", ""]:
        return None
    time_str = str(time_val).strip()
    for fmt in ["%H:%M:%S", "%H:%M", "%I:%M:%S %p", "%I:%M %p", "%I:%M%p"]:
        try:
            return datetime.strptime(time_str, fmt).time()
        except ValueError:
            continue
    return None

def analyze_mispunches(row, punch_cols):
    punches = []
    for col in punch_cols:
        val = parse_time(row[col])
        if val is not None:
            punches.append(val)
            
    total_punches = len(punches)
    
    status = "OK"
    category = "Complete"
    action = "-"
    
    # 1. Duplicate Scans (7+ Punches)
    if total_punches in [7, 8, 9, 10]:
        status = "Error"
        category = "Duplicate / Extra Scans"
        action = f"Review Extra Scans ({total_punches} Punches)"
        
    # 2. Odd Punch Cases (Mispunches)
    elif total_punches % 2 != 0:
        status = "Error"
        if total_punches == 1:
            category = "Single Scan Only"
            action = "Check Shift IN / OUT"
            
        elif total_punches == 3:
            category = "Missing Break / Shift IN (3 Punches)"
            p1 = punches[0]
            if 10 <= p1.hour < 12:
                action = "Missing Shift Start (Suggested: 08:00 AM)"
            elif 20 <= p1.hour < 23:
                action = "Missing Shift Start (Suggested: 18:00 PM)"
            else:
                action = f"Missing Break Return after {punches[1].strftime('%H:%M')}"
                
        elif total_punches == 5:
            category = "Missing Break Return (5 Punches)"
            action = f"30-min Break Return missing after {punches[3].strftime('%H:%M')}"
            
    return pd.Series([total_punches, status, category, action])

if uploaded_file is not None:
    if uploaded_file.name.endswith('.csv'):
        df = pd.read_csv(uploaded_file)
    else:
        df = pd.read_excel(uploaded_file)
        
    col_names = df.columns.tolist()
    
    # Standard format: First 4 columns are metadata (ID, Name, Manager, Shift/Location)
    id_col = col_names[0]
    name_col = col_names[1]
    manager_col = col_names[2]
    shift_col = col_names[3]
    punch_cols = col_names[4:]
    
    st.subheader("📋 Processing Summary & Live Analysis")
    
    analysis_df = df.apply(lambda row: analyze_mispunches(row, punch_cols), axis=1)
    analysis_df.columns = ['Total Punches', 'Status', 'Mispunch Category', 'Suggested Missing Action / Time']
    
    final_df = pd.concat([df[[id_col, name_col, manager_col, shift_col]], analysis_df, df[punch_cols]], axis=1)
    
    mispunches_df = final_df[final_df['Status'] == "Error"]
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Records Processed", len(final_df))
    col2.metric("Clean Records (No Issue)", len(final_df) - len(mispunches_df))
    col3.metric("Mispunches Detected", len(mispunches_df))
    
    st.markdown("---")
    st.subheader("⚠️ Mispunches & Action Required List")
    
    if len(mispunches_df) > 0:
        st.dataframe(mispunches_df, use_container_width=True)
        
        # Download Option
        @st.cache_data
        def convert_df(df_to_export):
            import io
            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
                df_to_export.to_excel(writer, index=False, sheet_name='MisPunch Summary')
            return buffer.getvalue()

        excel_data = convert_df(final_df)
        st.download_button(
            label="📥 Download Clean / Refined Excel File",
            data=excel_data,
            file_name="Refined_Mispunch_Report.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    else:
        st.success("🎉 Mispunch nahi mila! Sabhi records complete hain.")
