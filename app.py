import streamlit as st
import pandas as pd
import os

# 1. SAHIFA SOZLAMALARI
st.set_page_config(page_title="Maktab AI Yordamchisi", layout="wide")

# --- PAROL TIZIMI ---
TO_GRI_PAROL = "informatika2024"

if "authenticated" not in st.session_state:
    st.title("🔐 Maktab AI Tizimi")
    parol = st.text_input("Kirish uchun parolni kiriting:", type="password")
    if st.button("Kirish"):
        if parol == TO_GRI_PAROL:
            st.session_state.authenticated = True
            st.rerun()
        else:
            st.error("❌ Parol noto'g'ri!")
    st.stop()

# --- BAZANI YUKLASH ---
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
                excel_file = pd.ExcelFile(f)
                for sheet in excel_file.sheet_names:
                    df_s = pd.read_excel(f, sheet_name=sheet, dtype=str)
                    df_s.columns = [str(c).strip() for c in df_s.columns]
                    df_s['Sahifa'] = sheet
                    all_data.append(df_s)
        except:
            continue
    return pd.concat(all_data, ignore_index=True) if all_data else None

df = yuklash()

# --- INTERFEYS ---
st.title("🏫 Maktab AI: Suhbatdosh va Analitik")

if df is not None:
    st.sidebar.success(f"✅ Baza yuklandi: {len(df)} ta qator")
    if st.sidebar.button("📊 Jami statistika"):
        st.sidebar.write(f"Jami yozuvlar: {len(df)}")
        st.sidebar.write(f"Sahifalar: {list(df['Sahifa'].unique())}")

# --- CHAT OYNASI ---
if "messages" not in st.session_state:
    st.session_state.messages = []

# Avvalgi xabarlarni chiqarish
for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

# Yangi savol kiritish
if savol := st.chat_input("Savol bering (Ism yozing yoki Salom bering)..."):
    # User xabarini saqlash
    st.session_state.messages.append({"role": "user", "content": savol})
    with st.chat_message("user"):
        st.markdown(savol)

    # Bot javobi
    with st.chat_message("assistant"):
        s = savol.lower()
        javob = ""

        if df is not None:
            # 1. Bazadan qidirish
            mask = df.apply(lambda row: row.astype(str).str.contains(savol, case=False, na=False).any(), axis=1)
            res = df[mask]

            if not res.empty:
                st.write(f"Ma'rufjon aka, mana '{savol}' bo'yicha topilgan ma'lumotlar:")
                st.dataframe(res)
                javob = f"Bazadan jami {len(res)} ta mos ma'lumot topdim. Yana kimni qidiraylik?"
            
            # 2. Agar bazadan topilmasa yoki shunchaki salomlashsa
            elif any(soz in s for soz in ["salom", "assalom", "qalay", "yaxshimi", "nima gap"]):
                javob = "Vaalaykum assalom, Ma'rufjon aka! Men tayyorman. Ism yozsangiz bazadan qidiraman, savol bersangiz javob beraman."
            
            elif "nechta" in s:
                javob = f"Hozirgi bazamizda jami {len(df)} ta ma'lumot bor."
            
            else:
                javob = f"Kechirasiz Ma'rufjon aka, '{savol}' haqida bazada ma'lumot topilmadi. Ism-familiyani to'liq yozib ko'ring-chi?"
        else:
            javob = "Baza hali yuklanmagan. Iltimos, Excel faylni GitHub-ga yuklang."

        st.markdown(javob)
        st.session_state.messages.append({"role": "assistant", "content": javob})
