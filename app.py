import streamlit as st
import pandas as pd
import os
import requests
import random

# Docx kutubxonasi o'rnatilmagan bo'lsa xato bermasligi uchun
try:
    import docx
except ImportError:
    os.system('pip install python-docx')
    import docx

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
def apply_style():
    st.markdown("""
        <style>
        .stApp { background-color: #f4f7f9; }
        [data-testid="stSidebar"] { background-color: #ffffff; border-right: 1px solid #e6e9ef; }
        .main-card { background-color: #ffffff; border-radius: 20px; padding: 25px; box-shadow: 0 4px 15px rgba(0,0,0,0.05); }
        .ai-header { border: 1.5px solid #3b82f6; border-radius: 12px; padding: 15px; margin-bottom: 20px; background: white; }
        .stButton>button { border-radius: 25px; background: linear-gradient(90deg, #3b82f6, #2563eb); color: white; width: 100%; font-weight: bold; }
        .stRadio div[role="radiogroup"] > label { background-color: #1e293b !important; color: white !important; border-radius: 25px !important; padding: 8px 20px !important; margin-bottom: 5px !important; }
        </style>
    """, unsafe_allow_html=True)

# --- 3. BAZANI YUKLASH ---
@st.cache_data
def yuklash_baza():
    files = [f for f in os.listdir('.') if f.lower().endswith(('.xlsx', '.xls', '.docx')) and f != 'app.py']
    all_df = []
    text_data = ""
    for f in files:
        try:
            if f.endswith('.docx'):
                doc = docx.Document(f)
                text_data += "\n".join([p.text for p in doc.paragraphs])
            else:
                df = pd.read_excel(f, dtype=str)
                all_df.append(df)
        except: continue
    final_df = pd.concat(all_df, ignore_index=True) if all_df else None
    return final_df, text_data

# --- 4. LOGIN ---
if "authenticated" not in st.session_state:
    st.markdown(f"""<style>
        .stApp {{ background: linear-gradient(rgba(0,0,0,0.6), rgba(0,0,0,0.6)), url("https://images.unsplash.com/photo-1509062522246-3755977927d7?q=80&w=1600"); background-size: cover; }}
        .login-txt {{ color: white; text-align: center; text-shadow: 2px 2px 10px black; }}
        div[data-baseweb="input"] {{ background: white !important; border-radius: 10px !important; }}
    </style>""", unsafe_allow_html=True)
    st.markdown(f'<h1 class="login-txt">🏛 {MAKTAB_NOMI}</h1>', unsafe_allow_html=True)
    st.markdown('<h3 class="login-txt">Tizimga kirish</h3>', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        p = st.text_input("", type="password", placeholder="Parol...", label_visibility="collapsed")
        if st.button("Kirish 🚀"):
            if p == TO_GRI_PAROL:
                st.session_state.authenticated = True
                st.rerun()
            else: st.error("Parol xato!")
    st.stop()

# --- 5. ASOSIY PANEL ---
apply_style()
df_baza, txt_baza = yuklash_baza()

with st.sidebar:
    st.markdown(f"### 🏫 {MAKTAB_NOMI}")
    st.info(f"👤 **Direktor:**\n{DIREKTOR_FIO}")
    menu = st.radio("Bo'limlar:", ["🤖 AI Assistant", "📊 Monitoring"])
    if st.button("Chiqish 🚪"):
        del st.session_state.authenticated
        st.rerun()

st.markdown('<div class="main-card">', unsafe_allow_html=True)

if menu == "🤖 AI Assistant":
    st.markdown('<div class="ai-header"><h2>🤖 AI Yordamchi</h2><p>Maktab bazasi bilan ishlash</p></div>', unsafe_allow_html=True)
    
    if "messages" not in st.session_state:
        st.session_state.messages = [{"role": "assistant", "content": "Assalomu alaykum!"}]
    
    for m in st.session_state.messages:
        with st.chat_message(m["role"]): st.markdown(m["content"])
        
    if savol := st.chat_input("Savol yozing..."):
        st.session_state.messages.append({"role": "user", "content": savol})
        with st.chat_message("user"): st.markdown(savol)
        
        with st.chat_message("assistant"):
            # Bazani AI ga tayyorlash
            baza_str = df_baza.head(10).to_string() if df_baza is not None else "Baza topilmadi"
            payload = {
                "model": "llama-3.3-70b-versatile",
                "messages": [
                    {"role": "system", "content": f"Sen {MAKTAB_NOMI} yordamchisisan. Ma'lumot: {baza_str} {txt_baza[:500]}"},
                    {"role": "user", "content": savol}
                ]
            }
            try:
                r = requests.post("https://api.groq.com/openai/v1/chat/completions", 
                                 json=payload, 
                                 headers={"Authorization": f"Bearer {GROQ_API_KEY}"})
                res = r.json()['choices'][0]['message']['content']
            except: res = "Groq API ulanishda xato!"
            
            st.markdown(res)
            st.session_state.messages.append({"role": "assistant", "content": res})

elif menu == "📊 Monitoring":
    st.markdown('<div class="ai-header"><h2>📊 Monitoring</h2></div>', unsafe_allow_html=True)
    f = st.file_uploader("Excel fayl yuklang", type=['xlsx'])
    if f: st.success("Fayl yuklandi!")

st.markdown('</div>', unsafe_allow_html=True)
