import streamlit as st
import pandas as pd
import os
import requests
import re
import docx
import random

# --- 1. ASOSIY SOZLAMALAR ---
MAKTAB_NOMI = "1-sonli umumiy o'rta ta'lim maktabi"
DIREKTOR_FIO = "Mahmudov Matyoqub Narzulloyevich"
GROQ_API_KEY = "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"
TO_GRI_PAROL = "informatika2024"
MONITORING_KODI = "admin777"
BOT_TOKEN = "8524007504:AAFiMXSbXhe2M-84WlNM16wNpzhNolfQIf8"
GURUH_ID = "-1003047388159"

st.set_page_config(page_title=MAKTAB_NOMI, layout="wide")

# --- 2. DIZAYN (FON VA MATN) ---
def set_bg(url):
    st.markdown(
        f"""
        <style>
        .stApp {{
            background: linear-gradient(rgba(0,0,0,0.6), rgba(0,0,0,0.6)), url("{url}");
            background-size: cover;
            background-position: center;
            background-attachment: fixed;
        }}
        
        /* Oq rangdagi sarlavhalar uchun umumiy uslub */
        .white-text {{
            color: white;
            text-align: center;
            text-shadow: 2px 2px 10px rgba(0,0,0,0.9);
            font-family: sans-serif;
            width: 100%;
        }}
        
        .school-title {{
            font-size: 45px;
            font-weight: bold;
            margin-top: 50px;
            margin-bottom: 20px;
        }}

        .login-title {{
            font-size: 30px;
            font-weight: bold;
            margin-top: 20px;
            margin-bottom: 20px;
        }}

        /* Input va tugmani markazlashtirish va chiroyli qilish */
        .stTextInput, .stButton {{
            max-width: 400px;
            margin: auto;
        }}
        
        /* Input ichini biroz shaffof va chiroyli qilish */
        div[data-baseweb="input"] {{
            background-color: rgba(255, 255, 255, 0.9) !important;
            border-radius: 10px !important;
        }}
        </style>
        """,
        unsafe_allow_html=True
    )

# --- 3. XAVFSIZLIK (LOGIN EKRANI) ---
if "authenticated" not in st.session_state:
    login_rasmlar = [
        "https://images.unsplash.com/photo-1509062522246-3755977927d7?q=80&w=1600",
        "https://images.unsplash.com/photo-1524178232363-1fb2b075b655?q=80&w=1600"
    ]
    
    if "bg_url" not in st.session_state:
        st.session_state.bg_url = random.choice(login_rasmlar)
    
    set_bg(st.session_state.bg_url)

    # 1. Maktab nomi (Oq rangda)
    st.markdown(f'<div class="white-text school-title">🏛 {MAKTAB_NOMI}</div>', unsafe_allow_html=True)
    
    # Bo'sh joy tashlash
    st.write("<br><br>", unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        # 2. Tizimga kirish so'zi (Oq rangda, fonsiz)
        st.markdown('<div class="white-text login-title">Tizimga kirish</div>', unsafe_allow_html=True)
        
        # 3. Parol kiritish (Ichida placeholder bilan)
        parol = st.text_input("", placeholder="Parolni kiriting...", type="password", key="login_pass", label_visibility="collapsed")
        
        st.write("") # Kichik bo'shliq
        
        # 4. Tugma
        if st.button("Kirish 🚀", use_container_width=True):
            if parol == TO_GRI_PAROL:
                st.session_state.authenticated = True
                st.rerun()
            else:
                st.error("❌ Parol noto'g'ri!")
    st.stop()

# --- QOLGAN FUNKSIYALAR (O'zgarishsiz qoladi) ---
st.markdown("<style>.stApp {background: none !important;}</style>", unsafe_allow_html=True)
st.success("Tizimga xush kelibsiz!")
# ... (AI va Monitoring kodlari shu yerdan davom etadi)
