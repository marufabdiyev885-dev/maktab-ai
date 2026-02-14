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

# --- 2. DIZAYN (CSS) ---
def set_bg(url):
    st.markdown(
        f"""
        <style>
        .stApp {{
            background: linear-gradient(rgba(0,0,0,0.5), rgba(0,0,0,0.5)), url("{url}");
            background-size: cover;
            background-position: center;
            background-attachment: fixed;
        }}
        
        /* Maktab nomi */
        .school-title {{
            color: white;
            font-size: 40px;
            font-weight: bold;
            text-align: center;
            text-shadow: 2px 2px 10px rgba(0,0,0,0.9);
            margin-top: 50px;
            margin-bottom: 10px;
        }}

        /* OQ BLOK (Login Card) */
        .login-box {{
            background-color: rgba(255, 255, 255, 0.95);
            padding: 25px 35px;
            border-radius: 20px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.5);
            max-width: 400px;
            margin: auto;
            text-align: center;
            min-height: 250px; /* Blok balandligini saqlash uchun */
        }}

        /* "Tizimga kirish" sarlavhasini oq blok ustiga chiqarish */
        .login-text {{
            color: #1E1E1E;
            font-size: 26px;
            font-weight: bold;
            margin-top: -10px; /* Blok ichida yuqoriga surish */
            margin-bottom: 20px;
            display: block;
        }}
        
        /* Input ichidagi ortiqcha joylarni olish */
        div[data-baseweb="input"] {{
            margin-top: -10px !important;
        }}
        </style>
        """,
        unsafe_allow_html=True
    )

# --- 3. LOGIN EKRANI ---
if "authenticated" not in st.session_state:
    login_rasmlar = [
        "https://images.unsplash.com/photo-1509062522246-3755977927d7?q=80&w=1600",
        "https://images.unsplash.com/photo-1524178232363-1fb2b075b655?q=80&w=1600"
    ]
    
    if "bg_url" not in st.session_state:
        st.session_state.bg_url = random.choice(login_rasmlar)
    
    set_bg(st.session_state.bg_url)

    # 1. Maktab nomi (Tepada)
    st.markdown(f'<div class="school-title">🏛 {MAKTAB_NOMI}</div>', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 1.3, 1])
    with col2:
        # --- OQ BLOK BOSHLANISHI ---
        st.markdown('<div class="login-box">', unsafe_allow_html=True)
        
        # 2. Tizimga kirish (Blokning ichida, eng tepada)
        st.markdown('<span class="login-text">Tizimga kirish</span>', unsafe_allow_html=True)
        
        # 3. Parol kiritish
        parol = st.text_input("", placeholder="Parolni kiriting...", type="password", key="login_pass", label_visibility="collapsed")
        
        st.write("<br>", unsafe_allow_html=True)
        
        # 4. Tugma
        if st.button("Kirish 🚀", use_container_width=True):
            if parol == TO_GRI_PAROL:
                st.session_state.authenticated = True
                st.rerun()
            else:
                st.error("❌ Parol noto'g'ri!")
        
        st.markdown('</div>', unsafe_allow_html=True) 
        # --- OQ BLOK TUGASHI ---
    st.stop()

# --- 4. TIZIMGA KIRGANDAN KEYINGI QISM ---
st.markdown("<style>.stApp {background: none !important;}</style>", unsafe_allow_html=True)

with st.sidebar:
    st.markdown(f"### 🏛 {MAKTAB_NOMI}")
    st.divider()
    menu = st.radio("Bo'limni tanlang:", ["🤖 AI Yordamchi", "📊 Jurnal Monitoringi"])

st.title(f"Xush kelibsiz! {menu}")
# (Qolgan AI va Monitoring kodlarini shu yerga davom ettirasiz...)
