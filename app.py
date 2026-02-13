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

st.set_page_config(page_title=f"{MAKTAB_NOMI} AI", layout="wide")

# --- PAROL ---
if "authenticated" not in st.session_state:
    st.title(f"🔐 {MAKTAB_NOMI} | Tizim")
    parol = st.text_input("Parol:", type="password")
    if st.button("Kirish"):
        if parol == TO_GRI_PAROL:
            st.session_state.authenticated = True
            st.rerun()
        else: st.error("❌ Xato!")
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
                    all_data.append(df_s)
        except: continue
    return pd.concat(all_data, ignore_index=True) if all_data else None

df = yuklash()

# --- CHAT ---
if "messages" not in st.session_state:
    st.session_state.messages = []

for m in st.session_state.messages:
    with st.chat_message(m["role"]): st.markdown(m["content"])

if savol := st.chat_input("Savolingizni yozing..."):
    st.session_state.messages.append({"role": "user", "content": savol})
    with st.chat_message("user"): st.markdown(savol)

    with st.chat_message("assistant"):
        found_info = ""
        if df is not None:
            mask = df.apply(lambda row: row.astype(str).str.contains(savol, case=False, na=False).any(), axis=1)
            sinf_data = df[mask]
            if not sinf_data.empty:
                st.dataframe(sinf_data, use_container_width=True)
                found_info = f"Ma'lumot topildi: {len(sinf_data)} ta qator."
            else:
                found_info = "Ma'lumot topilmadi."

        # 🚀 JONLI TEST VA ULANISH
        ai_text = ""
        last_error = ""
        
        prompt = f"Sen {MAKTAB_NOMI} yordamchisisan. Savol: {savol}. Natija: {found_info}. O'zbekcha qisqa javob ber."
        
        # Tasodifiy bitta kalitni tanlaymiz
        active_key = random.choice(API_KEYS)
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={active_key}"
        
        try:
            r = requests.post(url, json={"contents": [{"parts": [{"text": prompt}]}]}, timeout=15)
            if r.status_code == 200:
                ai_text = r.json()['candidates'][0]['content']['parts'][0]['text']
            else:
                last_error = f"Xato kodi: {r.status_code}, Xabar: {r.text[:100]}"
        except Exception as e:
            last_error = f"Ulanishda xato: {str(e)}"

        if ai_text:
            st.markdown(ai_text)
            st.session_state.messages.append({"role": "assistant", "content": ai_text})
        else:
            # Agar AI ishlamasa, jadval baribir ekranda, lekin xatoni ko'rsatamiz
            st.warning(f"Ma'rufjon aka, jadval chiqdi, lekin AI ulanmadi. Sababi: {last_error}")
