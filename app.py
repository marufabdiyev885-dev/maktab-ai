import streamlit as st
import pandas as pd
import os
import requests
import re
import io
import docx  # Word fayllari uchun
import random

# --- 1. ASOSIY SOZLAMALAR ---
MAKTAB_NOMI = "1-sonli umumta'lim maktabi"
DIREKTOR_FIO = "Mahmudov Matyoqub Narzulloyevich"
GROQ_API_KEY = "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"
TO_GRI_PAROL = "informatika2024"
BOT_TOKEN = "8524007504:AAFiMXSbXhe2M-84WlNM16wNpzhNolfQIf8"
GURUH_ID = "-5045481739" # O'zingizning guruh ID-ni shu yerga yozing

st.set_page_config(page_title=MAKTAB_NOMI, layout="wide")

# --- 2. RAHBARIYAT VA MOTIVATSIYA PANELI (SIDEBAR) ---
with st.sidebar:
    st.markdown(f"## 🏛 {MAKTAB_NOMI}")
    st.image("https://cdn-icons-png.flaticon.com/512/2859/2859706.png", width=80)
    
    st.divider()
    
    # SAHIFA TANLASH
    menu = st.radio("Bo'limni tanlang:", ["🤖 AI Yordamchi", "📊 Jurnal Monitoringi"])

    st.divider()
    hikmatlar = ["Ilm — saodat kalitidir.", "Ta’lim — kuchli qurol.", "Informatika — kelajak tili!"]
    st.warning(f"🌟 **Kun hikmati:**\n\n*{random.choice(hikmatlar)}*")

    st.divider()
    st.info(f"**Direktor:**\n\n{DIREKTOR_FIO}")
    st.caption("© Maktab AI Tizimi")

# --- 3. XAVFSIZLIK ---
if "authenticated" not in st.session_state:
    st.title(f"🏫 {MAKTAB_NOMI} | Tizim")
    parol = st.text_input("Parolni kiriting:", type="password")
    if st.button("Kirish"):
        if parol == TO_GRI_PAROL:
            st.session_state.authenticated = True
            st.rerun()
        else: st.error("❌ Parol xato!")
    st.stop()

# --- 4. BAZANI YUKLASH (Kechagi doimiy fayllar uchun) ---
@st.cache_data
def yuklash():
    files = [f for f in os.listdir('.') if f.lower().endswith(('.xlsx', '.csv', '.docx')) and 'app.py' not in f]
    all_data = []
    word_text = ""
    for f in files:
        try:
            if f.endswith('.docx'):
                doc = docx.Document(f)
                word_text += "\n".join([para.text for para in doc.paragraphs])
            else:
                df_s = pd.read_excel(f, dtype=str) if f.endswith('.xlsx') else pd.read_csv(f, dtype=str)
                df_s.columns = [str(c).strip().lower() for c in df_s.columns]
                all_data.append(df_s)
        except: continue
    return (pd.concat(all_data, ignore_index=True) if all_data else None), word_text

df_baza, maktab_doc_content = yuklash()

# --- 5. SAHIFALAR LOGIKASI ---

# --- A) AI YORDAMCHI SAHIFASI ---
if menu == "🤖 AI Yordamchi":
    st.title(f"🤖 {MAKTAB_NOMI} AI Yordamchisi")

    if "messages" not in st.session_state:
        st.session_state.messages = [{"role": "assistant", "content": "Assalomu alaykum, Ma'rufjon aka! Maktabimizning bilimlar xazinasiga xush kelibsiz. Qanday yordam bera olaman?"}]

    for m in st.session_state.messages:
        with st.chat_message(m["role"]): st.markdown(m["content"])

    if savol := st.chat_input("Savolingizni yozing..."):
        st.session_state.messages.append({"role": "user", "content": savol})
        with st.chat_message("user"): st.markdown(savol)
        
        with st.chat_message("assistant"):
            found_data = ""
            soni = 0
            
            # Farosat filtri
            shunchaki_gap = [r"rahmat", r"ajoyib", r"yaxshi", r"zo'r", r"salom", r"assalomu alaykum", r"baraka toping"]
            is_greeting = any(re.search(rf"\b{soz}\b", savol.lower()) for soz in shunchaki_gap)

            if df_baza is not None and not is_greeting:
                keywords = [s.lower() for s in savol.split() if len(s) > 2]
                if keywords:
                    res = df_baza[df_baza.apply(lambda row: any(k in str(v).lower() for k in keywords for v in row), axis=1)]
                    if not res.empty:
                        st.dataframe(res, use_container_width=True)
                        soni = len(res) 
                        found_data = res.head(20).to_string(index=False)

            # AI JAVOBI (Farosat va xushomad bilan)
            system_talimoti = f"""
            Sen {MAKTAB_NOMI} maktabining eng farosatli va odobli yordamchisisan. 
            Suhbatdoshing - Ma'rufjon aka (Informatika ustozi). 
            Doimo 'Ma'rufjon aka' yoki 'Ustoz' deb ehtirom bilan gapir. 
            Agar ma'lumot topsang (soni={soni}), uni xushmuomalalik bilan tushuntir.
            """
            
            payload = {
                "model": "llama-3.3-70b-versatile",
                "messages": [
                    {"role": "system", "content": system_talimoti},
                    {"role": "user", "content": f"Baza: {found_data}. Savol: {savol}"}
                ],
                "temperature": 0.7 
            }
            
            try:
                r = requests.post("https://api.groq.com/openai/v1/chat/completions", json=payload, headers={"Authorization": f"Bearer {GROQ_API_KEY}"}, timeout=15)
                ai_text = r.json()['choices'][0]['message']['content']
            except: ai_text = "Sizga xizmat qilish - men uchun sharaf, Ma'rufjon aka!"

            st.markdown(ai_text)
            st.session_state.messages.append({"role": "assistant", "content": ai_text})

# --- B) JURNAL MONITORINGI SAHIFASI ---
elif menu == "📊 Jurnal Monitoringi":
    st.title("📊 Kunlik Jurnal Nazorati")
    st.write("eMaktab statistikasini yuklang va o'qituvchilarni ogohlantiring.")

    jurnal_fayl = st.file_uploader("Excel faylni yuklang", type=['xlsx'], key="monitoring")
    
    if jurnal_fayl:
        df_j = pd.read_excel(jurnal_fayl)
        st.dataframe(df_j.head())
        
        # Ustunlarni tanlash
        c1, c2 = st.columns(2)
        with c1: oqit_c = st.selectbox("O'qituvchi ustuni:", df_j.columns)
        with c2: stat_c = st.selectbox("Holat ustuni:", df_j.columns)
        
        qidiruv = st.text_input("Qidiriladigan so'z:", "To'ldirilmagan")
        
        xatolar = df_j[df_j[stat_c].astype(str).str.contains(qidiruv, na=False)]
        
        if not xatolar.empty:
            st.warning(f"Aniqlangan kamchiliklar: {len(xatolar)}")
            if st.button("📢 Telegramga hisobot yuborish"):
                xabar = "<b>🔔 JURNAL MONITORINGI</b>\n\n"
                for i, row in xatolar.head(25).iterrows():
                    xabar += f"❌ {row[oqit_c]}\n"
                xabar += "\n<i>Iltimos, darslarni eMaktabga kiriting!</i>"
                
                res = requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", json={"chat_id": GURUH_ID, "text": xabar, "parse_mode": "HTML"})
                if res.status_code == 200: st.success("Xabar guruhga yuborildi!")
                else: st.error("Xatolik yuz berdi!")
        else:
            st.success("Hamma jurnallar to'liq! Baran-baraka, Ustoz!")

