import streamlit as st
import pandas as pd
import os
import requests
import json

# 1. SOZLAMALAR
API_KEY = "AIzaSyAJpdQJJmdWC54Repc9Oz7Qs0nFniEMprI" 
TO_GRI_PAROL = "informatika2024"

st.set_page_config(page_title="Maktab AI | Full Vision", layout="wide")

# --- PAROL TIZIMI ---
if "authenticated" not in st.session_state:
    st.title("🔐 Maktab AI Tizimi")
    parol = st.text_input("Kirish uchun parolni kiriting:", type="password")
    if st.button("Kirish"):
        if parol == TO_GRI_PAROL:
            st.session_state.authenticated = True
            st.rerun()
        else:
            st.error("❌ Parol noto'g'ri!")
    st.stop()

# --- BAZANI YUKLASH ---
@st.cache_data
def yuklash():
    files = [f for f in os.listdir('.') if f.lower().endswith(('.xlsx', '.csv')) and 'app.py' not in f]
    all_data = []
    for f in files:
        try:
            if f.endswith('.csv'):
                df = pd.read_csv(f, dtype=str)
                all_data.append(df)
            else:
                excel_file = pd.ExcelFile(f)
                for sheet in excel_file.sheet_names:
                    df_s = pd.read_excel(f, sheet_name=sheet, dtype=str)
                    df_s.columns = [str(c).strip() for c in df_s.columns]
                    df_s['Sahifa'] = sheet
                    all_data.append(df_s)
        except:
            continue
    return pd.concat(all_data, ignore_index=True) if all_data else None

df = yuklash()

# --- CHAT TARIXI ---
if "messages" not in st.session_state:
    st.session_state.messages = []

for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

# --- ASOSIY MULOQOT ---
if savol := st.chat_input("Ma'rufjon aka, xohlagan narsangizni so'rang..."):
    st.session_state.messages.append({"role": "user", "content": savol})
    with st.chat_message("user"):
        st.markdown(savol)

    with st.chat_message("assistant"):
        # 📊 BAZA HAQIDA UMUMIY MA'LUMOT
        jami_soni = len(df) if df is not None else 0
        ustunlar = ", ".join(df.columns) if df is not None else "Noma'lum"
        
        # 🔍 QIDIRUV VA KONTEKST TAYYORLASH
        context = f"Tizimda jami {jami_soni} ta qator ma'lumot bor. Jadvallardagi ustunlar: {ustunlar}. "
        if df is not None:
            # Foydalanuvchi savolidagi so'zlar bo'yicha bazadan qidirish
            mask = df.apply(lambda row: row.astype(str).str.contains(savol, case=False, na=False).any(), axis=1)
            res = df[mask].head(20) # AIga ko'proq ma'lumot berish uchun 20 ta qator
            if not res.empty:
                context += "Qidiruv bo'yicha topilgan aniq ma'lumotlar:\n" + res.to_string(index=False)
                st.dataframe(res) # Jadvalni ekranda ko'rsatish

        # 🚀 GEMINI AI BILAN BOG'LANISH (Eng ishonchli yo'l)
        url_list = f"https://generativelanguage.googleapis.com/v1beta/models?key={API_KEY}"
        try:
            # 1. Qaysi model ishlayotganini aniqlash
            models_res = requests.get(url_list).json()
            available_models = [m['name'] for m in models_res.get('models', []) if 'generateContent' in m.get('supportedGenerationMethods', [])]
            target_model = available_models[0] if available_models else "models/gemini-1.5-flash"
            
            # 2. Savolni AIga yuborish
            url = f"https://generativelanguage.googleapis.com/v1beta/{target_model}:generateContent?key={API_KEY}"
            prompt = (
                f"Sen Ma'rufjon aka ismli maktab administratorining shaxsiy yordamchisisan. "
                f"Sening isming MaktabAI. Bazada {jami_soni} ta ma'lumot bor. "
                f"Mana senga kerakli ma'lumotlar: {context}. "
                f"Foydalanuvchi savoli: {savol}. "
                f"DIQQAT: Ma'rufjon aka bilan juda samimiy gaplash, har bir javobda u kishining ismini ayt. "
                f"Agar bazadan biror narsani topsang, uni tahlil qilib chiroyli tushuntir. "
                f"O'zbek tilida javob ber."
            )
            
            payload = {"contents": [{"parts": [{"text": prompt}]}]}
            r = requests.post(url, json=payload, timeout=15)
            
            if r.status_code == 200:
                ai_text = r.json()['candidates'][0]['content']['parts'][0]['text']
            else:
                ai_text = f"Ma'rufjon aka, hozircha jadvalga qarab turing, AI tizimida kichik uzilish bo'ldi. Xato: {r.status_code}"
        except Exception as e:
            ai_text = f"Ma'rufjon aka, ulanishda texnik muammo: {str(e)}"

        st.markdown(ai_text)
        st.session_state.messages.append({"role": "assistant", "content": ai_text})
