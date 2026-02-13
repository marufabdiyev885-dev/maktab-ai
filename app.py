import streamlit as st
import pandas as pd
import os
import requests
import json

# 1. SOZLAMALAR
# Yangi kalit o'rnatildi!
API_KEY = "AIzaSyAJpdQJJmdWC54Repc9Oz7Qs0nFniEMprI" 
TO_GRI_PAROL = "informatika2024"

st.set_page_config(page_title="Maktab AI | Active", layout="wide")

# --- PAROL ---
if "authenticated" not in st.session_state:
    st.title("🔐 Maktab AI Tizimi")
    parol = st.text_input("Parolni kiriting:", type="password")
    if st.button("Kirish"):
        if parol == TO_GRI_PAROL:
            st.session_state.authenticated = True
            st.rerun()
        else: st.error("❌ Parol noto'g'ri!")
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
if savol := st.chat_input("Ma'rufjon aka, yangi AI bilan gaplashib ko'ring..."):
    st.session_state.messages.append({"role": "user", "content": savol})
    with st.chat_message("user"): st.markdown(savol)

    with st.chat_message("assistant"):
        context_text = ""
        # 1. Bazadan qidirish
        if df is not None:
            mask = df.apply(lambda row: row.astype(str).str.contains(savol, case=False, na=False).any(), axis=1)
            results = df[mask].head(15)
            if not results.empty:
                context_text = results.to_string(index=False)
                st.dataframe(results)

        # 2. Yangi Gemini API bilan suhbat (v1 version)
        url = f"https://generativelanguage.googleapis.com/v1/models/gemini-1.5-flash:generateContent?key={API_KEY}"
        headers = {'Content-Type': 'application/json'}
        
        system_instruction = (
            "Sen Ma'rufjon ismli maktab administratorining aqlli yordamchisisan. Isming MaktabAI. "
            "Sening miyangda 1362 ta o'quvchi va o'qituvchining ma'lumoti bor. "
            "Agar savol bazadagi ma'lumotga tegishli bo'lsa, uni tahlil qilib ber. "
            "Ma'rufjon aka bilan juda samimiy, do'stona va o'zbek tilida gaplash. "
            "U kishini har doim 'Ma'rufjon aka' deb chaqir. "
            "Bazadagi topilgan ma'lumotlar: " + context_text
        )

        payload = {
            "contents": [{"parts": [{"text": f"{system_instruction}\n\nSavol: {savol}"}]}]
        }

        try:
            r = requests.post(url, headers=headers, data=json.dumps(payload))
            if r.status_code == 200:
                ai_text = r.json()['candidates'][0]['content']['parts'][0]['text']
            else:
                error_info = r.json().get('error', {}).get('message', 'Noma\'lum xato')
                ai_text = f"Ma'rufjon aka, texnik muammo: {error_info}"
        except:
            ai_text = "Ma'rufjon aka, ulanishda xato bo'ldi. Internetni tekshiring."

        st.markdown(ai_text)
        st.session_state.messages.append({"role": "assistant", "content": ai_text})
