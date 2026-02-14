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

# --- 2. DIZAYN FUNKSIYALARI ---
def apply_custom_design():
    st.markdown(
        """
        <style>
        /* Sidebar rangini yumshatish */
        [data-testid="stSidebar"] {
            background-color: #f0f2f6;
            border-right: 1px solid #d1d5db;
        }
        
        /* Asosiy sarlavha stili */
        .main-header {
            color: #1e3a8a;
            font-size: 32px;
            font-weight: bold;
            border-left: 6px solid #3b82f6;
            padding-left: 15px;
            margin-bottom: 20px;
        }

        /* Chat xabarlari dizayni */
        .stChatMessage {
            background-color: rgba(59, 130, 246, 0.05);
            border-radius: 12px;
        }

        /* Tugmalar stili */
        .stButton>button {
            border-radius: 10px;
            background-color: #3b82f6;
            color: white;
            transition: 0.3s;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

def set_login_bg(url):
    st.markdown(
        f"""
        <style>
        .stApp {{
            background: linear-gradient(rgba(0,0,0,0.6), rgba(0,0,0,0.6)), url("{url}");
            background-size: cover;
            background-position: center;
            background-attachment: fixed;
        }}
        header {{visibility: hidden;}}
        .main .block-container {{padding-top: 0rem;}}
        .white-text {{
            color: white;
            text-align: center;
            text-shadow: 2px 2px 12px rgba(0,0,0,1);
            font-family: sans-serif;
            width: 100%;
        }}
        .school-title {{font-size: 45px; font-weight: bold; padding-top: 100px;}}
        .login-title {{font-size: 30px; margin-top: 20px;}}
        div[data-baseweb="input"] {{
            background-color: rgba(255, 255, 255, 0.95) !important;
            border-radius: 12px !important;
            max-width: 380px;
            margin: auto;
        }}
        </style>
        """,
        unsafe_allow_html=True
    )

# --- 3. LOGIN EKRANI ---
if "authenticated" not in st.session_state:
    set_login_bg("https://images.unsplash.com/photo-1509062522246-3755977927d7?q=80&w=1600")
    st.markdown(f'<div class="white-text school-title">🏛 {MAKTAB_NOMI}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="white-text login-title">Tizimga kirish</div>', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        parol = st.text_input("", placeholder="Parolni kiriting...", type="password", label_visibility="collapsed")
        if st.button("Kirish 🚀", use_container_width=True):
            if parol == TO_GRI_PAROL:
