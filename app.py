import streamlit as st
import pandas as pd
import os
import requests
import json

# 1. SOZLAMALAR
API_KEY = "AIzaSyAJpdQJJmdWC54Repc9Oz7Qs0nFniEMprI" 
TO_GRI_PAROL = "informatika2024"

st.set_page_config(page_title="Maktab AI | Professional", layout="wide")

# --- PAROL ---
if "authenticated" not in st.session_state:
    st.title("🔐 Maktab AI Tizimi")
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

if savol := st.chat_input("Sinf nomini yozing (masalan: 9-A)..."):
    st.session_state.messages.append({"role": "user", "content": savol})
    with st.chat_message("user"): st.markdown(savol)

    with st.chat_message("assistant"):
        found = False
        if df is not None:
            # Sinfni aniqroq qidirish (case-insensitive)
            mask = df.apply(lambda row: row.astype(str).str.contains(savol, case=False, na=False).any(), axis=1)
            sinf_data = df[mask]

            if not sinf_data.empty:
                st.success(f"Ma'rufjon aka, {len(sinf_data)} ta ma'lumot topildi:")
                st.dataframe(sinf_data, use_container_width=True)
                found = True
                summary = f"Savol: {savol}. Topilgan qatorlar soni: {len(sinf_data)} ta."
            else:
                summary = f"Savol: {savol}. Afsuski, hech narsa topilmadi."

        # 🚀 AI BILAN BOG'LANISH (Yengillashtirilgan variant)
        url_list = f"https://generativelanguage.googleapis.com/v1beta/models?key={API_KEY}"
        try:
            models_res = requests.get(url_list).json()
            available_models = [m['name'] for m in models_res.get('models', []) if 'generateContent' in m.get('supportedGenerationMethods', [])]
            target_model = available_models[0] if available_models else "models/gemini-1.5-flash"
            
            url = f"https://generativelanguage.googleapis.com/v1beta/{target_model}:generateContent?key={API_KEY}"
            
            # AI'ga katta jadvalni emas, shunchaki natija haqida hisobotni yuboramiz
            prompt = (
                f"Sen Ma'rufjon aka ismli maktab adminining yordamchisisan. "
                f"Tizimda natija topildimi: {'Ha' if found else 'Yoq'}. {summary}. "
                f"Sening vazifang - Ma'rufjon akaga samimiy qilib natija haqida xabar berish. "
                f"Agar topilgan bo'lsa: 'Ma'rufjon aka, mana siz so'ragan ro'yxatni chiqardim' kabi gapir. "
                f"Agar topilmagan bo'lsa: 'Ma'rufjon aka, bazada bunday ma'lumot topilmadi' deb ayt. "
                f"O'zbekcha javob ber."
            )
            
            payload = {"contents": [{"parts": [{"text": prompt}]}]}
            r = requests.post(url, json=payload, timeout=15)
            ai_text = r.json()['candidates'][0]['content']['parts'][0]['text']
        except:
            ai_text = "Ma'rufjon aka, jadval tayyor! AI bilan aloqada ozgina tormozlanish bo'ldi, lekin ma'lumotlar ekranda."

        st.markdown(ai_text)
        st.session_state.messages.append({"role": "assistant", "content": ai_text})
