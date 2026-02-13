import streamlit as st
import pandas as pd
import os

# 1. SOZLAMALAR
TO_GRI_PAROL = "informatika2024"
st.set_page_config(page_title="Maktab AI | To'liq Baza", layout="wide")

# --- PAROL ---
if "authenticated" not in st.session_state:
    st.title("🔐 Kirish")
    parol = st.text_input("Parol:", type="password")
    if st.button("Kirish"):
        if parol == TO_GRI_PAROL:
            st.session_state.authenticated = True
            st.rerun()
        else:
            st.error("❌ Xato!")
    st.stop()

# --- BAZANI YUKLASH (HAMMA LISTLARNI O'QIYDIGAN QILINDI) ---
@st.cache_data
def yuklash():
    files = [f for f in os.listdir('.') if f.lower().endswith(('.xlsx', '.csv')) and 'app.py' not in f]
    all_data = []
    for f in files:
        try:
            if f.endswith('.csv'):
                df = pd.read_csv(f, dtype=str)
                all_data.append(df)
            else:
                # Excel faylidagi barcha listlarni o'qiymiz
                excel_file = pd.ExcelFile(f)
                for sheet_name in excel_file.sheet_names:
                    df_sheet = pd.read_excel(f, sheet_name=sheet_name, dtype=str)
                    # Ustun nomlarini tozalash
                    df_sheet.columns = [str(c).strip() for c in df_sheet.columns]
                    # List nomini ham ma'lumot sifatida qo'shib qo'yamiz (ajratish oson bo'lishi uchun)
                    df_sheet['Manba_List'] = sheet_name
                    all_data.append(df_sheet)
        except Exception as e:
            st.sidebar.error(f"Fayl o'qishda xato ({f}): {e}")
            continue
    return pd.concat(all_data, ignore_index=True) if all_data else None

st.title("🏫 Maktab Aqlli Yordamchisi (Barcha sahifalar)")
df = yuklash()

if "messages" not in st.session_state:
    st.session_state.messages = []

for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.write(m["content"])

# --- ASOSIY MANTIQ ---
if savol := st.chat_input("Savol yozing..."):
    st.session_state.messages.append({"role": "user", "content": savol})
    with st.chat_message("user"):
        st.write(savol)

    with st.chat_message("assistant"):
        javob = ""
        s = savol.lower()

        if df is not None:
            # 1. QIDIRUV (Ism yoki ma'lumot yozilganda)
            mask = df.apply(lambda row: row.astype(str).str.contains(savol, case=False, na=False).any(), axis=1)
            res = df[mask]

            if "nechta" in s:
                soni = len(df)
                javob = f"Bazadagi barcha sahifalardan jami **{soni} ta** qator topildi."
            
            elif not res.empty:
                javob = f"'{savol}' bo'yicha quyidagi ma'lumotlar topildi:\n"
                # Har bir topilgan qator qaysi listdan olinganini ham ko'rsatamiz
                st.dataframe(res)
            else:
                javob = f"Kechirasiz, '{savol}' bo'yicha hech qanday ma'lumot topilmadi."
        else:
            javob = "Baza yuklanmagan! Iltimos, Excel faylingizni tekshiring."

        st.markdown(javob)
        st.session_state.messages.append({"role": "assistant", "content": javob})
