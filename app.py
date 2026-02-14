import streamlit as st
import pandas as pd
import os
import requests
import re
import docx
import random

# --- SOZLAMALAR ---
MAKTAB_NOMI = "1-sonli umumta'lim maktabi"
DIREKTOR_FIO = "Mahmudov Matyoqub Narzulloyevich"
GROQ_API_KEY = "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"
TO_GRI_PAROL = "informatika2024"
MONITORING_KODI = "admin777" 
BOT_TOKEN = "8524007504:AAFiMXSbXhe2M-84WlNM16wNpzhNolfQIf8"
GURUH_ID = "-5045481739" 

st.set_page_config(page_title=MAKTAB_NOMI, layout="wide")

# --- SIDEBAR ---
with st.sidebar:
    st.markdown(f"## 🏛 {MAKTAB_NOMI}")
    st.divider()
    menu = st.radio("Bo'limni tanlang:", ["🤖 AI Yordamchi", "📊 Jurnal Monitoringi"])
    st.info(f"**Direktor:**\n{DIREKTOR_FIO}")

# --- XAVFSIZLIK ---
if "authenticated" not in st.session_state:
    st.title(f"🏫 {MAKTAB_NOMI} | Tizim")
    parol = st.text_input("Parolni kiriting:", type="password")
    if st.button("Kirish"):
        if parol == TO_GRI_PAROL:
            st.session_state.authenticated = True
            st.rerun()
        else: st.error("❌ Xato!")
    st.stop()

# --- BAZA YUKLASH ---
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
                # BU JOYI MUHIM: Har qanday formatni o'qishga urinadi
                try:
                    df_s = pd.read_excel(f, dtype=str)
                except:
                    df_s = pd.read_html(f)[0]
                all_data.append(df_s)
        except: continue
    return (pd.concat(all_data, ignore_index=True) if all_data else None), word_text

df_baza, maktab_doc_content = yuklash()

# --- SAHIFALAR ---
if menu == "🤖 AI Yordamchi":
    st.title("🤖 AI Yordamchi")
    if "messages" not in st.session_state:
        st.session_state.messages = [{"role": "assistant", "content": "Assalomu alaykum! Hurmatli foydalanuvchi, xizmatingizdaman."}]

    for m in st.session_state.messages:
        with st.chat_message(m["role"]): st.markdown(m["content"])

    if savol := st.chat_input("Savol yozing..."):
        st.session_state.messages.append({"role": "user", "content": savol})
        with st.chat_message("user"): st.markdown(savol)
        
        with st.chat_message("assistant"):
            found_data = df_baza.head(20).to_string() if df_baza is not None else "Baza bo'sh"
            payload = {
                "model": "llama-3.3-70b-versatile",
                "messages": [
                    {"role": "system", "content": f"Sen {MAKTAB_NOMI} AI yordamchisisan. Suhbatdoshingga 'Hurmatli foydalanuvchi' deb murojaat qil."},
                    {"role": "user", "content": f"Baza: {found_data}. Savol: {savol}"}
                ]
            }
            try:
                r = requests.post("https://api.groq.com/openai/v1/chat/completions", json=payload, headers={"Authorization": f"Bearer {GROQ_API_KEY}"})
                ai_text = r.json()['choices'][0]['message']['content']
            except: ai_text = "Hurmatli foydalanuvchi, tizimda uzilish bo'ldi."
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

    j_fayl = st.file_uploader("Excel faylni yuklang", type=['xlsx', 'xls'])
    if j_fayl:
        try:
            # HTML yoki haqiqiy Excel ekanini aniqlab o'qish
            try:
                df_j = pd.read_excel(j_fayl)
            except:
                j_fayl.seek(0)
                df_j = pd.read_html(j_fayl)[0]
            
            # Sarlavhalardagi bo'shliqlarni tozalash
            df_j.columns = [str(c).strip() for c in df_j.columns]
            st.dataframe(df_j.head())
            
            c_oqit = st.selectbox("O'qituvchi ustunini tanlang:", df_j.columns)
            c_baho = st.selectbox("Baho ustunini tanlang (X Undan Y):", df_j.columns)
            
            if st.button("📢 Telegramga yuborish"):
                def tekshir(val):
                    s = str(val).lower()
                    if "undan" in s:
                        try:
                            # Raqamlarni ajratib olish (masalan "83 Undan 81")
                            nums = re.findall(r'\d+', s)
                            if len(nums) >= 2:
                                return int(nums[1]) < int(nums[0])
                        except: return False
                    return False

                xatolar = df_j[df_j[c_baho].apply(tekshir)]
                
                if not xatolar.empty:
                    text = f"<b>⚠️ JURNAL MONITORINGI</b>\n<i>{MAKTAB_NOMI}</i>\n\nKamchiliklar aniqlandi:\n"
                    for _, r in xatolar.iterrows():
                        text += f"❌ {r[c_oqit]} -> {r[c_baho]}\n"
                else:
                    text = f"<b>✅ JURNAL MONITORINGI</b>\n<i>{MAKTAB_NOMI}</i>\n\n✨ <b>Jurnallar 100 foiz baholangan!</b>"

                requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", 
                              json={"chat_id": GURUH_ID, "text": text, "parse_mode": "HTML"})
                st.success("Hisobot yuborildi!")
        except Exception as e:
            st.error(f"Faylni o'qishda kutilmagan xato: {e}")
