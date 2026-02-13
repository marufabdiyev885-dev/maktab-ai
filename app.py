import streamlit as st
import requests
import pandas as pd
import os
import json

# 1. API VA SOZLAMALAR
API_KEY = "AIzaSyAp3ImXzlVyNF_UXjes2LsSVhG0Uusobdw"
TO_GRI_PAROL = "informatika2024"

st.set_page_config(page_title="Maktab AI | Ma'rufjon Abdiyev", layout="centered")

# --- PAROL TIZIMI ---
if "authenticated" not in st.session_state:
    st.title("🔐 Tizimga kirish")
    parol = st.text_input("Parolni kiriting:", type="password")
    if st.button("Kirish"):
        if parol == TO_GRI_PAROL:
            st.session_state.authenticated = True
            st.rerun()
        else:
            st.error("❌ Parol noto'g'ri!")
    st.stop()

# --- BAZANI O'QISH ---
@st.cache_data
def yuklash():
    files = [f for f in os.listdir('.') if f.lower().endswith(('.xlsx', '.csv')) and 'app.py' not in f]
    all_data = []
    for f in files:
        try:
            if f.endswith('.csv'):
                df = pd.read_csv(f, dtype=str, encoding='utf-8')
            else:
                sheets = pd.read_excel(f, sheet_name=None, dtype=str)
                df = pd.concat(sheets.values(), ignore_index=True)
            all_data.append(df)
        except:
            continue
    return pd.concat(all_data, ignore_index=True) if all_data else None

st.title("🏫 Maktab AI Yordamchisi")
df = yuklash()

# --- CHAT TARIXI ---
if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# --- ASOSIY JARAYON ---
if savol := st.chat_input("Salom deb yozing yoki ma'lumot so'rang..."):
    st.session_state.messages.append({"role": "user", "content": savol})
    with st.chat_message("user"):
        st.markdown(savol)

    with st.chat_message("assistant"):
        # 1. Bazadan qidirish
        context = ""
        if df is not None:
            # Ismni bazadan qidirish (katta-kichik harfga qaramaydi)
            mask = df.apply(lambda row: row.astype(str).str.contains(savol, case=False, na=False).any(), axis=1)
            results = df[mask].head(10)
            if not results.empty:
                context = "Bazadan topilgan ma'lumotlar:\n" + results.to_string(index=False)

        # 2. TO'G'IRLANGAN GOOGLE API SO'ROVI (v1 versiyasi)
        # 404 xatosini oldini olish uchun URL va model nomi o'zgartirildi
        url = f"https://generativelanguage.googleapis.com/v1/models/gemini-1.5-flash:generateContent?key={API_KEY}"
        headers = {'Content-Type': 'application/json'}
        
        prompt = f"Sen samimiy maktab yordamchisisan. Foydalanuvchi savoliga o'zbek tilida javob ber."
        if context:
            prompt += f"\n\nQuyidagi ma'lumotlar bazadan topildi, shularga tayanib javob ber:\n{context}"
        
        prompt += f"\n\nSavol: {savol}"

        payload = {
            "contents": [{"parts": [{"text": prompt}]}]
        }

        try:
            with st.spinner("O'ylayapman..."):
                r = requests.post(url, headers=headers, data=json.dumps(payload))
                res_json = r.json()
                
                if r.status_code == 200:
                    full_res = res_json['candidates'][0]['content']['parts'][0]['text']
                    st.markdown(full_res)
                    st.session_state.messages.append({"role": "assistant", "content": full_res})
                else:
                    # Agar v1 ham xato bersa, xatoni aniq ko'rsatadi
                    error_msg = res_json.get('error', {}).get('message', 'Nomaalum xato')
                    st.error(f"API xatosi: {error_msg}")
        except Exception as e:
            st.error(f"Ulanishda xato: {str(e)}")
