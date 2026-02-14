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

# --- 2. DIZAYN FUNKSIYASI ---
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
        header {{visibility: hidden;}}
        .main .block-container {{
            padding-top: 0rem;
        }}
        .white-text {{
            color: white;
            text-align: center;
            text-shadow: 2px 2px 10px rgba(0,0,0,1);
            font-family: sans-serif;
            width: 100%;
        }}
        .school-title {{
            font-size: 42px;
            font-weight: bold;
            padding-top: 80px;
        }}
        .login-title {{
            font-size: 28px;
            margin-top: 20px;
        }}
        div[data-baseweb="input"] {{
            background-color: rgba(255, 255, 255, 0.9) !important;
            border-radius: 12px !important;
        }}
        </style>
        """,
        unsafe_allow_html=True
    )

# --- 3. XAVFSIZLIK (LOGIN EKRANI) ---
if "authenticated" not in st.session_state:
    bg_url = "https://images.unsplash.com/photo-1509062522246-3755977927d7?q=80&w=1600"
    set_bg(bg_url)

    st.markdown(f'<div class="white-text school-title">🏛 {MAKTAB_NOMI}</div>', unsafe_allow_html=True)
    st.markdown('<div class="white-text login-title">Tizimga kirish</div>', unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        parol = st.text_input("", placeholder="Parolni kiriting...", type="password", key="login_pass", label_visibility="collapsed")
        if st.button("Kirish 🚀", use_container_width=True):
            if parol == TO_GRI_PAROL:
                st.session_state.authenticated = True
                st.rerun()
            else:
                st.error("❌ Parol noto'g'ri!")
    st.stop()

# --- 4. TIZIMGA KIRGANDAN KEYINGI QISM ---
# Fonni tozalaymiz
st.markdown("<style>.stApp {background: none !important;} header {visibility: visible;}</style>", unsafe_allow_html=True)

# Sidebar menyusi
with st.sidebar:
    st.markdown(f"### 🏛 {MAKTAB_NOMI}")
    st.divider()
    menu = st.radio("Bo'limni tanlang:", ["🤖 AI Yordamchi", "📊 Jurnal Monitoringi"])
    st.info(f"👤 **Direktor:**\n{DIREKTOR_FIO}")

# Baza yuklash funksiyasi
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

df_baza, _ = yuklash()

# --- 5. SAHIFALAR ---

# 1-SAHIFA: AI YORDAMCHI
if menu == "🤖 AI Yordamchi":
    st.title("🤖 AI Yordamchi")
    if "messages" not in st.session_state:
        st.session_state.messages = [{"role": "assistant", "content": "Assalomu alaykum! Maktab ma'lumotlari bo'yicha savol berishingiz mumkin."}]
    
    for m in st.session_state.messages:
        with st.chat_message(m["role"]): st.markdown(m["content"])
    
    if savol := st.chat_input("Savol yozing..."):
        st.session_state.messages.append({"role": "user", "content": savol})
        with st.chat_message("user"): st.markdown(savol)
        
        with st.chat_message("assistant"):
            found_data = df_baza.head(15).to_string() if df_baza is not None else "Baza bo'sh"
            payload = {
                "model": "llama-3.3-70b-versatile",
                "messages": [
                    {"role": "system", "content": f"Sen {MAKTAB_NOMI} AI yordamchisisan."},
                    {"role": "user", "content": f"Baza: {found_data}. Savol: {savol}"}
                ]
            }
            try:
                r = requests.post("https://api.groq.com/openai/v1/chat/completions", json=payload, headers={"Authorization": f"Bearer {GROQ_API_KEY}"})
                ai_text = r.json()['choices'][0]['message']['content']
            except: ai_text = "Tizimda yuklanish ko'p, keyinroq urinib ko'ring."
            st.markdown(ai_text)
            st.session_state.messages.append({"role": "assistant", "content": ai_text})

# 2-SAHIFA: MONITORING
elif menu == "📊 Jurnal Monitoringi":
    st.title("📊 Jurnal Monitoringi")
    
    if "m_auth" not in st.session_state: st.session_state.m_auth = False
    
    if not st.session_state.m_auth:
        m_pass = st.text_input("Monitoring uchun maxsus kodni kiriting:", type="password")
        if st.button("Kirish"):
            if m_pass == MONITORING_KODI:
                st.session_state.m_auth = True
                st.rerun()
            else: st.error("❌ Monitoring kodi noto'g'ri!")
        st.stop()

    j_fayl = st.file_uploader("eMaktabdan olingan Excel faylni yuklang", type=['xlsx', 'xls'])
    if j_fayl:
        try:
            df_j = pd.read_excel(j_fayl)
            st.success("Fayl yuklandi!")
            st.dataframe(df_j.head())
            
            c_oqit = st.selectbox("O'qituvchi ism-familiyasi ustunini tanlang:", df_j.columns)
            c_baho = st.selectbox("Baho/Monitoring ustunini tanlang:", df_j.columns)
            
            if st.button("📢 Natijani Telegramga yuborish"):
                # Bu yerda tahlil kodi...
                text = f"<b>📊 {MAKTAB_NOMI} Monitoringi</b>\n\nFayl muvaffaqiyatli tahlil qilindi."
                requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", 
                              json={"chat_id": GURUH_ID, "text": text, "parse_mode": "HTML"})
                st.success("Ma'lumotlar guruhga yuborildi!")
        except Exception as e:
            st.error(f"Faylni o'qishda xatolik: {e}")
