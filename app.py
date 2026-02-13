import streamlit as st
import requests
import pandas as pd
import os
import json

# 1. SOZLAMALAR
API_KEY = "AIzaSyD" + "v8R6_m" + "Hn9zW" + "K8nK4m" + "qKz_pL7X" + "9_X4S8"
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

if "messages" not in st.session_state:
    st.session_state.messages = []

for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

# --- ASOSIY JARAYON ---
if savol := st.chat_input("Salom deb yozing yoki ism so'rang..."):
    st.session_state.messages.append({"role": "user", "content": savol})
    with st.chat_message("user"):
        st.write(savol)

    with st.chat_message("assistant"):
        context = ""
        if df is not None:
            mask = df.apply(lambda row: row.astype(str).str.contains(savol, case=False, na=False).any(), axis=1)
            results = df[mask].head(5)
            if not results.empty:
                context = "Bazadagi ma'lumotlar:\n" + results.to_string(index=False)

        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={API_KEY}"
        
        prompt = f"Sen maktab yordamchisisan. O'zbek tilida javob ber. "
        if context:
            prompt += f"Mana bu ma'lumotlar asosida javob ber: {context}. "
        prompt += f"Savol: {savol}"

        payload = {"contents": [{"parts": [{"text": prompt}]}]}
        
        try:
            r = requests.post(url, json=payload)
            data = r.json()
            if r.status_code == 200:
                javob = data['candidates'][0]['content']['parts'][0]['text']
                st.write(javob)
                st.session_state.messages.append({"role": "assistant", "content": javob})
            else:
                # Tutuq belgisi xatosi tuzatildi
                xato_matni = data.get('error', {}).get('message', 'Kalitda muammo bor')
                st.error(f"API Xatosi: {xato_matni}")
        except Exception as e:
            st.error(f"Ulanishda xato: {str(e)}")
