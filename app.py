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

# --- 2. DIZAYN SOZLAMALARI ---
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
        
        .school-title {{
            color: white;
            font-size: 45px;
            font-weight: bold;
            text-align: center;
            text-shadow: 3px 3px 15px rgba(0,0,0,0.9);
            margin-top: 50px;
            margin-bottom: 20px;
            width: 100%;
        }}

        .login-box {{
            background-color: rgba(255, 255, 255, 0.95);
            padding: 40px;
            border-radius: 25px;
            box-shadow: 0 15px 35px rgba(0,0,0,0.5);
            max-width: 450px;
            margin: auto;
            text-align: center;
        }}
        
        /* Input ramkasini chiroyli qilish */
        div[data-baseweb="input"] {{
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
        "https://images.unsplash.com/photo-1524178232363-1fb2b075b655?q=80&w=1600",
        "https://images.unsplash.com/photo-1516321318423-f06f85e504b3?q=80&w=1600",
        "https://images.unsplash.com/photo-1485827404703-89b55fcc595e?q=80&w=1600"
    ]
    
    if "bg_url" not in st.session_state:
        st.session_state.bg_url = random.choice(login_rasmlar)
    
    set_bg(st.session_state.bg_url)

    # 1. Maktab nomi (Tepada, ochiq holda)
    st.markdown(f'<div class="school-title">🏛 {MAKTAB_NOMI}</div>', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 1.2, 1])
    with col2:
        # Oq blok boshlanishi
        st.markdown('<div class="login-box">', unsafe_allow_html=True)
        
        # 2. Sarlavha (Blok ichida)
        st.markdown("<h2 style='color: #1E1E1E; margin-bottom: 20px; font-family: sans-serif;'>Tizimga kirish</h2>", unsafe_allow_html=True)
        
        # 3. Parol kiritish (Blok ichida)
        parol = st.text_input("", placeholder="Parolni kiriting...", type="password", key="login_pass")
        
        st.write("<br>", unsafe_allow_html=True)
        
        # 4. Tugma (Blok ichida)
        if st.button("Kirish 🚀", use_container_width=True):
            if parol == TO_GRI_PAROL:
                st.session_state.authenticated = True
                st.rerun()
            else:
                st.error("❌ Parol noto'g'ri!")
        
        st.markdown('</div>', unsafe_allow_html=True) # Oq blok tugashi
    st.stop()

# Fonni tozalash (Kirgandan keyin)
st.markdown("<style>.stApp {background: none !important;}</style>", unsafe_allow_html=True)

# --- 4. SIDEBAR ---
with st.sidebar:
    st.markdown(f"### 🏛 {MAKTAB_NOMI}")
    st.divider()
    menu = st.radio("Bo'limni tanlang:", ["🤖 AI Yordamchi", "📊 Jurnal Monitoringi"])
    st.info(f"👤 **Direktor:**\n{DIREKTOR_FIO}")

# --- 5. BAZA YUKLASH ---
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

# --- 6. SAHIFALAR ---
if menu == "🤖 AI Yordamchi":
    st.title("🤖 AI Yordamchi")
    if "messages" not in st.session_state:
        st.session_state.messages = [{"role": "assistant", "content": "Assalomu alaykum! Xizmatingizdaman."}]
    for m in st.session_state.messages:
        with st.chat_message(m["role"]): st.markdown(m["content"])
    if savol := st.chat_input("Savol yozing..."):
        st.session_state.messages.append({"role": "user", "content": savol})
        with st.chat_message("user"): st.markdown(savol)
        with st.chat_message("assistant"):
            found_data = df_baza.head(15).to_string() if df_baza is not None else "Baza bo'sh"
            payload = {"model": "llama-3.3-70b-versatile", "messages": [{"role": "system", "content": f"Sen {MAKTAB_NOMI} AI yordamchisisan."}, {"role": "user", "content": f"Baza: {found_data}. Savol: {savol}"}]}
            try:
                r = requests.post("https://api.groq.com/openai/v1/chat/completions", json=payload, headers={"Authorization": f"Bearer {GROQ_API_KEY}"})
                ai_text = r.json()['choices'][0]['message']['content']
            except: ai_text = "Xatolik yuz berdi."
            st.markdown(ai_text)
            st.session_state.messages.append({"role": "assistant", "content": ai_text})

elif menu == "📊 Jurnal Monitoringi":
    st.title("📊 Jurnal Monitoringi")
    if "m_auth" not in st.session_state: st.session_state.m_auth = False
    if not st.session_state.m_auth:
        m_pass = st.text_input("Monitoring kodi:", type="password")
        if st.button("Kirish"):
            if m_pass == MONITORING_KODI:
                st.session_state.m_auth = True
                st.rerun()
            else: st.error("❌ Xato!")
        st.stop()
    j_fayl = st.file_uploader("eMaktab faylini yuklang", type=['xlsx', 'xls'])
    if j_fayl:
        try:
            try: df_j = pd.read_excel(j_fayl, header=[0, 1])
            except: j_fayl.seek(0); df_j = pd.read_html(j_fayl, header=0)[0]
            df_j.columns = [' '.join([str(i) for i in col]).strip() if isinstance(col, tuple) else str(col) for col in df_j.columns]
            df_j.columns = [re.sub(r'Unnamed: \d+_level_\d+', '', c).strip() for c in df_j.columns]
            st.dataframe(df_j.head())
            c_oqit = st.selectbox("O'qituvchi ustuni:", df_j.columns)
            c_baho = st.selectbox("Baho ustuni:", df_j.columns)
            if st.button("📢 Yuborish"):
                def tahlil(val):
                    s = str(val).lower()
                    if "undan" in s:
                        nums = re.findall(r'\d+', s)
                        if len(nums) >= 2: return int(nums[1]) < int(nums[0])
                    return False
                df_filtir = df_j[df_j[c_oqit].notna() & ~df_j[c_oqit].str.contains('maktab|tuman', case=False, na=False)]
                xatolar = df_filtir[df_filtir[c_baho].apply(tahlil)]
                if not xatolar.empty:
                    text = f"<b>⚠️ JURNAL MONITORINGI</b>\n\n"
                    for _, r in xatolar.iterrows(): text += f"❌ <b>{r[c_oqit]}</b> -> {r[c_baho]}\n"
                else: text = "<b>✅ Hammasi joyida!</b>"
                requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", json={"chat_id": GURUH_ID, "text": text, "parse_mode": "HTML"})
                st.success("Yuborildi!")
        except Exception as e: st.error(f"Xato: {e}")
