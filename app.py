import streamlit as st
import requests
import pandas as pd
import os
import json

# 1. SOZLAMALAR
API_KEY = "AIzaSyAp3ImXzlVyNF_UXjes2LsSVhG0Uusobdw"
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

st.title("🏫 Maktab AI Yordamchisi")
df = yuklash()

# --- CHAT TARIXI ---
if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# --- MODELLARNI TESTDAN O'TKAZISH VA JAVOB OLISH ---
def ask_google_ai(prompt_text):
    # Google tanishi mumkin bo'lgan barcha model nomlari (404 ni chetlab o'tish uchun)
    models = [
        "gemini-1.5-flash-8b",
        "gemini-1.5-flash",
        "gemini-1.0-pro",
        "gemini-pro"
    ]
    
    for model_name in models:
        # Har bir modelni v1beta orqali sinab ko'ramiz
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={API_KEY}"
        payload = {"contents": [{"parts": [{"text": prompt_text}]}]}
        
        try:
            r = requests.post(url, json=payload, timeout=5)
            if r.status_code == 200:
                res = r.json()
                return res['candidates'][0]['content']['parts'][0]['text']
        except:
            continue
    return None

# --- ASOSIY JARAYON ---
if savol := st.chat_input("Salom deb yozing yoki ism so'rang..."):
    st.session_state.messages.append({"role": "user", "content": savol})
    with st.chat_message("user"):
        st.write(savol)

    with st.chat_message("assistant"):
        # Bazadan qidirish
        context = ""
        if df is not None:
            mask = df.apply(lambda row: row.astype(str).str.contains(savol, case=False, na=False).any(), axis=1)
            results = df[mask].head(10)
            if not results.empty:
                context = "Bazadagi ma'lumotlar:\n" + results.to_string(index=False)

        prompt = f"Sen maktab yordamchisisan. Foydalanuvchi savoliga o'zbek tilida javob ber. "
        if context:
            prompt += f"Mana bu bazadagi ma'lumotlardan foydalan:\n{context}\n\n"
        prompt += f"Savol: {savol}"

        with st.spinner("AI o'ylamoqda..."):
            javob = ask_google_ai(prompt)
            if javob:
                st.markdown(javob)
                st.session_state.messages.append({"role": "assistant", "content": javob})
            else:
                st.error("Google AI bilan bog'lanishda muammo. API kalitini yangilash kerak bo'lishi mumkin.")
