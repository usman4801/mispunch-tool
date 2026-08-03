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
        div[data-testid="stMetric"] {{
            background-color: #f8f9fa;
            padding: 10px;
            border-radius: 8px;
            border: 1px solid #e9ecef;
        }}
        /* Enable multiline header wrapping & freeze column resizing */
        div[data-testid="stDataFrame"] th {{
            white-space: pre-wrap !important;
            word-wrap: break-word !important;
        }}
        div[data-testid="stDataFrame"] [data-testid="stDataFrameResizable"] {{
            pointer-events: none !important;
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

def format_time_clean(time_val):
    t = parse_time(time_val)
    if t is not None:
        return t.strftime("%H:%M")
    return ""

def analyze_mispunches(row, punch_cols):
    punches = []
    actual_punch_positions = []
    
    for idx, col in enumerate(punch_cols):
        val = parse_time(row[col])
        if val is not None:
            punches.append(val)
            actual_punch_positions.append(idx)
            
    total_punches = len(punches)
    
    status = "OK"
    category = "Complete"
    working_hours_str = "N/A"
    issue_type = "Clean"
    
    # Check if last punch was logged at an IN column
    is_last_punch_an_in = False
    if total_punches > 0:
        last_punch_col_index = actual_punch_positions[-1]
        if last_punch_col_index % 2 == 0:  # 0, 2, 4 are IN columns
            is_last_punch_an_in = True

    # CASE 1: MISSING PUNCHES OR LAST PUNCH IS IN
    if total_punches % 2 != 0 or is_last_punch_an_in:
        status = "Error"
        working_hours_str = "Incomplete (Missing Shift OUT)"
        issue_type = "Mispunch"
        
        if is_last_punch_an_in and total_punches % 2 == 0:
            category = "Shift END is IN (Missing Shift OUT)"
        elif total_punches == 1:
            category = "Single Scan Only"
        elif total_punches == 3:
            category = "Missing Break / Shift IN (3 Punches)"
        elif total_punches == 5:
            category = "Missing Break Return (5 Punches)"
        else:
            category = f"Missing Scan ({total_punches} Punches)"

    # CASE 2: EXTRA PUNCHES (7 or More Punches)
    elif total_punches >= 7:
        status = "Error"
        working_hours_str = "N/A (Extra Scans)"
        category = "Extra Punches"
        issue_type = "Mispunch"

    # CASE 3: VALID EVEN PAIRS
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
            issue_type = "Defaulter Hours"
        elif total_seconds > max_allowed_seconds:
            status = "Error"
            category = "Overtime / Excessive Hours (> 09:10)"
            issue_type = "Defaulter Hours"
        else:
            status = "OK"
            category = "Complete"
            issue_type = "Clean"

    return pd.Series([total_punches, working_hours_str, status, category, issue_type])

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
    analysis_df.columns = ['Total Punches', 'No. of Working Hours', 'Status', 'Mispunch Category', 'Issue Type']
    
    # Safe header renaming (IN / OUT) and Clean HH:MM Time Formatting
    renamed_punch_cols = {}
    punches_df_cleaned = pd.DataFrame()
    
    for idx, col in enumerate(punch_cols):
        pair_num = (idx // 2) + 1
        label = "IN" if idx % 2 == 0 else "OUT"
        col_label = label if pair_num == 1 else f"{label} ({pair_num})"
        
        renamed_punch_cols[col] = col_label
        punches_df_cleaned[col_label] = df[col].apply(format_time_clean)
    
    # ID aur Name Columns
    base_info_df = df[[id_col, name_col]].copy()
    base_info_df.columns = ['P.Soft ID', 'Employee Name']
    
    # REPEATED OFFENDER NUMBER COUNTER
    base_info_df['Repeated Offender'] = base_info_df.groupby('P.Soft ID').cumcount() + 1
    
    # Merge Clean Table
    final_df = pd.concat([base_info_df, analysis_df, punches_df_cleaned], axis=1)
    
    # Rearrange columns
    cols_order = (
        ['P.Soft ID', 'Employee Name', 'Repeated Offender', 'No. of Working Hours', 'Mispunch Category', 'Issue Type'] 
        + list(punches_df_cleaned.columns) 
        + ['Total Punches', 'Status']
    )
    final_df = final_df[cols_order]

    mispunches_only = final_df[final_df['Issue Type'] == "Mispunch"].copy()
    defaulter_hours_only = final_df[final_df['Issue Type'] == "Defaulter Hours"].copy()
    clean_records_only = final_df[final_df['Issue Type'] == "Clean"].copy()
    
    total_errors = len(mispunches_only) + len(defaulter_hours_only)
    
    # Initialize Session State for Active View Filter
    if "selected_view" not in st.session_state:
        st.session_state.selected_view = "mispunches"
        
    # TOP INTERACTIVE CARDS (CLICK TO FILTER)
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Records", len(final_df))
        if st.button("👁️ View All Records", key="btn_all", use_container_width=True):
            st.session_state.selected_view = "all"
            
    with col2:
        st.metric("Clean Records", len(clean_records_only))
        if st.button("👁️ View Clean List", key="btn_clean", use_container_width=True):
            st.session_state.selected_view = "clean"
            
    with col3:
        st.metric("Mispunches", len(mispunches_only))
        if st.button("⚠️ View Mispunches", key="btn_mispunch", type="primary", use_container_width=True):
            st.session_state.selected_view = "mispunches"
            
    with col4:
        st.metric("Defaulter Hours", len(defaulter_hours_only))
        if st.button("⏰ View Defaulters", key="btn_defaulters", use_container_width=True):
            st.session_state.selected_view = "defaulters"
            
    st.markdown("---")

    # Column configuration settings
    column_config_settings = {
        "Repeated Offender": st.column_config.NumberColumn(
            "Repeated\nOffender", 
            width="small"
        ),
        "Total Punches": st.column_config.NumberColumn(
            "Total\nPunches", 
            width="small"
        ),
        "No. of Working Hours": st.column_config.TextColumn(
            "No. of\nWorking Hours", 
            width="medium"  # Width increased to medium so full text is visible
        ),
        "Status": st.column_config.TextColumn(
            "Status", 
            width="small"
        )
    }

    # DISPLAY LIST BASED ON CLICKED CARD / SELECTION
    if st.session_state.selected_view == "defaulters":
        st.subheader(f"⏰ Defaulter Working Hours List ({len(defaulter_hours_only)} Records)")
        st.caption("Net working hours < 08:50 or > 09:10 wale employees ki list:")
        if len(defaulter_hours_only) > 0:
            st.dataframe(defaulter_hours_only.drop(columns=['Issue Type']), column_config=column_config_settings, use_container_width=True, hide_index=True)
        else:
            st.success("🎉 Koi Defaulter Working Hours wala record nahi mila!")

    elif st.session_state.selected_view == "mispunches":
        st.subheader(f"⚠️ Missing & Extra Punches List ({len(mispunches_only)} Records)")
        st.caption("Missing punches (1, 3, 5), last scan IN, ya Extra Scans (7+) wale employees ki list:")
        if len(mispunches_only) > 0:
            st.dataframe(mispunches_only.drop(columns=['Issue Type']), column_config=column_config_settings, use_container_width=True, hide_index=True)
        else:
            st.success("🎉 Koi Mispunch / Extra Punch nahi mila!")

    elif st.session_state.selected_view == "clean":
        st.subheader(f"✅ Clean Employee Records ({len(clean_records_only)} Records)")
        st.caption("Pura time aur exact punches wale perfect records:")
        st.dataframe(clean_records_only.drop(columns=['Issue Type']), column_config=column_config_settings, use_container_width=True, hide_index=True)

    else:
        st.subheader(f"📊 All Employee Records ({len(final_df)} Records)")
        st.dataframe(final_df.drop(columns=['Issue Type']), column_config=column_config_settings, use_container_width=True, hide_index=True)

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
