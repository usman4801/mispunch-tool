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
        div[data-testid="stRadioButton"] > div {{
            flex-direction: row;
            gap: 15px;
        }}
        </style>
        """,
        unsafe_allow_html=True
    )
except Exception as e:
    st.error(f"Background image load nahi ho saki: {e}")

# Main UI Header
st.title("📊 Attendance Mispunch & Working Hours Detection System")
st.write("Apni attendance Excel/CSV file upload karein taake Mispunches, Missing Breaks, Extra Scans, aur Defaulter Hours auto-detect ho sakein.")

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
    issue_type = "Clean"
    
    # -------------------------------------------------------------
    # CASE 1: MISSING PUNCHES (Odd Punches: 1, 3, 5)
    # -------------------------------------------------------------
    if total_punches % 2 != 0:
        status = "Error"
        working_hours_str = "Incomplete (Missing Punch)"
        issue_type = "Mispunch"
        
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
        issue_type = "Mispunch"

    # -------------------------------------------------------------
    # CASE 3: COMPLETE PAIRS (2, 4, 6 Punches)
    # -------------------------------------------------------------
    elif total_punches in [2, 4, 6]:
        dummy_date = datetime(2026, 1, 1)
        total_seconds = 0
        
        for i in range(0, total_punches, 2):
            start_dt = datetime.combine(dummy_date, punches[i])
            end_dt = datetime.combine(dummy_date, punches[i+1])
            
            if end_dt < start_dt:
                end_dt += timedelta(days=1)
            
            total_seconds += (end_dt - start_dt).total_seconds()
        
        hours = int(total_seconds // 3600)
        minutes = int((total_seconds % 3600) // 60)
        
        working_hours_str = f"{hours:02d}:{minutes:02d}"
        
        min_allowed_seconds = (8 * 3600) + (50 * 60) # 31800 sec
        max_allowed_seconds = (9 * 3600) + (10 * 60) # 33000 sec
        
        if total_seconds < min_allowed_seconds:
            status = "Error"
            category = "Short Working Hours (< 08:50)"
            action = f"Net working time ({working_hours_str}) is less than 8h 50m"
            issue_type = "Defaulter Hours"
        elif total_seconds > max_allowed_seconds:
            status = "Error"
            category = "Overtime / Excessive Hours (> 09:10)"
            action = f"Net working time ({working_hours_str}) is more than 9h 10m"
            issue_type = "Defaulter Hours"
        else:
            status = "OK"
            category = "Complete"
            action = "-"
            issue_type = "Clean"

    return pd.Series([total_punches, working_hours_str, status, category, action, issue_type])

if uploaded_file is not None:
    if uploaded_file.name.endswith('.csv'):
        df = pd.read_csv(uploaded_file)
    else:
        df = pd.read_excel(uploaded_file)
        
    col_names = df.columns.tolist()
    
    # Sirf pehle 2 main identifier columns rakhenge (e.g., ID aur Employee Name)
    id_col = col_names[0]
    name_col = col_names[1]
    punch_cols = col_names[4:]
    
    st.subheader("📋 Processing Summary & Live Analysis")
    
    analysis_df = df.apply(lambda row: analyze_mispunches(row, punch_cols), axis=1)
    analysis_df.columns = ['Total Punches', 'No. of Working Hours', 'Status', 'Mispunch Category', 'Suggested Missing Action / Time', 'Issue Type']
    
    # Column 2 aur Column 3 (Unnamed: 2, Unnamed: 3) yahan ignore kar diye gaye hain
    final_df = pd.concat([df[[id_col, name_col]], analysis_df, df[punch_cols]], axis=1)
    
    mispunches_only = final_df[final_df['Issue Type'] == "Mispunch"]
    defaulter_hours_only = final_df[final_df['Issue Type'] == "Defaulter Hours"]
    total_errors = len(mispunches_only) + len(defaulter_hours_only)
    
    # Top Counters
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Records", len(final_df))
    col2.metric("Clean Records", len(final_df) - total_errors)
    col3.metric("Mispunches", len(mispunches_only))
    col4.metric("Defaulter Hours", len(defaulter_hours_only))
    
    st.markdown("---")
    
    # VIEW SELECTOR BUTTONS
    view_option = st.radio(
        "🔎 **Select List View to Inspect:**",
        options=[
            f"⚠️ Missing & Extra Punches ({len(mispunches_only)})", 
            f"⏰ Defaulter Hours List ({len(defaulter_hours_only)})",
            f"📊 All Records ({len(final_df)})"
        ],
        index=0
    )
    
    st.markdown("---")

    # DISPLAY LIST BASED ON SELECTION
    if "Defaulter Hours" in view_option:
        st.subheader(f"⏰ Defaulter Working Hours List ({len(defaulter_hours_only)} Records)")
        st.caption("Net working hours < 08:50 or > 09:10 wale employees ki list:")
        if len(defaulter_hours_only) > 0:
            st.dataframe(defaulter_hours_only.drop(columns=['Issue Type']), use_container_width=True)
        else:
            st.success("🎉 Koi Defaulter Working Hours wala record nahi mila!")

    elif "Missing & Extra Punches" in view_option:
        st.subheader(f"⚠️ Missing & Extra Punches List ({len(mispunches_only)} Records)")
        st.caption("Missing punches (1, 3, 5) ya Extra Scans (7+) wale employees ki list:")
        if len(mispunches_only) > 0:
            st.dataframe(mispunches_only.drop(columns=['Issue Type']), use_container_width=True)
        else:
            st.success("🎉 Koi Mispunch / Extra Punch nahi mila!")

    else:
        st.subheader(f"📊 All Employee Records ({len(final_df)} Records)")
        st.dataframe(final_df.drop(columns=['Issue Type']), use_container_width=True)

    st.markdown("---")
    
    # Download Option
    @st.cache_data
    def convert_df(df_to_export):
        import io
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
            df_to_export.drop(columns=['Issue Type']).to_excel(writer, index=False, sheet_name='Summary Report')
            mispunches_only.drop(columns=['Issue Type']).to_excel(writer, index=False, sheet_name='Mispunches')
            defaulter_hours_only.drop(columns=['Issue Type']).to_excel(writer, index=False, sheet_name='Defaulter Hours')
        return buffer.getvalue()

    excel_data = convert_df(final_df)
    st.download_button(
        label="📥 Download Complete Report (Multi-Sheet Excel)",
        data=excel_data,
        file_name="Refined_Attendance_Report.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
