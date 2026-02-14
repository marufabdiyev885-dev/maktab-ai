import streamlit as st
import pandas as pd
import os
import requests
import re
import io
import docx
import random

# --- 1. ASOSIY SOZLAMALAR ---
MAKTAB_NOMI = "1-sonli umumta'lim maktabi"
DIREKTOR_FIO = "Mahmudov Matyoqub Narzulloyevich"
GROQ_API_KEY = "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"
TO_GRI_PAROL = "informatika2024"
MONITORING_KODI = "admin777" 
BOT_TOKEN = "8524007504:AAFiMXSbXhe2M-84WlNM16wNpzhNolfQIf8"
GURUH_ID = "-5045481739" 

st.set_page_config(page_title=MAKTAB_NOMI, layout="wide")

# --- 2. BAZANI YUKLASH (XATOLIKLAR TUZATILGAN) ---
@st.cache_data
def yuklash():
    files = [f for f in os.listdir('.') if f.lower().endswith(('.xlsx', '.xls', '.csv', '.docx')) and 'app.py' not in f]
    all_data = []
    word_text = ""
    for f in files:
        try:
            if f.endswith('.docx'):
                doc = docx.Document(f)
                word_text += "\n".join([para.text for para in doc.paragraphs])
            elif f.endswith(('.xlsx', '.xls')):
                try:
                    # Oddiy Excel sifatida o'qish
                    excel_sheets = pd.read_excel(f, sheet_name=None, dtype=str)
                    for name, sheet_df in excel_sheets.items():
                        if not sheet_df.empty: all_data.append(sheet_df)
                except:
                    # AGAR XATO BERASA: HTML formatidagi Excel deb o'qish (eMaktab uchun)
                    try:
                        df_list = pd.read_html(f)
                        if df_list: all_data.append(df_list[0].astype(str))
                    except: continue
            elif f.endswith('.csv'):
                df_s = pd.read_csv(f, dtype=str)
                if not df_s.empty: all_data.append(df_s)
        except: continue
    
    if all_data:
        full_df = pd.concat(all_data, ignore_index=True)
        full_df.columns = [str(c).strip().lower() for c in full_df.columns]
        cols = pd.Series(full_df.columns)
        for i, col in enumerate(cols):
            count = cols[:i].tolist().count(col)
            if count > 0: cols[i] = f"{col}.{count}"
        full_df.columns = cols
        full_df = full_df.applymap(lambda x: str(x).strip() if pd.notnull(x) else "")
        return full_df, word_text
    return None, word_text

df_baza, maktab_doc_content = yuklash()

# --- 3. SIDEBAR ---
with st.sidebar:
    st.title(f"🏛 {MAKTAB_NOMI}")
    menu = st.radio("Menyu:", ["🤖 AI Yordamchi", "📊 Jurnal Monitoringi"])

# --- 4. XAVFSIZLIK ---
if "authenticated" not in st.session_state:
    st.title(f"🏫 {MAKTAB_NOMI}")
    parol = st.text_input("Parol:", type="password")
    if st.button("Kirish"):
        if parol == TO_GRI_PAROL:
            st.session_state.authenticated = True
            st.rerun()
        else: st.error("Xato!")
    st.stop()

# --- 5. AI YORDAMCHI ---
if menu == "🤖 AI Yordamchi":
    st.title("🤖 Maktab AI")
    if "messages" not in st.session_state:
        st.session_state.messages = [{"role": "assistant", "content": "Assalomu alaykum! Maktab bazasi bo'yicha savollaringizga javob beraman."}]

    for m in st.session_state.messages:
        with st.chat_message(m["role"]): st.markdown(m["content"])

    if savol := st.chat_input("Savol yozing..."):
        st.session_state.messages.append({"role": "user", "content": savol})
        with st.chat_message("user"): st.markdown(savol)
        
        with st.chat_message("assistant"):
            found_data = ""
            salomlar = ["salom", "assalom", "qalay", "yaxshimi"]
            is_greeting = any(s in savol.lower() for s in salomlar)

            if df_baza is not None and not is_greeting:
                q_words = [s.lower() for s in savol.split() if len(s) > 2]
                if q_words:
                    res = df_baza[df_baza.apply(lambda row: any(k in str(v).lower() for k in q_words for v in row), axis=1)]
                    if not res.empty:
                        st.dataframe(res)
                        found_data = res.head(20).to_string(index=False)

            payload = {
                "model": "llama-3.3-70b-versatile",
                "messages": [
                    {"role": "system", "content": f"Sen {MAKTAB_NOMI} AI yordamchisisan. Faqat bazadan gapir, ism to'qima!"},
                    {"role": "user", "content": f"Baza: {found_data}\n\nSavol: {savol}"}
                ], "temperature": 0.2
            }
            try:
                r = requests.post("https://api.groq.com/openai/v1/chat/completions", 
                                 json=payload, headers={"Authorization": f"Bearer {GROQ_API_KEY}"})
                ai_text = r.json()['choices'][0]['message']['content']
            except: ai_text = "Natijalarni jadvalda ko'rishingiz mumkin."
            
            st.markdown(ai_text)
            st.session_state.messages.append({"role": "assistant", "content": ai_text})

# --- 6. MONITORING VA TELEGRAM (XATOLIK TUZATILDI) ---
elif menu == "📊 Jurnal Monitoringi":
    st.title("📊 Telegram Monitoring")
    if "m_auth" not in st.session_state: st.session_state.m_auth = False
    if not st.session_state.m_auth:
        m_pass = st.text_input("Kod:", type="password")
        if st.button("Kirish"):
            if m_pass == MONITORING_KODI:
                st.session_state.m_auth = True
                st.rerun()
            else: st.error("Xato!")
        st.stop()

    j_fayl = st.file_uploader("eMaktab faylini yuklang", type=['xlsx', 'xls'])
    if j_fayl:
        try:
            # Monitoring faylini o'qishda xatolikni oldini olish
            try:
                df_j = pd.read_excel(j_fayl, header=[0, 1])
            except:
                j_fayl.seek(0)
                df_j = pd.read_html(j_fayl, header=0)[0]
            
            # Ustunlarni tekislash
            df_j.columns = [' '.join([str(i) for i in col]).strip() if isinstance(col, tuple) else str(col) for col in df_j.columns]
            st.write("✅ Jadval yuklandi!")
            st.dataframe(df_j.head())
            
            c_oqit = st.selectbox("O'qituvchi ustuni:", df_j.columns)
            c_baho = st.selectbox("Baho ustuni:", df_j.columns)
            
            if st.button("📢 Telegramga yuborish"):
                text = f"<b>📊 {MAKTAB_NOMI} Monitoringi</b>\nHisobot tayyor."
                requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", 
                             json={"chat_id": GURUH_ID, "text": text, "parse_mode": "HTML"})
                st.success("Telegramga yuborildi!")
        except Exception as e: st.error(f"Faylni o'qishda xato: {e}")
