import streamlit as st
import pandas as pd
import os
import requests
import random

# --- 1. MAKTAB MA'LUMOTLARI ---
MAKTAB_NOMI = "32-sonli umumta'lim maktabi" 
DIREKTOR_FIO = "Eshmatov Toshmat" 
TO_GRI_PAROL = "informatika2024"

# --- API KALITLAR ---
API_KEYS = [
    "AIzaSyAJpdQJJmdWC54Repc9Oz7Qs0nFniEMprI", 
    "AIzaSyBY-QpfMsPgGe3IRc0aS9Cl1fDObIgA2LA", 
    "AIzaSyDXumH-cSk4hAGxpR4oNO-vS2v9MHpX5lo"
]

st.set_page_config(page_title=f"{MAKTAB_NOMI} AI", layout=wide)

# --- BAZA YUKLASH ---
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
                    all_data.append(df_s)
        except: continue
    return pd.concat(all_data, ignore_index=True) if all_data else None

df = yuklash()

# --- CHAT ---
if "messages" not in st.session_state:
    st.session_state.messages = []

if savol := st.chat_input("Savolingizni yozing..."):
    st.session_state.messages.append({"role": "user", "content": savol})
    
    with st.chat_message("assistant"):
        found_info = "Ma'lumot topilmadi."
        if df is not None:
            mask = df.apply(lambda row: row.astype(str).str.contains(savol, case=False, na=False).any(), axis=1)
            sinf_data = df[mask]
            if not sinf_data.empty:
                st.dataframe(sinf_data)
                found_info = "Ma'lumot topildi va jadvalda ko'rsatildi."

        # 🚀 ENG ISHONCHLI MODEL VA URL
        ai_text = ""
        prompt = f"Sen {MAKTAB_NOMI} yordamchisisan. Savol: {savol}. Natija: {found_info}. O'zbekcha samimiy javob ber."
        
        # Kalitlarni aralashtirib, bittalab tekshiramiz
        shuffled_keys = API_KEYS.copy()
        random.shuffle(shuffled_keys)
        
        for key in shuffled_keys:
            # v1beta emas, v1 versiyasidan va gemini-pro modelidan foydalanamiz
            url = f"https://generativelanguage.googleapis.com/v1/models/gemini-pro:generateContent?key={key}"
            try:
                r = requests.post(url, json={"contents": [{"parts": [{"text": prompt}]}]}, timeout=10)
                if r.status_code == 200:
                    ai_text = r.json()['candidates'][0]['content']['parts'][0]['text']
                    break
            except: continue

        if not ai_text:
            ai_text = "Ma'rufjon aka, jadval tayyor. Tizimda kichik texnik sozlash ketyapti, lekin ma'lumotlar ekranda."
        
        st.markdown(ai_text)
