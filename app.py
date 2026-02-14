import streamlit as st
import pandas as pd
import os
import requests
import random

# --- 1. ASOSIY SOZLAMALAR ---
MAKTAB_NOMI = "1-sonli umumiy o'rta ta'lim maktabi"
DIREKTOR_FIO = "Mahmudov Matyoqub Narzulloyevich"
TO_GRI_PAROL = "informatika2024"

st.set_page_config(page_title=MAKTAB_NOMI, layout="wide")

# --- 2. YANGI ZAMONAVIY DIZAYN (CSS) ---
def apply_internal_design():
    st.markdown(
        """
        <style>
        /* Umumiy fon rangi */
        .stApp {
            background-color: #F0F2F6;
        }

        /* Sidebar (Chap menyu) dizayni */
        [data-testid="stSidebar"] {
            background-color: #FFFFFF;
            padding: 20px;
            border-right: none;
            box-shadow: 2px 0 15px rgba(0,0,0,0.05);
        }

        /* Sidebar ichidagi sarlavha bloki */
        .sidebar-header {
            background-color: #F8F9FA;
            padding: 15px;
            border-radius: 12px;
            text-align: center;
            margin-bottom: 20px;
            border: 1px solid #E9ECEF;
        }

        /* Menyu tugmalari (Radio buttonlarni o'zgartirish) */
        .stRadio div[role="radiogroup"] > label {
            background-color: #1E293B;
            color: white !important;
            padding: 12px 20px;
            border-radius: 25px;
            margin-bottom: 10px;
            border: none;
            transition: 0.3s;
        }

        /* Asosiy oq blok (Chat va Monitoring uchun) */
        .main-card {
            background-color: white;
            padding: 30px;
            border-radius: 20px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.05);
            min-height: 80vh;
        }

        /* Chat sarlavhasi dizayni */
        .ai-title-box {
            border: 2px solid #3B82F6;
            border-radius: 12px;
            padding: 15px;
            margin-bottom: 25px;
            background-color: white;
        }
        
        /* Chat xabarlari (Pufakchalar) */
        .stChatMessage {
            border-radius: 20px !important;
            padding: 15px !important;
        }
        
        /* User xabari (o'ngda bo'lishi uchun) */
        [data-testid="chatAvatarIcon-user"] {
            background-color: #64748B !important;
        }

        /* Chiqish tugmasi (Ko'k rangli dumaloq) */
        .stButton>button {
            width: 100%;
            border-radius: 25px;
            background-color: #007BFF;
            color: white;
            border: none;
            font-weight: bold;
            padding: 10px;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

def set_login_bg():
    st.markdown(
        f"""
        <style>
        .stApp {{
            background: linear-gradient(rgba(0,0,0,0.6), rgba(0,0,0,0.6)), url("https://images.unsplash.com/photo-1509062522246-3755977927d7?q=80&w=1600");
            background-size: cover; background-position: center;
        }}
        header {{visibility: hidden;}}
        .white-text {{color: white; text-align: center; text-shadow: 2px 2px 10px black; width: 100%;}}
        .school-title {{font-size: 45px; font-weight: bold; padding-top: 100px;}}
        .login-title {{font-size: 30px; margin-top: 20px; text-align: center; color: white;}}
        div[data-baseweb="input"] {{background-color: white !important; border-radius: 12px !important;}}
        </style>
        """,
        unsafe_allow_html=True
    )

# --- 3. LOGIN LOGIKASI ---
if "authenticated" not in st.session_state:
    set_login_bg()
    st.markdown(f'<div class="white-text school-title">🏛 {MAKTAB_NOMI}</div>', unsafe_allow_html=True)
    st.markdown('<div class="login-title">Tizimga kirish</div>', unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        parol = st.text_input("", placeholder="Parolni kiriting...", type="password", label_visibility="collapsed")
        if st.button("Kirish 🚀", use_container_width=True):
            if parol == TO_GRI_PAROL:
                st.session_state.authenticated = True
                st.rerun()
            else: st.error("Parol xato!")
    st.stop()

# --- 4. ICHKI SAHIFA (RASMDAGI DIZAYN) ---
apply_internal_design()

# SIDEBAR (Chap tomon)
with st.sidebar:
    st.markdown('<div class="sidebar-header"><h3>🏛 Maktab Paneli</h3></div>', unsafe_allow_html=True)
    st.write(f"👤 **Direktor:**\n{DIREKTOR_FIO}")
    st.divider()
    
    # Menyu (AI va Monitoring)
    menu = st.radio("", ["🤖 AI Assistant", "🎵 Monitoring"], label_visibility="collapsed")
    
    st.write("<br>" * 5, unsafe_allow_html=True) # Bo'sh joy
    if st.button("Chiqish 🚪"):
        del st.session_state.authenticated
        st.rerun()

# ASOSIY QISM (O'ng tomon)
st.markdown('<div class="main-card">', unsafe_allow_html=True)

if menu == "🤖 AI Assistant":
    # Sarlavha bloki (Rasmda ko'kdagi ramka kabi)
    st.markdown('''
        <div class="ai-title-box">
            <h2 style="color: #1E293B; margin: 0;">🤖 Sun'iy Intellekt Yordamchisi</h2>
            <p style="color: #64748B; margin: 0;">Maktab bazasi asosida savollarga javob beradi</p>
        </div>
    ''', unsafe_allow_html=True)

    # Chat xabarlari
    if "messages" not in st.session_state:
        st.session_state.messages = [{"role": "assistant", "content": "Assalomu alaykum! Maktab hujjatlari bo'yicha nima yordam bera olaman?"}]

    for m in st.session_state.messages:
        with st.chat_message(m["role"]):
            st.markdown(m["content"])

    if savol := st.chat_input("Savolingizni bu yerga yozing..."):
        st.session_state.messages.append({"role": "user", "content": savol})
        with st.chat_message("user"): st.markdown(savol)
        with st.chat_message("assistant"):
            st.markdown("🔍 O'ylayapman...") # Bu yerga AI javobini ulasangiz bo'ladi

elif menu == "🎵 Monitoring":
    st.markdown('<div class="ai-title-box"><h2 style="color: #1E293B; margin: 0;">📊 Jurnal Monitoringi</h2></div>', unsafe_allow_html=True)
    st.info("Fayllarni yuklang va tahlil natijalarini ko'ring.")
    st.file_uploader("eMaktab faylini tanlang", type=["xlsx"])

st.markdown('</div>', unsafe_allow_html=True)
