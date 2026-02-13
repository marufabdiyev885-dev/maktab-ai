import streamlit as st
import pandas as pd
import os
import requests
import json

# 1. SOZLAMALAR
API_KEY = "AIzaSyAJpdQJJmdWC54Repc9Oz7Qs0nFniEMprI" 
TO_GRI_PAROL = "informatika2024"

st.set_page_config(page_title="Maktab AI | Final", layout="wide")

# --- PAROL ---
if "authenticated" not in st.session_state:
    st.title("🔐 Maktab AI Tizimi")
    parol = st.text_input("Parol:", type="password")
    if st.button("Kirish"):
        if parol == TO_GRI_PAROL:
            st.session_state.authenticated = True
            st.rerun()
        else: st.error("❌ Parol noto'g'ri!")
    st.stop()

# --- BAZA ---
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

# --- CHAT ---
if "messages" not in st.session_state:
    st.session_state.messages = []

for m in st.session_state.messages:
    with st.chat_message(m["role"]): st.markdown(m["content"])

if savol := st.chat_input("Ma'rufjon aka, endi sinab ko'ring..."):
    st.session_state.messages.append({"role": "user", "content": savol})
    with st.chat_message("user"): st.markdown(savol)

    with st.chat_message("assistant"):
        context = ""
        if df is not None:
            mask = df.apply(lambda row: row.astype(str).str.contains(savol, case=False, na=False).any(), axis=1)
            res = df[mask].head(10)
            if not res.empty:
                context = "Bazadagi ma'lumotlar: " + res.to_string(index=False)
                st.dataframe(res)

        # DIQQAT: v1beta va gemini-1.5-flash-latest kombinatsiyasi eng chidamlisi
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash-latest:generateContent?key={API_KEY}"
        headers = {'Content-Type': 'application/json'}
        
        prompt = (
            f"Sen Ma'rufjon aka ismli maktab adminining yordamchisisan. "
            f"Bazadagi ma'lumot: {context}. Savol: {savol}. "
            f"Javobni o'zbek tilida, juda samimiy va Ma'rufjon aka deb murojaat qilgan holda ber."
        )
        
        payload = {"contents": [{"parts": [{"text": prompt}]}]}
        
        try:
            r = requests.post(url, headers=headers, json=payload)
            res_json = r.json()
            if r.status_code == 200:
                javob = res_json['candidates'][0]['content']['parts'][0]['text']
            else:
                # Agar flash-latest ham o'xshamas, oddiy gemini-pro ni sinaymiz
                url_alt = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key={API_KEY}"
                r_alt = requests.post(url_alt, headers=headers, json=payload)
                if r_alt.status_code == 200:
                    javob = r_alt.json()['candidates'][0]['content']['parts'][0]['text']
                else:
                    err = res_json.get('error', {}).get('message', 'Model topilmadi')
                    javob = f"Ma'rufjon aka, Google hali ham modelni bermayapti. Xato: {err}"
        except:
            javob = "Texnik xatolik yuz berdi."

        st.markdown(javob)
        st.session_state.messages.append({"role": "assistant", "content": javob})
