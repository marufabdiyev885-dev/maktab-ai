import streamlit as st
import pandas as pd
import os
import requests
import json

# 1. SOZLAMALAR
API_KEY = "AIzaSyAJpdQJJmdWC54Repc9Oz7Qs0nFniEMprI" 
TO_GRI_PAROL = "informatika2024"

st.set_page_config(page_title="Maktab AI | 100% Ishlaydigan", layout="wide")

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

if savol := st.chat_input("Ma'rufjon aka, endi aniq ishlashi kerak..."):
    st.session_state.messages.append({"role": "user", "content": savol})
    with st.chat_message("user"): st.markdown(savol)

    with st.chat_message("assistant"):
        context = ""
        if df is not None:
            mask = df.apply(lambda row: row.astype(str).str.contains(savol, case=False, na=False).any(), axis=1)
            res = df[mask].head(10)
            if not res.empty:
                context = "Baza ma'lumoti: " + res.to_string(index=False)
                st.dataframe(res)

        # 🚀 ENG ISHONCHLI STRATEGIYA: 
        # Avval modellarni ro'yxatdan o'tkazamiz
        url_list = f"https://generativelanguage.googleapis.com/v1beta/models?key={API_KEY}"
        
        try:
            models_res = requests.get(url_list).json()
            # Ishlaydigan birinchi modelni tanlaymiz (asosan gemini-1.5-flash yoki gemini-pro)
            available_models = [m['name'] for m in models_res.get('models', []) if 'generateContent' in m.get('supportedGenerationMethods', [])]
            
            if available_models:
                target_model = available_models[0] # Eng birinchi modelni olamiz
                url = f"https://generativelanguage.googleapis.com/v1beta/{target_model}:generateContent?key={API_KEY}"
                
                prompt = f"Sen Ma'rufjon aka ismli maktab adminiga yordam beruvchi AIsan. Mana ma'lumot: {context}. Savol: {savol}. O'zbekcha javob ber."
                payload = {"contents": [{"parts": [{"text": prompt}]}]}
                
                r = requests.post(url, json=payload)
                if r.status_code == 200:
                    ai_text = r.json()['candidates'][0]['content']['parts'][0]['text']
                else:
                    ai_text = f"Ma'rufjon aka, server rad etdi. Kalit hali faollashmagan bo'lishi mumkin."
            else:
                ai_text = "Ma'rufjon aka, hisobingizda birorta ham AI model topilmadi. AI Studio-da sozlamalarni ko'rish kerak."
                
        except Exception as e:
            ai_text = f"Texnik xato: {str(e)}"

        st.markdown(ai_text)
        st.session_state.messages.append({"role": "assistant", "content": ai_text})
