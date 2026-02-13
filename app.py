import streamlit as st
import pandas as pd
import os
import requests

# 1. SOZLAMALAR
# !!! DIQQAT: API_KEY qismiga o'zingizni kalitingizni qo'ying !!!
API_KEY = "SIZNING_GEMINI_API_KALITINGIZ" 
TO_GRI_PAROL = "informatika2024"

st.set_page_config(page_title="Maktab AI | Mukammal", layout="wide")

# --- PAROL TIZIMI ---
if "authenticated" not in st.session_state:
    st.title("🔐 Maktab AI")
    parol = st.text_input("Parol:", type="password")
    if st.button("Kirish"):
        if parol == TO_GRI_PAROL:
            st.session_state.authenticated = True
            st.rerun()
        else: st.error("Xato!")
    st.stop()

# --- BAZANI YUKLASH ---
@st.cache_data
def yuklash():
    files = [f for f in os.listdir('.') if f.lower().endswith(('.xlsx', '.csv')) and 'app.py' not in f]
    all_data = []
    for f in files:
        try:
            if f.endswith('.csv'): df = pd.read_csv(f, dtype=str)
            else:
                excel = pd.ExcelFile(f)
                for sheet in excel.sheet_names:
                    df_s = pd.read_excel(f, sheet_name=sheet, dtype=str)
                    df_s.columns = [str(c).strip() for c in df_s.columns]
                    df_s['Sahifa'] = sheet
                    all_data.append(df_s)
        except: continue
    return pd.concat(all_data, ignore_index=True) if all_data else None

df = yuklash()

# --- CHAT TIZIMI ---
if "messages" not in st.session_state:
    st.session_state.messages = []

for m in st.session_state.messages:
    with st.chat_message(m["role"]): st.markdown(m["content"])

if savol := st.chat_input("Ma'rufjon aka, biror nima so'rang..."):
    st.session_state.messages.append({"role": "user", "content": savol})
    with st.chat_message("user"): st.markdown(savol)

    with st.chat_message("assistant"):
        # 1. BAZADAN QIDIRISH (AIga kontekst sifatida berish uchun)
        context = ""
        if df is not None:
            mask = df.apply(lambda row: row.astype(str).str.contains(savol, case=False, na=False).any(), axis=1)
            res = df[mask].head(10) # Eng yaqin 10 ta ma'lumotni olamiz
            if not res.empty:
                context = "Bazadagi ma'lumotlar:\n" + res.to_string(index=False)
                st.dataframe(res) # Jadvalni baribir ko'rsatib turamiz

        # 2. GEMINI AI BILAN BOG'LANISH (ASOSIY MIYA)
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={API_KEY}"
        
        system_prompt = (
            "Sen Ma'rufjon ismli maktab adminiga yordam beruvchi o'ta aqlli va samimiy AIsan. "
            "Sening isming 'Maktab AI'. Sen xuddi insondek fikrlaysan. "
            "Agar savolga tegishli ma'lumot baza ichida bo'lsa, o'sha ma'lumotni tahlil qilib javob ber. "
            "Masalan: 'Ma'rufjon aka, men bu o'quvchini topdim. U 9-A sinfda o'qir ekan...' deb javob ber. "
            "Agar savol bazaga tegishli bo'lmasa, umumiy mavzularda suhbatlash. "
            "O'zbek tilida, do'stona va professional tilda javob qaytar."
        )
        
        payload = {
            "contents": [{
                "parts": [{"text": f"{system_prompt}\n\nKontekst: {context}\n\nSavol: {savol}"}]
            }]
        }

        try:
            response = requests.post(url, json=payload)
            if response.status_code == 200:
                ai_javob = response.json()['candidates'][0]['content']['parts'][0]['text']
            else:
                ai_javob = "Ma'rufjon aka, AI miyam bilan ulanishda biroz muammo bo'ldi. Lekin jadvaldan qidirib ko'rdim."
        except:
            ai_javob = "Ulanishda xato. Internetni yoki API kalitni tekshiring."

        st.markdown(ai_javob)
        st.session_state.messages.append({"role": "assistant", "content": ai_javob})
