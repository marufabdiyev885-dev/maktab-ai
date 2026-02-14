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

# --- 2. DIZAYN (RASMGA O'XSHATILGAN CSS) ---
def apply_internal_design():
    st.markdown(
        """
        <style>
        .stApp { background-color: #f4f7f9; }
        [data-testid="stSidebar"] { background-color: #ffffff; border-right: 1px solid #e6e9ef; }
        .sidebar-user-card { background-color: #f8fafc; border-radius: 15px; padding: 15px; margin-bottom: 20px; border: 1px solid #f1f5f9; }
        .main-content-card { background-color: #ffffff; border-radius: 24px; padding: 30px; box-shadow: 0 10px 40px rgba(0,0,0,0.03); margin-top: 10px; }
        .ai-header-box { border: 1.5px solid #3b82f6; border-radius: 12px; padding: 20px; margin-bottom: 25px; display: flex; align-items: center; gap: 15px; }
        .stChatMessage { border-radius: 20px !important; margin-bottom: 10px !important; }
        [data-testid="stChatMessageAssistant"] { background-color: #e0f2fe !important; color: #0369a1 !important; }
        .stRadio div[role="radiogroup"] > label { background-color: #1e293b !important; color: white !important; border-radius: 30px !important; padding: 10px 25px !important; margin-bottom: 8px !important; transition: 0.2s; }
        .stButton > button { background: linear-gradient(90deg, #3b82f6, #2563eb); color: white; border-radius: 30px; width: 100%; font-weight: 600; }
        </style>
        """,
        unsafe_allow_html=True
    )

def set_login_bg():
    st.markdown(f"""<style>
    .stApp {{ background: linear-gradient(rgba(0,0,0,0.6), rgba(0,0,0,0.6)), url("https://images.unsplash.com/photo-1509062522246-3755977927d7?q=80&w=1600"); background-size: cover; }}
    header {{visibility: hidden;}} .white-text {{color: white; text-align: center; text-shadow: 2px 2px 10px black; width: 100%;}}
    .school-title {{font-size: 45px; font-weight: bold; padding-top: 100px;}} .login-title {{font-size: 30px; margin-top: 20px; text-align: center; color: white;}}
    div[data-baseweb="input"] {{background-color: white !important; border-radius: 12px !important;}}
    </style>""", unsafe_allow_html=True)

# --- 3. BAZANI YUKLASH (ASOSIY LOGIKA) ---
@st.cache_data
def yuklash():
    files = [f for f in os.listdir('.') if f.lower().endswith(('.xlsx', '.xls', '.docx')) and 'app.py' not in f]
    all_data = []
    word_text = ""
    for f in files:
        try:
            if f.endswith('.docx'):
                doc = docx.Document(f)
                word_text += "\n".join([para.text for para in doc.paragraphs])
            else:
                try: df_s = pd.read_excel(f, dtype=str)
                except: df_s = pd.read_html(f)[0]
                all_data.append(df_s)
        except: continue
    return (pd.concat(all_data, ignore_index=True) if all_data else None), word_text

# --- 4. LOGIN LOGIKASI ---
if "authenticated" not in st.session_state:
    set_login_bg()
    st.markdown(f'<div class="white-text school-title">🏛 {MAKTAB_NOMI}</div>', unsafe_allow_html=True)
    st.markdown('<div class="login-title">Tizimga kirish</div>', unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        parol = st.text_input("", placeholder="Parolni kiriting...", type="password", label_visibility="collapsed")
        if st.button("Kirish 🚀", use_container_width=True):
            if parol == TO_GRI_PAROL: st.session_state.authenticated = True; st.rerun()
            else: st.error("Xato!")
    st.stop()

# --- 5. ICHKI PANAL ---
apply_internal_design()
df_baza, word_baza = yuklash()

with st.sidebar:
    st.markdown(f'<div style="background-color: #1e293b; padding: 15px; border-radius: 15px; text-align: center; margin-bottom: 20px;"><h3 style="color: white; margin: 0; font-size: 16px;">🏛 {MAKTAB_NOMI}</h3></div>', unsafe_allow_html=True)
    st.markdown(f'<div class="sidebar-user-card"><p style="margin: 0; font-size: 12px; color: #64748b;">👤 Direktor:</p><p style="margin: 0; font-weight: bold; color: #1e293b;">{DIREKTOR_FIO}</p></div>', unsafe_allow_html=True)
    menu = st.radio("", ["🤖 AI Assistant", "📊 Monitoring"], label_visibility="collapsed")
    st.write("<br>" * 8, unsafe_allow_html=True)
    if st.button("Chiqish 🚪"):
        del st.session_state.authenticated
        st.rerun()

st.markdown('<div class="main-content-card">', unsafe_allow_html=True)

if menu == "🤖 AI Assistant":
    st.markdown(f'<div class="ai-header-box"><span style="font-size: 30px;">🤖</span><div><h2 style="margin: 0; color: #1e293b; font-size: 22px;">Sun\'iy Intellekt Yordamchisi</h2><p style="margin: 0; color: #64748b; font-size: 13px;">Baza ma\'lumotlari asosida savollarga javob beradi</p></div></div>', unsafe_allow_html=True)
    
    if "messages" not in st.session_state:
        st.session_state.messages = [{"role": "assistant", "content": "Assalomu alaykum! Xizmatingizdaman."}]
    
    for m in st.session_state.messages:
        with st.chat_message(m["role"]): st.markdown(m["content"])
        
    if savol := st.chat_input("Savolingizni yozing..."):
        st.session_state.messages.append({"role": "user", "content": savol})
        with st.chat_message("user"): st.markdown(savol)
        with st.chat_message("assistant"):
            with st.spinner("Tahlil qilinmoqda..."):
                found_data = df_baza.head(20).to_string() if df_baza is not None else "Baza bo'sh"
                payload = {"model": "llama-3.3-70b-versatile", "messages": [{"role": "system", "content": f"Sen {MAKTAB_NOMI} AI yordamchisisan. Ma'lumotlar: {found_data} {word_baza[:1000]}"}, {"role": "user", "content": savol}]}
                try:
                    r = requests.post("https://api.groq.com/openai/v1/chat/completions", json=payload, headers={"Authorization": f"Bearer {GRO_API_KEY}"})
                    ai_text = r.json()['choices'][0]['message']['content']
                except: ai_text = "Xatolik yuz berdi."
                st.markdown(ai_text)
                st.session_state.messages.append({"role": "assistant", "content": ai_text})

elif menu == "📊 Monitoring":
    st.markdown('<div class="ai-header-box"><span style="font-size: 30px;">📊</span><h2 style="margin: 0; color: #1e293b;">Jurnal Monitoringi</h2></div>', unsafe_allow_html=True)
    # Monitoring kodi (O'zgarishsiz qoldi)
    j_fayl = st.file_uploader("eMaktab faylini yuklang", type=['xlsx', 'xls'])
    if j_fayl:
        st.success("Fayl yuklandi!")
        # Monitoring tahlil qismi shu yerda davom etadi...

st.markdown('</div>', unsafe_allow_html=True)
