import streamlit as st
import pandas as pd
import os
import requests

# --- 1. ASOSIY SOZLAMALAR ---
MAKTAB_NOMI = "1-sonli umumiy o'rta ta'lim maktabi"
DIREKTOR_FIO = "Mahmudov Matyoqub Narzulloyevich"
TO_GRI_PAROL = "informatika2024"

st.set_page_config(page_title=MAKTAB_NOMI, layout="wide")

# --- 2. RASMDAGI DIZAYN (ULTRA MODERN CSS) ---
def apply_internal_design():
    st.markdown(
        """
        <style>
        /* Umumiy fon */
        .stApp {
            background-color: #f4f7f9;
        }

        /* SIDEBARNI RASMDAGIDEK QILISH */
        [data-testid="stSidebar"] {
            background-color: #ffffff;
            border-right: 1px solid #e6e9ef;
        }
        
        /* Sidebar ichidagi direktor bloki */
        .sidebar-user-card {
            background-color: #f8fafc;
            border-radius: 15px;
            padding: 15px;
            margin-bottom: 20px;
            border: 1px solid #f1f5f9;
        }

        /* ASOSIY OQ KONTEYNER */
        .main-content-card {
            background-color: #ffffff;
            border-radius: 24px;
            padding: 40px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.03);
            margin-top: 20px;
        }

        /* CHAT SARLAVHASI (KO'K RAMKA) */
        .ai-header-box {
            border: 1.5px solid #3b82f6;
            border-radius: 12px;
            padding: 20px;
            margin-bottom: 30px;
            display: flex;
            align-items: center;
            gap: 15px;
        }

        /* CHAT PUFAKCHALARI (MESSAGE BUBBLES) */
        .stChatMessage {
            border-radius: 20px !important;
            border: none !important;
            background-color: #f1f5f9 !important; /* Standart fon */
            margin-bottom: 15px !important;
        }
        
        /* Assistant xabari ko'kroq fon */
        [data-testid="stChatMessageAssistant"] {
            background-color: #e0f2fe !important;
            color: #0369a1 !important;
        }

        /* User xabari kulrangroq fon */
        [data-testid="stChatMessageUser"] {
            background-color: #f1f5f9 !important;
        }

        /* MENYU TUGMALARI */
        .stRadio div[role="radiogroup"] > label {
            background-color: #1e293b !important; /* To'q rangli rasm kabi */
            color: white !important;
            border-radius: 30px !important;
            padding: 10px 25px !important;
            margin-bottom: 8px !important;
            font-size: 14px !important;
            font-weight: 500 !important;
            transition: all 0.2s ease;
        }
        
        .stRadio div[role="radiogroup"] > label:hover {
            transform: scale(1.02);
        }

        /* CHIQUVCHI TUGMA */
        .stButton > button {
            background: linear-gradient(90deg, #3b82f6, #2563eb);
            color: white;
            border-radius: 30px;
            padding: 12px 30px;
            border: none;
            width: 100%;
            font-weight: 600;
            box-shadow: 0 4px 12px rgba(37, 99, 235, 0.2);
        }

        /* CHAT INPUT (PASTDAGI YOZISH JOYI) */
        .stChatInputContainer {
            background-color: #1e293b !important;
            border-radius: 15px !important;
            padding: 5px !important;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

# --- 3. LOGIN (O'ZGARISHSIZ) ---
if "authenticated" not in st.session_state:
    st.markdown("""<style>
    .stApp { background: linear-gradient(rgba(0,0,0,0.6), rgba(0,0,0,0.6)), url("https://images.unsplash.com/photo-1509062522246-3755977927d7?q=80&w=1600"); background-size: cover; }
    header {visibility: hidden;} .white-text {color: white; text-align: center; text-shadow: 2px 2px 10px black; width: 100%;}
    .school-title {font-size: 45px; font-weight: bold; padding-top: 100px;} .login-title {font-size: 30px; margin-top: 20px; text-align: center; color: white;}
    div[data-baseweb="input"] {background-color: white !important; border-radius: 12px !important;}
    </style>""", unsafe_allow_html=True)
    st.markdown(f'<div class="white-text school-title">🏛 {MAKTAB_NOMI}</div>', unsafe_allow_html=True)
    st.markdown('<div class="login-title">Tizimga kirish</div>', unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        parol = st.text_input("", placeholder="Parolni kiriting...", type="password", label_visibility="collapsed")
        if st.button("Kirish 🚀", use_container_width=True):
            if parol == TO_GRI_PAROL: st.session_state.authenticated = True; st.rerun()
            else: st.error("Xato!")
    st.stop()

# --- 4. ICHKI PANAL (RASMDAGI NUSXA) ---
apply_internal_design()

# SIDEBAR
with st.sidebar:
    st.markdown(f'''
        <div style="background-color: #1e293b; padding: 20px; border-radius: 15px; text-align: center; margin-bottom: 25px;">
            <h3 style="color: white; margin: 0; font-size: 18px;">🏛 Maktab Paneli</h3>
        </div>
    ''', unsafe_allow_html=True)
    
    st.markdown(f'''
        <div class="sidebar-user-card">
            <p style="margin: 0; font-size: 12px; color: #64748b;">👤 Direktor:</p>
            <p style="margin: 0; font-weight: bold; color: #1e293b; font-size: 14px;">{DIREKTOR_FIO}</p>
        </div>
    ''', unsafe_allow_html=True)
    
    menu = st.radio("", ["🤖 AI Assistant", "🎵 Monitoring"], label_visibility="collapsed")
    
    st.markdown("<br>" * 10, unsafe_allow_html=True)
    if st.button("Chiqish 🚪"):
        del st.session_state.authenticated
        st.rerun()

# ASOSIY QISM
st.markdown('<div class="main-content-card">', unsafe_allow_html=True)

if menu == "🤖 AI Assistant":
    # Ko'k ramkali sarlavha
    st.markdown('''
        <div class="ai-header-box">
            <span style="font-size: 30px;">🤖</span>
            <div>
                <h2 style="margin: 0; color: #1e293b; font-size: 24px;">Sun'iy Intellekt Yordamchisi</h2>
                <p style="margin: 0; color: #64748b; font-size: 14px;">Maktab bazasia asosida savollarga javob beradi</p>
            </div>
        </div>
    ''', unsafe_allow_html=True)

    if "messages" not in st.session_state:
        st.session_state.messages = [{"role": "assistant", "content": "Assalomu alaykum! Maktab hujjutari bo'yicha nima yordam bera olaman?"}]

    for m in st.session_state.messages:
        with st.chat_message(m["role"]):
            st.markdown(m["content"])

    if savol := st.chat_input("Savolingizni bu yerga yozing..."):
        st.session_state.messages.append({"role": "user", "content": savol})
        with st.chat_message("user"): st.markdown(savol)
        # AI Logic...

elif menu == "🎵 Monitoring":
    st.markdown('<div class="ai-header-box"><span style="font-size: 30px;">📈</span><h2 style="margin: 0;">Monitoring</h2></div>', unsafe_allow_html=True)
    st.file_uploader("Faylni tanlang", type=["xlsx"])

st.markdown('</div>', unsafe_allow_html=True)
