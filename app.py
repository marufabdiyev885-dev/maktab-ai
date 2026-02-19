if j_fayl:
        df_j = None
        fayl_nomi = j_fayl.name.lower()
        try:
            if fayl_nomi.endswith('.xlsx'):
                df_j = pd.read_excel(j_fayl, engine='openpyxl')
            elif fayl_nomi.endswith('.xls'):
                df_j = pd.read_excel(j_fayl, engine='xlrd')
            else:
                # Noma'lum format - ikkalasini sinab ko'rish
                try:
                    df_j = pd.read_excel(j_fayl, engine='openpyxl')
                except Exception:
                    j_fayl.seek(0)
                    df_j = pd.read_excel(j_fayl, engine='xlrd')
