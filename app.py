import streamlit as st
import pandas as pd
import os

# 1. SOZLAMALAR
TO_GRI_PAROL = "informatika2024"

st.set_page_config(page_title="Maktab AI", layout="centered")

# --- PAROL TIZIMI ---
if "authenticated" not in st.session_state:
    st.title("🔐 Tizimga kirish")
    parol = st.text_input("Parolni kiriting:", type="password")
    if st.button("Kirish"):
        if parol == TO_GRI_PAROL:
            st.session_state.authenticated = True
            st.rerun()
        else:
            st.error("❌ Parol noto'g'ri!")
    st.stop()

# --- BAZANI O'QISH ---
@st.cache_data
def yuklash():
    files = [f for f in os.listdir('.') if f.lower().endswith(('.xlsx', '.csv')) and 'app.py' not in f]
    all_data = []
    for f in files:
        try:
            if f.endswith('.csv'):
                df = pd.read_csv(f, dtype=str, encoding='utf-8')
            else:
                sheets = pd.read_excel(f, sheet_name=None, dtype=str)
                df = pd.concat(sheets.values(), ignore_index=True)
            all_data.append(df)
        except:
            continue
    return pd.concat(all_data, ignore_index=True) if all_data else None

st.title("🏫 Maktab Yordamchisi")
df = yuklash()

if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "Assalomu alaykum! Men maktab yordamchisiman. Kimni qidiryapmiz?"}]

for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

# --- QIDIRUV VA JAVOB ---
if savol := st.chat_input("Ism yoki familiya yozing..."):
    st.session_state.messages.append({"role": "user", "content": savol})
    with st.chat_message("user"):
        st.write(savol)

    with st.chat_message("assistant"):
        # 1. Salomlashishni tekshirish
        salomlar = ["salom", "assalom", "qalay", "yaxshimi", "zdrav", "hello"]
        if any(s in savol.lower() for s in salomlar):
            javob = "Vaalaykum assalom! Yaxshimisiz? Maktab bazasidan kimni qidirib beray?"
        
        # 2. Bazadan qidirish
        elif df is not None:
            mask = df.apply(lambda row: row.astype(str).str.contains(savol, case=False, na=False).any(), axis=1)
            results = df[mask].head(10)
            
            if not results.empty:
                javob = f"Bazadan quyidagi ma'lumotlarni topdim:\n\n"
                # Ma'lumotni chiroyli jadval ko'rinishida chiqarish
                st.dataframe(results)
                javob += "Yana kimdir haqida bilmoqchimisiz?"
            else:
                javob = f"Uzr, bazamizda '{savol}' ismli shaxs haqida ma'lumot topilmadi. Ismni to'g'ri yozganingizga ishonch hosil qiling."
        else:
            javob = "Hozircha baza yuklanmagan. Iltimos, Excel faylni GitHub-ga yuklang."

        st.markdown(javob)
        st.session_state.messages.append({"role": "assistant", "content": javob})
