import streamlit as st
import pandas as pd
import os
import requests
import random

# --- 1. MAKTAB MA'LUMOTLARI ---
MAKTAB_NOMI = "32-sonli umumta'lim maktabi" 
DIREKTOR_FIO = "Eshmatov Toshmat" 
TO_GRI_PAROL = "informatika2024"

# --- API KALITLAR RO'YXATI (3 TA KALIT) ---
API_KEYS = [
    "AIzaSyAJpdQJJmdWC54Repc9Oz7Qs0nFniEMprI", # 1-kalit
    "AIzaSyBY-QpfMsPgGe3IRc0aS9Cl1fDObIgA2LA", # 2-kalit
    "AIzaSyDXumH-cSk4hAGxpR4oNO-vS2v9MHpX5lo"  # 3-kalit
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
                    all_data.append(df_s)
        except: continue
    return pd.concat(all_data, ignore_index=True) if all_data else None

df = yuklash()

# --- CHAT TARIXI ---
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
                found_info = f"Bazadan topilgan ma'lumotlar: {sinf_data.head(10).to_string(index=False)}"
            else:
                found_info = "Bazada ma'lumot yo'q."

        # 🚀 AQLLI API ALMASHTIRISH (Load Balancing)
        prompt = (
            f"Sen {MAKTAB_NOMI}ning rasmiy raqamli yordamchisisan. Direktor: {DIREKTOR_FIO}. "
            f"Hozir senga murojaat qilayotgan: Ma'rufjon aka. Bazadagi ma'lumot: {found_info}. "
            f"Foydalanuvchi savoli: {savol}. "
            f"Javobing samimiy bo'lsin, AI yoki Google ekaningni aytma. O'zbekcha javob ber."
        )

        ai_text = ""
        shuffled_keys = API_KEYS.copy()
        random.shuffle(shuffled_keys) # Har safar har xil kalitdan boshlaydi

        for key in shuffled_keys:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={key}"
            try:
                r = requests.post(url, json={"contents": [{"parts": [{"text": prompt}]}]}, timeout=15)
                if r.status_code == 200:
                    ai_text = r.json()['candidates'][0]['content']['parts'][0]['text']
                    break # Javob olindi, to'xtaymiz
                else: continue # Keyingi kalitga o'tamiz
            except: continue

        if not ai_text:
            ai_text = "Ma'rufjon aka, hozircha jadvalga qarab turing, barcha liniyalarimiz band ekan."

        st.markdown(ai_text)
        st.session_state.messages.append({"role": "assistant", "content": ai_text})
