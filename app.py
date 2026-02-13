import streamlit as st
import requests
import pandas as pd
import os

# 1. API va Xavfsizlik sozlamalari
API_KEY = "AIzaSyAp3ImXzlVyNF_UXjes2LsSVhG0Uusobdw"
TO_GRI_PAROL = "informatika2024"
FAYL_NOMI = "baza.xlsx"  # GitHub'ga yuklaydigan faylingiz nomi aynan shunday bo'lsin

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
    </style>
    """, unsafe_allow_html=True)

with st.sidebar:
    st.title("👨‍🏫 Ustoz Panel")
    st.info(f"Abdiyev Ma'rufjon")
    if st.button("Chiqish"):
        del st.session_state.authenticated
        st.rerun()
    st.divider()
    st.write("Baza holati:")
    if os.path.exists(FAYL_NOMI):
        st.success("✅ Baza topildi va yuklangan")
    else:
        st.error("⚠️ baza.xlsx topilmadi!")

st.title("🏫 Maktab AI Yordamchisi")
st.write("Men maktab bazasi asosida savollaringizga javob beraman.")

# Modelni aniqlash
if 'active_model' not in st.session_state:
    st.session_state.active_model = "gemini-1.5-flash"

# --- BAZANI AVTOMATIK O'QISH ---
if os.path.exists(FAYL_NOMI):
    try:
        # Excel faylni o'qish
        df = pd.read_excel(FAYL_NOMI)
        
        # Chat interfeysi
        savol = st.chat_input("O'quvchi yoki sinf haqida so'rang...")

        if savol:
            with st.chat_message("user"):
                st.write(savol)
            
            with st.chat_message("assistant"):
                # Jadvalni matn ko'rinishiga o'tkazish
                context = df.to_string(index=False) 
                url = f"https://generativelanguage.googleapis.com/v1beta/models/{st.session_state.active_model}:generateContent?key={API_KEY}"
                
                with st.spinner("Qidiryapman..."):
                    payload = {
                        "contents": [{
                            "parts": [{
                                "text": f"Quyidagi jadval ma'lumotlari asosida savolga o'zbek tilida javob ber:\n\n{context}\n\nSavol: {savol}"
                            }]
                        }]
                    }
                    r = requests.post(url, json=payload)
                    if r.status_code == 200:
                        res_json = r.json()
                        st.write(res_json['candidates'][0]['content']['parts'][0]['text'])
                    else:
                        st.error(f"API xatosi: {r.status_code}")
    except Exception as e:
        st.error(f"Faylni o'qishda xato: {e}")
else:
    st.warning(f"⚠️ GitHub-da '{FAYL_NOMI}' fayli topilmadi. Iltimos, faylni yuklang.")
