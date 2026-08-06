# (Keep all your imports, page config, and UI setup the same as before)

def analyze_mispunches(row, punch_cols, mode):
    punches = []
    for col in punch_cols:
        val = parse_time(row.get(col))
        if val is not None:
            punches.append(val)
            
    total_punches = len(punches)
    
    # 1. Shift & Break setup
    shift_raw = str(row.get('Shift timings ', row.get('Shift timings', '')))
    shift_val = get_shift_type(shift_raw)
    breaks_raw = str(row.get('No of breaks ', '0')).strip()
    try:
        break_mins = int(''.join(filter(str.isdigit, breaks_raw)))
    except:
        break_mins = 0

    if total_punches == 0:
        return pd.Series([0, shift_val, "00:00", "OK", "Absent", "Clean"])

    # 2. Duration Calculation (Full Day logic)
    dummy_date = datetime(2026, 1, 1)
    total_duration_seconds = 0
    # Simple loop to sum all pairs
    for i in range(0, total_punches - (total_punches % 2), 2):
        s = datetime.combine(dummy_date, punches[i])
        e = datetime.combine(dummy_date, punches[i+1])
        if e < s: e += timedelta(days=1)
        total_duration_seconds += (e - s).total_seconds()
    
    effective_seconds = total_duration_seconds - (break_mins * 60)
    hours_str = f"{int(total_duration_seconds // 3600):02d}:{int((total_duration_seconds % 3600) // 60):02d}"
    
    # 3. FINAL CLEAN LOGIC:
    # If even punches AND hours >= 9 hours (32400 seconds) -> CLEAN
    if total_punches % 2 == 0 and effective_seconds >= 32400:
        return pd.Series([total_punches, shift_val, hours_str, "OK", "Complete", "Clean"])
    
    # If even punches but < 9 hours -> Defaulter
    elif total_punches % 2 == 0:
        return pd.Series([total_punches, shift_val, hours_str, "Error", "Short Working Hours", "Defaulter Hours"])
    
    # If odd punches -> Mispunch
    else:
        return pd.Series([total_punches, shift_val, hours_str, "Error", "Incomplete Punches", "Mispunch"])

# ... (Rest of your app logic to display this DataFrame remains same)
