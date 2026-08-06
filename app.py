def analyze_mispunches(row, punch_cols, mode):
    punches = []
    for col in punch_cols:
        val = parse_time(row.get(col))
        if val is not None:
            punches.append(val)
            
    total_punches = len(punches)
    
    # NEW PRIORITY SHIFT DETECTION
    # 1. Check if 'Shift' column exists in attendance file
    shift_val = str(row.get('Shift', row.get('Shift timings ', 'Day'))).strip()
    
    # 2. Smart Detection if 'Day' is default
    if shift_val.lower() == 'day':
        # Check roster for better clarity
        roster_shift = str(row.get('Shift timings ', 'Day')).strip()
        if 'night' in roster_shift.lower(): shift_val = "Night"
        elif 'mid' in roster_shift.lower(): shift_val = "Mid"
    
    # ... [Rest of your calculation logic]
