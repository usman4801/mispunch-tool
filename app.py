import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import base64

# Page Config
st.set_page_config(page_title="Attendance Mispunch Automation Tool", layout="wide")

# Function to encode JPEG image file
def get_base64_of_bin_file(bin_file):
    with open(bin_file, 'rb') as f:
        data = f.read()
    return base64.b64encode(data).decode()

image_filename = 'bg.jpeg.jpeg'

try:
    bin_str = get_base64_of_bin_file(image_filename)
    st.markdown(
        f"""
        <style>
        .stApp {{
            background-image: url("data:image/jpeg;base64,{bin_str}");
            background-size: cover;
            background-position: center;
            background-repeat: no-repeat;
            background-attachment: fixed;
        }}
        .block-container {{
            background-color: rgba(255, 255, 255, 0.90);
            padding: 2rem;
            border-radius: 12px;
            margin-top: 1.5rem;
            box-shadow: 0px 4px 15px rgba(0, 0, 0, 0.1);
        }}
        </style>
        """,
        unsafe_allow_html=True
    )
except Exception as e:
    st.error(f"Background image load nahi ho saki: {e}")

# Main UI Header
st.title("📊 Attendance Mispunch Detection & Automation System")
st.write("Apni attendance Excel/CSV file upload karein taake Mispunches, Missing Breaks, Duplicate Scans, aur Shift Hours auto-detect ho sakein.")

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
    working_hours_str = "N/A"
    
    # -------------------------------------------------------------
    # CASE 1: MISSING PUNCHES (Odd Punches: 1, 3, 5)
    # -------------------------------------------------------------
    if total_punches % 2 != 0:
        status = "Error"
        working_hours_str = "Incomplete (Missing Punch)"
        
        if total_punches == 1:
            category = "Single Scan Only"
            action = "Missing Shift OUT or Shift IN"
            
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
            action = f"Break Return missing after {punches[3].strftime('%H:%M')}"

    # -------------------------------------------------------------
    # CASE 2: EXTRA PUNCHES (7 or More Punches)
    # -------------------------------------------------------------
    elif total_punches >= 7:
        status = "Error"
        working_hours_str = "N/A (Extra Scans)"
        category = "Extra Punches"
        action = f"Review Extra Scans ({total_punches} Punches)"

    # -------------------------------------------------------------
    # CASE 3: COMPLETE PAIRS (2, 4, 6 Punches)
    # Shift timing chahay kuch bhi ho, agar Net Hours poore hain toh OK
    # -------------------------------------------------------------
    elif total_punches in [2, 4, 6]:
        dummy_date = datetime(2026, 1, 1)
        total_seconds = 0
        
        # Pairs mein net work calculate karenge (e.g. 1-to-2, 3-to-4, 5-to-6)
        for i in range(0, total_punches, 2):
            start_dt = datetime.combine(dummy_date, punches[i])
            end_dt = datetime.combine(dummy_date, punches[i+1])
            
            # Overnight shift handling
            if end_dt < start_dt:
                end_dt += timedelta(days=1)
            
            total_seconds += (end_dt - start_dt).total_seconds()
        
        hours = int(total_seconds // 3600)
        minutes = int((total_seconds % 3600) // 60)
        
        working_hours_str = f"{hours:02d}:{minutes:02d}"
        
        # Working Hours Allowed Limits:
        # 8 hours 50 mins = 31,800 seconds
        # 9 hours 10 mins = 33,000 seconds
        min_allowed_seconds = (8 * 3600) + (50 * 60) # 31800 sec
        max_allowed_seconds = (9 * 3600) + (10 * 60) # 33000 sec
        
        if total_seconds < min_allowed_seconds:
            status = "Error"
            category = "Short Working Hours (< 08:50)"
            action = f"Net working time ({working_hours_str}) is less than 8h 50m"
        elif total_seconds > max_allowed_seconds:
            status = "Error"
            category = "Overtime / Excessive Hours (> 09:10)"
            action = f"Net working time ({working_hours_str}) is more than 9h 10m"
        else:
            status = "OK"
            category = "Complete"
            action = "-"

    return pd.Series([total_punches, working_hours_str, status, category, action])

if uploaded_file is not None:
    if uploaded_file.name.endswith('.csv'):
        df = pd.read_csv(uploaded_file)
    else:
        df = pd.read_excel(uploaded_file)
        
    col_names = df.columns.tolist()
    
    id_col = col_names[0]
    name_col = col_names[1]
    manager_col = col_names[2]
    shift_col = col_names[3]
    punch_cols = col_names[4:]
    
    st.subheader("📋 Processing Summary & Live Analysis")
    
    analysis_df = df.apply(lambda row: analyze_mispunches(row, punch_cols), axis=1)
    analysis_df.columns = ['Total Punches', 'No. of Working Hours', 'Status', 'Mispunch Category', 'Suggested Missing Action / Time']
    
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
