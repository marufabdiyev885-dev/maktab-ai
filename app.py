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
if savol := st.chat_input("Ma'rufjon aka, buyuravering..."):
    st.session_state.messages.append({"role": "user", "content": savol})
    with st.chat_message("user"): st.markdown(savol)

    with st.chat_message("assistant"):
        context_text = ""
        if df is not None:
            mask = df.apply(lambda row: row.astype(str).str.contains(savol, case=False, na=False).any(), axis=1)
            results = df[mask].head(10)
            if not results.empty:
                context_text = results.to_string(index=False)
                st.dataframe(results)

        # Gemini API ulanish
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={API_KEY}"
        headers = {'Content-Type': 'application/json'}
        
        prompt = f"Sen Ma'rufjon ismli maktab adminiga yordam beruvchi aqlli AIsan. Bazadagi ma'lumot: {context_text}. Savol: {savol}. O'zbekcha javob ber."
        payload = {"contents": [{"parts": [{"text": prompt}]}]}

        try:
            r = requests.post(url, headers=headers, json=payload)
            res_json = r.json()
            
            if r.status_code == 200:
                ai_text = res_json['candidates'][0]['content']['parts'][0]['text']
            else:
                # Xatoni aniq aniqlash
                err_msg = res_json.get('error', {}).get('message', 'Noma\'lum xato')
                ai_text = f"API Xatosi: {err_msg}" # Bu yerda xato matni chiqadi
                
        except Exception as e:
            ai_text = f"Texnik ulanishda xato: {str(e)}"

        st.markdown(ai_text)
        st.session_state.messages.append({"role": "assistant", "content": ai_text})
