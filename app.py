import streamlit as st
import pandas as pd
import os
import requests

# --- 1. MAKTAB MA'LUMOTLARI ---
MAKTAB_NOMI = "32-sonli umumta'lim maktabi" 
DIREKTOR_FIO = "Eshmatov Toshmat" 
GROQ_API_KEY = "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"
TO_GRI_PAROL = "informatika2024"

st.set_page_config(page_title=f"{MAKTAB_NOMI} AI", layout="wide")

# --- PAROL TIZIMI ---
if "authenticated" not in st.session_state:
    st.title(f"🔐 {MAKTAB_NOMI} | Tizim")
    parol = st.text_input("Parol:", type="password")
    if st.button("Kirish"):
        if parol == TO_GRI_PAROL:
            st.session_state.authenticated = True
            st.rerun()
        else: st.error("❌ Parol noto'g'ri!")
    st.stop()

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
        # Bazadan qidirish
        found_data = "Bazada ma'lumot topilmadi."
        if df is not None:
            mask = df.apply(lambda row: row.astype(str).str.contains(savol, case=False, na=False).any(), axis=1)
            sinf_data = df[mask]
            if not sinf_data.empty:
                st.dataframe(sinf_data, use_container_width=True)
                found_data = f"Topilgan ma'lumotlar jadvali: {sinf_data.head(10).to_string(index=False)}"

        # 🚀 GROQ AI (Llama-3.1-70b) BILAN BOG'LANISH
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json"
        }
        
        # AI uchun yo'riqnoma (Prompt)
        system_prompt = (
            f"Sen {MAKTAB_NOMI}ning rasmiy raqamli yordamchisisan. "
            f"Maktab direktori: {DIREKTOR_FIO}. "
            f"Hozir senga Ma'rufjon aka murojaat qilyapti. "
            f"Vazifang: Bazadagi ma'lumotlarga qarab Ma'rufjon akaga samimiy javob berish. "
            f"O'zingni AI deb tanishtirma, faqat maktab xodimidek gapir. O'zbek tilida javob ber."
        )
        
        payload = {
            "model": "llama-3.1-70b-versatile",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Baza ma'lumoti: {found_data}. Savol: {savol}"}
            ],
            "temperature": 0.7
        }
        
        try:
            r = requests.post(url, json=payload, headers=headers, timeout=15)
            if r.status_code == 200:
                ai_text = r.json()['choices'][0]['message']['content']
            else:
                ai_text = "Ma'rufjon aka, hozircha jadvalga qarab turing, AI ulanishida kichik muammo bo'ldi."
        except:
            ai_text = "Aloqa uzildi. Iltimos, qayta urinib ko'ring."

        st.markdown(ai_text)
        st.session_state.messages.append({"role": "assistant", "content": ai_text})
