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

# --- 2. UMUMIY DIZAYN (CSS) ---
def apply_custom_design():
    st.markdown(
        """
        <style>
        /* Sidebar dizayni */
        [data-testid="stSidebar"] {
            background-color: #f8f9fa;
            border-right: 1px solid #e0e0e0;
        }
        
        /* Tugmalarni chiroyli qilish */
        .stButton>button {
            border-radius: 8px;
            background-color: #007bff;
            color: white;
            font-weight: bold;
            transition: 0.3s;
        }
        .stButton>button:hover {
            background-color: #0056b3;
            border-color: #0056b3;
        }

        /* Sahifa sarlavhalari */
        .main-header {
            color: #2c3e50;
            font-size: 32px;
            font-weight: bold;
            border-left: 5px solid #007bff;
            padding-left: 15px;
            margin-bottom: 25px;
        }
        
        /* Chat xabarlari uchun maxsus qoliplar */
        .stChatMessage {
            border-radius: 15px;
            padding: 10px;
            margin-bottom: 10px;
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
            background-size: cover; background-position: center; background-attachment: fixed;
        }}
        header {{visibility: hidden;}}
        .main .block-container {{padding-top: 0rem;}}
        .white-text {{color: white; text-align: center; text-shadow: 2px 2px 10px black; width: 100%;}}
        .school-title {{font-size: 42px; font-weight: bold; padding-top: 80px;}}
        .login-title {{font-size: 28px; margin-top: 20px;}}
        div[data-baseweb="input"] {{background-color: rgba(255, 255, 255, 0.9) !important; border-radius: 12px !important;}}
        </style>
        """,
        unsafe_allow_html=True
    )

# --- 3. XAVFSIZLIK (LOGIN) ---
if "authenticated" not in st.session_state:
    set_login_bg("https://images.unsplash.com/photo-1509062522246-3755977927d7?q=80&w=1600")
    st.markdown(f'<div class="white-text school-title">🏛 {MAKTAB_NOMI}</div>', unsafe_allow_html=True)
    st.markdown('<div class="white-text login-title">Tizimga kirish</div>', unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        parol = st.text_input("", placeholder="Parolni kiriting...", type="password", label_visibility="collapsed")
        if st.button("Kirish 🚀", use_container_width=True):
            if parol == TO_GRI_PAROL:
                st.session_state.authenticated = True
                st.rerun()
            else: st.error("❌ Xato!")
    st.stop()

# --- 4. ASOSIY TIZIM ---
apply_custom_design()

with st.sidebar:
    st.markdown(f"## 🏛 Maktab Paneli")
    st.info(f"👤 **Direktor:**\n{DIREKTOR_FIO}")
    st.divider()
    menu = st.radio("Bo'limlar:", ["🤖 AI Assistant", "📊 Monitoring"], index=0)
    if st.button("Chiqish 🚪"):
        del st.session_state.authenticated
        st.rerun()

# --- 5. SAHIFALAR ---

if menu == "🤖 AI Assistant":
    st.markdown('<div class="main-header">🤖 Sun\'iy Intellekt Yordamchisi</div>', unsafe_allow_html=True)
    st.caption("Maktab bazasi asosida savollarga javob beradi")
    
    # Chat dizayni
    if "messages" not in st.session_state:
        st.session_state.messages = [{"role": "assistant", "content": "Assalomu alaykum! Maktab hujjatlari bo'yicha nima yordam bera olaman?"}]
    
    for m in st.session_state.messages:
        with st.chat_message(m["role"]):
            st.markdown(m["content"])

    if savol := st.chat_input("Savolingizni bu yerga yozing..."):
        st.session_state.messages.append({"role": "user", "content": savol})
        with st.chat_message("user"): st.markdown(savol)
        with st.chat_message("assistant"):
            st.spinner("O'ylayapman...")
            # AI logic (bu yerga GROQ payload-ni qo'yasiz)
            ai_text = "Hozircha men test rejimida ishlayapman." 
            st.markdown(ai_text)
            st.session_state.messages.append({"role": "assistant", "content": ai_text})

elif menu == "📊 Monitoring":
    st.markdown('<div class="main-header">📊 Jurnal Monitoringi</div>', unsafe_allow_html=True)
    
    tab1, tab2 = st.tabs(["📁 Fayl Yuklash", "📈 Hisobot"])
    
    with tab1:
        st.markdown("#### eMaktab faylini tanlang")
        uploaded_file = st.file_uploader("", type=["xlsx", "xls"])
        if uploaded_file:
            st.success("Fayl qabul qilindi!")
            df = pd.read_excel(uploaded_file)
            st.dataframe(df.style.highlight_max(axis=0), use_container_width=True)
    
    with tab2:
        st.warning("Hisobot shakllanishi uchun fayl yuklang.")
