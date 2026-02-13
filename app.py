import streamlit as st
import requests
import pandas as pd
import os
import json

# 1. SOZLAMALAR
API_KEY = "AIzaSyAp3ImXzlVyNF_UXjes2LsSVhG0Uusobdw"
TO_GRI_PAROL = "informatika2024"

st.set_page_config(page_title="Maktab AI", layout="centered")

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

# --- BAZANI O'QISH ---
@st.cache_data
def yuklash():
    files = [f for f in os.listdir('.') if f.lower().endswith(('.xlsx', '.csv')) and 'app.py' not in f]
    all_data = []
    for f in files:
        try:
            if f.endswith('.csv'):
                df = pd.read_csv(f, dtype=str)
            else:
                sheets = pd.read_excel(f, sheet_name=None, dtype=str)
                df = pd.concat(sheets.values(), ignore_index=True)
            all_data.append(df)
        except:
            continue
    return pd.concat(all_data, ignore_index=True) if all_data else None

df = yuklash()

# --- ASOSIY ---
st.title("🏫 Maktab AI Yordamchisi")

if "messages" not in st.session_state:
    st.session_state.messages = []

for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

if savol := st.chat_input("Savol yozing..."):
    st.session_state.messages.append({"role": "user", "content": savol})
    with st.chat_message("user"):
        st.write(savol)

    with st.chat_message("assistant"):
        context = ""
        if df is not None:
            mask = df.apply(lambda row: row.astype(str).str.contains(savol, case=False, na=False).any(), axis=1)
            res = df[mask].head(5)
            if not res.empty:
                context = res.to_string(index=False)

        # TO'G'RIDAN-TO'G'RI URL (v1 versiyasi)
        url = f"https://generativelanguage.googleapis.com/v1/models/gemini-pro:generateContent?key={API_KEY}"
        payload = {"contents": [{"parts": [{"text": f"Baza: {context}\nSavol: {savol}"}]}]}
        
        try:
            r = requests.post(url, json=payload)
            data = r.json()
            
            if r.status_code == 200:
                javob = data['candidates'][0]['content']['parts'][0]['text']
                st.write(javob)
                st.session_state.messages.append({"role": "assistant", "content": javob})
            else:
                # Google bergan haqiqiy xatoni ko'rsatish
                st.error(f"Google API xatosi: {data['error']['message']}")
        except Exception as e:
            st.error(f"Bog'lanishda xato: {str(e)}")
