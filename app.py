import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import base64

# Page Config & Hide Unwanted Traceback Errors
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
except Exception:
    pass

# Main UI Header
st.title("📊 Attendance Mispunch & Working Hours Detection System")

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
    # Identify which columns actually contain valid non-empty punches
    actual_punch_positions = []
    
    for idx, col in enumerate(punch_cols):
        val = parse_time(row[col])
        if val is not None:
            punches.append(val)
            actual_punch_positions.append(idx)
            
    total_punches = len(punches)
    
    status = "OK"
    category = "Complete"
    action = "-"
    working_hours_str = "N/A"
    issue_type = "Clean"
    
    # -------------------------------------------------------------
    # SPECIFIC CHECK: LAST SCAN PAR OUT MISSING (IN POSITION PAR HAIN)
    # -------------------------------------------------------------
    # Agar aakhri punch kisi Odd index wali location (IN column) par aya hai
    is_last_punch_an_in = False
    if total_punches > 0:
        last_punch_col_index = actual_punch_positions[-1]
        if last_punch_col_index % 2 == 0:  # 0, 2, 4 are IN columns
            is_last_punch_an_in = True

    # CASE 1: MISSING PUNCHES (Odd Punches: 1, 3, 5) OR LAST PUNCH IS IN
    if total_punches % 2 != 0 or is_last_punch_an_in:
        status = "Error"
        working_hours_str = "Incomplete (Missing Shift OUT)"
        issue_type = "Mispunch"
        
        if is_last_punch_an_in and total_punches % 2 == 0:
            category = "Shift END is IN (Missing Shift OUT)"
            action = f"Last scan {punches[-1].strftime('%H:%M')} is IN instead of OUT"
        elif total_punches == 1:
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
        else:
            category = f"Missing Scan ({total_punches} Punches)"
            action = f"Check sequence after {punches[-1].strftime('%H:%M')}"

    # CASE 2: EXTRA PUNCHES (7 or More Punches)
    elif total_punches >= 7:
        status = "Error"
        working_hours_str = "N/A (Extra Scans)"
        category = "Extra Punches"
        action = f"Review Extra Scans ({total_punches} Punches)"
        issue_type = "Mispunch"

    # CASE 3: VALID EVEN PAIRS (2, 4, 6 Punches where Last Scan is OUT)
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
    
    id_col = col_names[0]
    name_col = col_names[1]
    punch_cols = col_names[4:]
    
    st.subheader("📋 Processing Summary & Live Analysis")
    
    analysis_df = df.apply(lambda row: analyze_mispunches(row, punch_cols), axis=1)
    analysis_df.columns = ['Total Punches', 'No. of Working Hours', 'Status', 'Mispunch Category', 'Suggested Missing Action / Time', 'Issue Type']
    
    # Safe header renaming (IN / OUT)
    renamed_punch_cols = {}
    for idx, col in enumerate(punch_cols):
        pair_num = (idx // 2) + 1
        label = "IN" if idx % 2 == 0 else "OUT"
        if pair_num == 1:
            renamed_punch_cols[col] = label
        else:
            renamed_punch_cols[col] = f"{label} ({pair_num})"
            
    punches_df_renamed = df[punch_cols].rename(columns=renamed_punch_cols)
    
    # ID aur Name Columns
    base_info_df = df[[id_col, name_col]].copy()
    base_info_df.columns = ['P.Soft ID', 'Employee Name']
    
    # Merge Clean Table
    final_df = pd.concat([base_info_df, analysis_df, punches_df_renamed], axis=1)
    
    mispunches_only = final_df[final_df['Issue Type'] == "Mispunch"].copy()
    defaulter_hours_only = final_df[final_df['Issue Type'] == "Defaulter Hours"].copy()
    
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
            st.dataframe(defaulter_hours_only.drop(columns=['Issue Type']), use_container_width=True, hide_index=True)
        else:
            st.success("🎉 Koi Defaulter Working Hours wala record nahi mila!")

    elif "Missing & Extra Punches" in view_option:
        st.subheader(f"⚠️ Missing & Extra Punches List ({len(mispunches_only)} Records)")
        st.caption("Missing punches (1, 3, 5) ya Extra Scans (7+) wale employees ki list:")
        if len(mispunches_only) > 0:
            st.dataframe(mispunches_only.drop(columns=['Issue Type']), use_container_width=True, hide_index=True)
        else:
            st.success("🎉 Koi Mispunch / Extra Punch nahi mila!")

    else:
        st.subheader(f"📊 All Employee Records ({len(final_df)} Records)")
        st.dataframe(final_df.drop(columns=['Issue Type']), use_container_width=True, hide_index=True)

    st.markdown("---")
    
    # Safe Download Option (Standard pandas engine)
    @st.cache_data
    def convert_df(df_to_export):
        import io
        buffer = io.BytesIO()
        try:
            with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                df_to_export.drop(columns=['Issue Type']).to_excel(writer, index=False, sheet_name='Summary Report')
                mispunches_only.drop(columns=['Issue Type']).to_excel(writer, index=False, sheet_name='Mispunches')
                defaulter_hours_only.drop(columns=['Issue Type']).to_excel(writer, index=False, sheet_name='Defaulter Hours')
        except Exception:
            with pd.ExcelWriter(buffer) as writer:
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
