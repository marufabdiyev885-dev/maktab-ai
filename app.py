import streamlit as st
import pandas as pd
import os
import requests
import json

# 1. SOZLAMALAR
API_KEY = "AIzaSyAp3ImXzlVyNF_UXjes2LsSVhG0Uusobdw" 
TO_GRI_PAROL = "informatika2024"

st.set_page_config(page_title="Maktab AI | Mukammal", layout="wide")

# --- PAROL TIZIMI ---
if "authenticated" not in st.session_state:
    st.title("🔐 Maktab AI Tizimi")
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

# --- CHAT TARIXI ---
if "messages" not in st.session_state:
    st.session_state.messages = []

for m in st.session_state.messages:
    with st.chat_message(m["role"]): st.markdown(m["content"])

# --- ASOSIY JARAYON ---
if savol := st.chat_input("Ma'rufjon aka, biror nima so'rang..."):
    st.session_state.messages.append({"role": "user", "content": savol})
    with st.chat_message("user"): st.markdown(savol)

    with st.chat_message("assistant"):
        context_text = ""
        # 1. Bazadan qidirish (AIga ma'lumot berish uchun)
        if df is not None:
            mask = df.apply(lambda row: row.astype(str).str.contains(savol, case=False, na=False).any(), axis=1)
            results = df[mask].head(15) # Topilgan 15 tagacha ma'lumotni AIga beramiz
            if not results.empty:
                context_text = results.to_string(index=False)
                st.dataframe(results) # Jadvalni baribir ko'rsatamiz

        # 2. Gemini AI bilan suhbat
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={API_KEY}"
        headers = {'Content-Type': 'application/json'}
        
        system_instruction = (
            "Sen Ma'rufjon ismli maktab administratorining shaxsiy yordamchisisan. Isming MaktabAI. "
            "Sening vazifang maktab bazasidagi ma'lumotlarni tahlil qilish va Ma'rufjon aka bilan samimiy suhbatlashish. "
            "Agar bazadan ma'lumot topilsa, uni shunchaki o'qib bermay, tahlil qilib ber. "
            "Masalan: 'Ma'rufjon aka, men qidiringiz bo'yicha 2 ta o'quvchini topdim, biri 9-A dan ekan...' deb javob ber. "
            "Har doim o'zbek tilida, do'stona va o'ta aqlli javob ber. "
            "Bazadagi ma'lumotlar quyidagilar: " + context_text
        )

        payload = {
            "contents": [{"parts": [{"text": f"{system_instruction}\n\nFoydalanuvchi savoli: {savol}"}]}]
        }

        try:
            r = requests.post(url, headers=headers, data=json.dumps(payload))
            if r.status_code == 200:
                ai_text = r.json()['candidates'][0]['content']['parts'][0]['text']
            else:
                ai_text = "Ma'rufjon aka, hozircha jadvalga qarab turing, AI tizimida kichik uzilish bo'ldi."
        except:
            ai_text = "Ulanishda muammo bor, lekin jadvaldan qidiruv ishlayapti."

        st.markdown(ai_text)
        st.session_state.messages.append({"role": "assistant", "content": ai_text})
