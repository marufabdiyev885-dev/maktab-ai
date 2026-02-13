import streamlit as st
import google.generativeai as genai
import pandas as pd
import os

# 1. API VA SOZLAMALAR
API_KEY = "AIzaSyAp3ImXzlVyNF_UXjes2LsSVhG0Uusobdw"
TO_GRI_PAROL = "informatika2024"

# Google AI sozlash
genai.configure(api_key=API_KEY)

st.set_page_config(page_title="Maktab AI", layout="centered")

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
if savol := st.chat_input("Salom deb yozing yoki ism so'rang..."):
    st.session_state.messages.append({"role": "user", "content": savol})
    with st.chat_message("user"):
        st.markdown(savol)

    with st.chat_message("assistant"):
        # 1. Bazadan qidirish
        context = ""
        if df is not None:
            mask = df.apply(lambda row: row.astype(str).str.contains(savol, case=False, na=False).any(), axis=1)
            results = df[mask].head(10)
            if not results.empty:
                context = results.to_string(index=False)

        # 2. AI javobi
        try:
            # Eng ishonchli model nomini prefiks bilan yozamiz
            model = genai.GenerativeModel('models/gemini-1.5-flash')
            
            if context:
                full_prompt = f"Sen maktab yordamchisisan. Mana bu ma'lumotlar asosida javob ber: {context}\nSavol: {savol}"
            else:
                full_prompt = f"Sen samimiy maktab yordamchisisan. Foydalanuvchi bilan gaplash (salomlashsa alik ol). Savol: {savol}"
            
            with st.spinner("O'ylayapman..."):
                response = model.generate_content(full_prompt)
                full_res = response.text
                st.markdown(full_res)
                st.session_state.messages.append({"role": "assistant", "content": full_res})
        
        except Exception as e:
            # Agar 1.5-flash ishlamasa, zaxira modelni sinab ko'radi
            try:
                model_alt = genai.GenerativeModel('models/gemini-pro')
                response = model_alt.generate_content(savol)
                st.markdown(response.text)
                st.session_state.messages.append({"role": "assistant", "content": response.text})
            except Exception as e2:
                st.error(f"Texnik xatolik: {str(e2)}")
