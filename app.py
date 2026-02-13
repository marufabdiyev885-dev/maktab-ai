import streamlit as st
import pandas as pd
import os
import requests

# 1. SOZLAMALAR
API_KEY = "SIZ_OLGAN_YANGI_API_KALIT" # Shu yerga haqiqiy kalitni qo'ying
TO_GRI_PAROL = "informatika2024"

st.set_page_config(page_title="Maktab AI Yordamchisi", layout="wide")

# --- PAROL TIZIMI ---
if "authenticated" not in st.session_state:
    st.title("🔐 Maktab AI tizimiga kirish")
    parol = st.text_input("Parolni kiriting:", type="password")
    if st.button("Kirish"):
        if parol == TO_GRI_PAROL:
            st.session_state.authenticated = True
            st.rerun()
        else:
            st.error("❌ Parol xato!")
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
            else:
                excel_file = pd.ExcelFile(f)
                for sheet in excel_file.sheet_names:
                    df_s = pd.read_excel(f, sheet_name=sheet, dtype=str)
                    df_s['Sahifa'] = sheet
                    all_data.append(df_s)
        except: continue
    return pd.concat(all_data, ignore_index=True) if all_data else None

df = yuklash()

# --- ADMIN PANEL (TUGMALAR) ---
st.title("🏫 Maktab AI: Admin va Suhbatdosh")
col1, col2, col3 = st.columns(3)
if df is not None:
    with col1:
        if st.button("📊 Umumiy statistika"):
            st.info(f"Jami ma'lumotlar: {len(df)} ta qator")
    with col2:
        if st.button("🎓 Sertifikatlar"):
            ser = df.apply(lambda r: r.astype(str).str.contains('sertifikat|bor|ha', case=False, na=False).any(), axis=1)
            st.success(f"Sertifikatli o'quvchilar: {len(df[ser])} ta")
    with col3:
        if st.button("📁 Sahifalar ro'yxati"):
            st.warning(f"Listlar: {', '.join(df['Sahifa'].unique())}")

# --- CHAT TIZIMI ---
if "messages" not in st.session_state:
    st.session_state.messages = []

for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

if savol := st.chat_input("Savol bering yoki shunchaki suhbatlashing..."):
    st.session_state.messages.append({"role": "user", "content": savol})
    with st.chat_message("user"):
        st.markdown(savol)

    with st.chat_message("assistant"):
        context = ""
        s = savol.lower()
        
        # 1. ANALITIK JAVOB (Bazadan qidirish)
        mask = df.apply(lambda row: row.astype(str).str.contains(savol, case=False, na=False).any(), axis=1)
        res = df[mask].head(5)
        
        if not res.empty:
            context = "Bazadan topilgan ma'lumotlar:\n" + res.to_string(index=False)
            javob = f"Bazadan topdim: \n"
            st.dataframe(res)
        
        # 2. AI BILAN SUHBAT (Gemini orqali)
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={API_KEY}"
        prompt = f"Sen maktab adminiga yordam beruvchi aqlli AIsan. Isming MaktabAI. Bazada 1362 ta odam bor. "
        if context:
            prompt += f"Mana bu bazadagi ma'lumot: {context}. "
        prompt += f"Foydalanuvchi savoli: {savol}. Javobni o'zbekcha, samimiy va qisqa ber."

        try:
            r = requests.post(url, json={"contents": [{"parts": [{"text": prompt}]}]})
            if r.status_code == 200:
                ai_javob = r.json()['candidates'][0]['content']['parts'][0]['text']
                st.markdown(ai_javob)
                st.session_state.messages.append({"role": "assistant", "content": ai_javob})
            else:
                # Agar API ishlamasa, oddiy javob berish
                simple_msg = "Tushunishimcha, bazadan ma'lumot qidiryapsiz. Yuqoridagi jadvalga qarang."
                st.markdown(simple_msg)
                st.session_state.messages.append({"role": "assistant", "content": simple_msg})
        except:
            st.error("Ulanishda xato, lekin bazadan qidiruv ishlayapti.")
