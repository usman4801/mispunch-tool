# ... (code up to punch_cols definition)

    # FIXED: Direct Index Mapping (P.Soft ID = Column 1, Employee Name = Column 2)
    # Yeh code aapke file layout ke hisab se 0-based index use kar raha hai
    id_data = df.iloc[:, 1].astype(str).str.replace(r'\.0$', '', regex=True)
    name_data = df.iloc[:, 2].astype(str)

    base_info_df = pd.DataFrame({
        'P.Soft ID': id_data,
        'Employee Name': name_data
    })
    
    # .0 hataane ke liye final check
    base_info_df['P.Soft ID'] = base_info_df['P.Soft ID'].str.replace(r'\.0$', '', regex=True)
    base_info_df['Employee Name'] = base_info_df['Employee Name'].str.replace(r'\.0$', '', regex=True)

    base_info_df['Repeated\nOffender'] = base_info_df.groupby('P.Soft ID').cumcount() + 1
    
    # ... (rest of the code follows)
