import streamlit as st
import pandas as pd
import os

# 1. SOZLAMALAR
TO_GRI_PAROL = "informatika2024"

st.set_page_config(page_title="Maktab Analitika AI", layout="wide")

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

st.title("🏫 Maktab Yordamchisi (Analitika)")
df = yuklash()

if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "Assalomu alaykum! Men maktab bazasi bo'yicha hisobotchi botman. Nimalarni hisoblab beray?"}]

for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

# --- QIDIRUV VA TAHLIL ---
if savol := st.chat_input("Savol yozing (Masalan: nechta o'quvchi bor? yoki sertifikatlar)"):
    st.session_state.messages.append({"role": "user", "content": savol})
    with st.chat_message("user"):
        st.write(savol)

    with st.chat_message("assistant"):
        javob = ""
        s = savol.lower()

        if df is not None:
            # 1. Umumiy sonini hisoblash
            if "nechta" in s and ("o'quvchi" in s or "odam" in s or "bor" in s):
                soni = len(df)
                javob = f"Hozirgi bazada jami **{soni} ta** ma'lumot (o'quvchi/pedagog) mavjud."

            # 2. Sertifikatlarni hisoblash
            elif "sertifikat" in s:
                # 'Sertifikat' yoki shunga o'xshash ustunni qidirish
                ser_mask = df.apply(lambda row: row.astype(str).str.contains("bor|mavjud|ha|yes|sertifikat", case=False, na=False).any(), axis=1)
                ser_df = df[ser_mask]
                if not ser_df.empty:
                    javob = f"Bazada sertifikatga ega o'quvchilar soni: **{len(ser_df)} ta**. \n\n"
                    st.dataframe(ser_df)
                else:
                    javob = "Afsuski, bazada sertifikati bor o'quvchilar haqida ma'lumot topilmadi."

            # 3. Oddiy ism qidirish
            else:
                mask = df.apply(lambda row: row.astype(str).str.contains(savol, case=False, na=False).any(), axis=1)
                results = df[mask].head(15)
                if not results.empty:
                    javob = f"'{savol}' bo'yicha topilgan ma'lumotlar:"
                    st.dataframe(results)
                else:
                    javob = f"Kechirasiz, '{savol}' bo'yicha hech narsa topilmadi."
        else:
            javob = "Baza yuklanmagan!"

        st.markdown(javob)
        st.session_state.messages.append({"role": "assistant", "content": javob})
