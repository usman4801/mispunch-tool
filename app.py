def analyze_mispunches(row, punch_cols, mode):
    # ... [Punches gathering logic remains same] ...
    
    # NEW: Extract Breaks from Row
    breaks_raw = str(row.get('No of breaks ', '0')).strip()
    try:
        # Convert "30 mins" or just "30" to minutes
        break_mins = int(''.join(filter(str.isdigit, breaks_raw)))
    except:
        break_mins = 0

    # ... [Total Seconds Calculation Logic] ...
    # Total Duration = Sum of (OUT - IN)
    # Effective Working Hours = Total Duration - Break Minutes
    
    effective_seconds = total_seconds - (break_mins * 60)
    
    # Rule: If effective_seconds >= 9 hours (32400 seconds), mark as Clean
    if effective_seconds >= 32400:
        return pd.Series([total_punches, shift_val, hours_str, "OK", "Complete", "Clean"])
    
    # ... [Rest of logic for Mispunch/Defaulter] ...
