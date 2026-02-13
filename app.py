import streamlit as st
import requests
import pandas as pd

# 1. API va Xavfsizlik sozlamalari
API_KEY = "AIzaSyAp3ImXzlVyNF_UXjes2LsSVhG0Uusobdw"
TO_GRI_PAROL = "informatika2024"

st.set_page_config(page_title="Maktab AI | Ma'rufjon Abdiyev", layout="centered")

# --- PAROL TEKSHIRISH ---
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

# --- ASOSIY DASTUR ---
st.markdown("""
    <style>
    .main {background-color: #f8f9fa;}
    .stChatFloatingInputContainer {bottom: 20px;}
    </style>
    """, unsafe_allow_html=True)

with st.sidebar:
    st.title("👨‍🏫 Ustoz Panel")
    st.info("Abdiyev Ma'rufjon")
    if st.button("Chiqish"):
        del st.session_state.authenticated
        st.rerun()
    st.divider()
    uploaded_file = st.file_uploader("Bazani yuklang (Excel/CSV)", type=['xlsx', 'csv'])

st.title("🏫 Maktab AI Yordamchisi")
st.write("Savollaringizga maktab bazasi asosida javob beraman.")

# Modelni aniqlash
if 'active_model' not in st.session_state:
    try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models?key={API_KEY}"
        res = requests.get(url).json()
        st.session_state.active_model = next((m['name'] for m in res['models'] if 'gemini-1.5-flash' in m['name']), res['models'][0]['name'])
    except:
        st.session_state.active_model = None

# Mantiq (Jadval ekranga chiqmaydi)
if uploaded_file:
    try:
        # Ma'lumotlarni yuklaymiz, lekin ko'rsatmaymiz
        df = pd.read_csv(uploaded_file) if uploaded_file.name.endswith('.csv') else pd.read_excel(uploaded_file)
        
        st.success("✅ Ma'lumotlar bazasi yuklangan. AI tayyor!")
        
        # Chat interfeysi
        savol = st.chat_input("O'quvchi yoki sinf haqida so'rang...")

        if savol:
            with st.chat_message("user"):
                st.write(savol)
            
            with st.chat_message("assistant"):
                # AI faqat kerakli qismini ko'rishi uchun jadvalni matnga aylantiramiz
                context = df.to_string(index=False, max_rows=100) 
                url = f"https://generativelanguage.googleapis.com/v1beta/{st.session_state.active_model}:generateContent?key={API_KEY}"
                
                with st.spinner("Qidiryapman..."):
                    payload = {"contents": [{"parts": [{"text": f"Jadval ma'lumotlari: {context}\nSavol: {savol}"}]}]}
                    r = requests.post(url, json=payload)
                    if r.status_code == 200:
                        st.write(r.json()['candidates'][0]['content']['parts'][0]['text'])
                    else:
                        st.error("API xatosi.")
    except Exception as e:
        st.error(f"Xato: {e}")
else:
    st.info("👈 Davom etish uchun bazani (Excel) yuklang. Jadval ekranda ko'rinmaydi, xavotir olmang.")