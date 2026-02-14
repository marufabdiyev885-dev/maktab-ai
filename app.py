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
MONITORING_KODI = "admin777" # Jurnal bo'limi uchun kod
BOT_TOKEN = "8524007504:AAFiMXSbXhe2M-84WlNM16wNpzhNolfQIf8"
GURUH_ID = "-5045481739" # Siz topgan probniy guruh ID

st.set_page_config(page_title=MAKTAB_NOMI, layout="wide")

# --- 2. RAHBARIYAT VA SIDEBAR ---
with st.sidebar:
    st.markdown(f"## 🏛 {MAKTAB_NOMI}")
    st.image("https://cdn-icons-png.flaticon.com/512/2859/2859706.png", width=80)
    st.divider()
    
    menu = st.radio("Bo'limni tanlang:", ["🤖 AI Yordamchi", "📊 Jurnal Monitoringi"])
    st.divider()
    
    hikmatlar = ["Ilm — saodat kalitidir.", "Informatika — kelajak tili!", "Ustoz — otangdek ulug‘!"]
    st.warning(f"🌟 **Kun hikmati:**\n\n*{random.choice(hikmatlar)}*")
    st.info(f"**Direktor:**\n{DIREKTOR_FIO}")

# --- 3. UMUMIY TIZIMGA KIRISH ---
if "authenticated" not in st.session_state:
    st.title(f"🏫 {MAKTAB_NOMI} | Tizim")
    parol = st.text_input("Asosiy parolni kiriting:", type="password")
    if st.button("Kirish"):
        if parol == TO_GRI_PAROL:
            st.session_state.authenticated = True
            st.rerun()
        else: st.error("❌ Xato!")
    st.stop()

# --- 4. BAZANI YUKLASH FUNKSIYASI ---
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

# --- 5. SAHIFALAR ---

# A) AI YORDAMCHI
if menu == "🤖 AI Yordamchi":
    st.title(f"🤖 {MAKTAB_NOMI} AI Yordamchisi")
    if "messages" not in st.session_state:
        st.session_state.messages = [{"role": "assistant", "content": "Assalomu alaykum, Ma'rufjon aka! Maktabimiz bazasi bo'yicha xizmatingizdaman."}]

    for m in st.session_state.messages:
        with st.chat_message(m["role"]): st.markdown(m["content"])

    if savol := st.chat_input("Savolingizni yozing..."):
        st.session_state.messages.append({"role": "user", "content": savol})
        with st.chat_message("user"): st.markdown(savol)
        
        with st.chat_message("assistant"):
            found_data = ""
            soni = 0
            if df_baza is not None:
                keywords = [s.lower() for s in savol.split() if len(s) > 2]
                if keywords:
                    res = df_baza[df_baza.apply(lambda row: any(k in str(v).lower() for k in keywords for v in row), axis=1)]
                    if not res.empty:
                        st.dataframe(res, use_container_width=True)
                        soni = len(res)
                        found_data = res.head(20).to_string(index=False)

            system_prompt = f"""Sen {MAKTAB_NOMI} maktabining farosatli AI yordamchisisan. 
            Suhbatdoshing Ma'rufjon aka (Ustoz). Doimo ehtirom bilan gapir. 
            Ma'lumot topilsa: {soni} ta topildi deb ayt."""
            
            payload = {
                "model": "llama-3.3-70b-versatile",
                "messages": [{"role": "system", "content": system_prompt}, {"role": "user", "content": f"Baza: {found_data}. Savol: {savol}"}]
            }
            try:
                r = requests.post("https://api.groq.com/openai/v1/chat/completions", json=payload, headers={"Authorization": f"Bearer {GROQ_API_KEY}"})
                ai_text = r.json()['choices'][0]['message']['content']
            except: ai_text = "Xizmatingizga tayyorman, Ustoz!"
            
            st.markdown(ai_text)
            st.session_state.messages.append({"role": "assistant", "content": ai_text})

# B) JURNAL MONITORINGI (MAXSUS KOD BILAN)
elif menu == "📊 Jurnal Monitoringi":
    st.title("📊 Jurnal Monitoringi Tizimi")
    
    if "monitoring_auth" not in st.session_state:
        st.session_state.monitoring_auth = False

    if not st.session_state.monitoring_auth:
        m_pass = st.text_input("Monitoring bo'limi kodini kiriting:", type="password")
        if st.button("Tasdiqlash"):
            if m_pass == MONITORING_KODI:
                st.session_state.monitoring_auth = True
                st.rerun()
            else: st.error("❌ Kod xato!")
        st.stop()

    # Agar kod to'g'ri bo'lsa:
    st.success("✅ Kirish tasdiqlandi. Jurnal faylini yuklashingiz mumkin.")
    j_fayl = st.file_uploader("Excelni yuklang", type=['xlsx'])
    if j_fayl:
        df_j = pd.read_excel(j_fayl)
        st.dataframe(df_j.head())
        col_oqit = st.selectbox("O'qituvchi ustuni:", df_j.columns)
        col_stat = st.selectbox("Holat ustuni:", df_j.columns)
        
        xatolar = df_j[df_j[col_stat].astype(str).str.contains("To'ldirilmagan", na=False)]
        
        if st.button("📢 Guruhga ogohlantirish yuborish"):
            text = f"<b>🔔 Jurnal monitoringi ({MAKTAB_NOMI})</b>\n\nKamchiliklar aniqlandi:\n"
            for name in xatolar[col_oqit].unique()[:20]:
                text += f"❌ {name}\n"
            text += "\n<i>Iltimos, darslarni o'z vaqtida to'ldiring!</i>"
            requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", json={"chat_id": GURUH_ID, "text": text, "parse_mode": "HTML"})
            st.success("Xabar guruhga yuborildi!")
