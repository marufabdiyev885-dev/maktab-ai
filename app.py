import streamlit as st
import pandas as pd
import os
import requests
import re
import io
import docx

# --- 1. ASOSIY SOZLAMALAR ---
MAKTAB_NOMI = "1-sonli umumta'lim maktabi"
DIREKTOR_FIO = "Mahmudov Matyoqub Narzulloyevich"
GROQ_API_KEY = "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"
TO_GRI_PAROL = "informatika2024"
MONITORING_KODI = "admin777" 
BOT_TOKEN = "8524007504:AAFiMXSbXhe2M-84WlNM16wNpzhNolfQIf8"
GURUH_ID = "-5045481739" 

st.set_page_config(page_title=MAKTAB_NOMI, layout="wide")

# --- 2. BAZANI YUKLASH (HAMMA LISTLARNI O'QIYDI) ---
@st.cache_data
def yuklash():
    files = [f for f in os.listdir('.') if f.lower().endswith(('.xlsx', '.xls', '.csv')) and 'app.py' not in f]
    all_data = []
    for f in files:
        try:
            if f.endswith(('.xlsx', '.xls')):
                # sheet_name=None — hamma listlarni (List1, List2...) o'qiydi
                sheets = pd.read_excel(f, sheet_name=None, dtype=str)
                for sheet_name, df in sheets.items():
                    if not df.empty:
                        # Qaysi listdan olinganini belgilab qo'yamiz (ixtiyoriy)
                        df['manba_list'] = sheet_name 
                        all_data.append(df)
            elif f.endswith('.csv'):
                df_s = pd.read_csv(f, dtype=str)
                if not df_s.empty: all_data.append(df_s)
        except:
            # HTML formatidagi Excel bo'lsa (eMaktab xatosi uchun)
            try:
                df_html = pd.read_html(f)[0].astype(str)
                all_data.append(df_html)
            except: continue
    
    if all_data:
        full_df = pd.concat(all_data, ignore_index=True)
        full_df.columns = [str(c).strip().lower() for c in full_df.columns]
        # Duplikat ustunlarni tozalash
        cols = pd.Series(full_df.columns)
        for i, col in enumerate(cols):
            count = cols[:i].tolist().count(col)
            if count > 0: cols[i] = f"{col}.{count}"
        full_df.columns = cols
        full_df = full_df.applymap(lambda x: str(x).strip() if pd.notnull(x) else "")
        return full_df
    return None

df_baza = yuklash()

# --- 3. SIDEBAR ---
with st.sidebar:
    st.title(f"🏛 {MAKTAB_NOMI}")
    menu = st.radio("Menyu:", ["🤖 AI Yordamchi", "📊 Jurnal Monitoringi"])

# --- 4. XAVFSIZLIK ---
if "authenticated" not in st.session_state:
    st.title(f"🏫 {MAKTAB_NOMI} Tizimi")
    parol = st.text_input("Kirish paroli:", type="password")
    if st.button("Kirish"):
        if parol == TO_GRI_PAROL:
            st.session_state.authenticated = True
            st.rerun()
        else: st.error("Parol xato!")
    st.stop()

# --- 5. AI YORDAMCHI (LISTLARNI ARALASHTIRMAYDI) ---
if menu == "🤖 AI Yordamchi":
    st.title("🤖 Maktab AI")
    if "messages" not in st.session_state:
        st.session_state.messages = [{"role": "assistant", "content": "Assalomu alaykum! Hamma listlardagi ma'lumotlar yuklandi. Kimni qidiramiz?"}]

    for m in st.session_state.messages:
        with st.chat_message(m["role"]): st.markdown(m["content"])

    if savol := st.chat_input("Savol yozing..."):
        st.session_state.messages.append({"role": "user", "content": savol})
        with st.chat_message("user"): st.markdown(savol)
        
        with st.chat_message("assistant"):
            found_data = ""
            if df_baza is not None:
                keywords = [s.lower() for s in savol.split() if len(s) > 2]
                if keywords:
                    # Qidiruv barcha listlardan yig'ilgan bazada ketadi
                    res = df_baza[df_baza.apply(lambda row: any(k in str(v).lower() for k in keywords for v in row), axis=1)]
                    if not res.empty:
                        st.dataframe(res)
                        found_data = res.head(15).to_string(index=False)

            payload = {
                "model": "llama-3.3-70b-versatile",
                "messages": [
                    {"role": "system", "content": f"Sen {MAKTAB_NOMI} AI yordamchisisan. Faqat berilgan bazadan javob ber. Agar ma'lumot topilmasa, to'qima!"},
                    {"role": "user", "content": f"Baza: {found_data}\n\nSavol: {savol}"}
                ], "temperature": 0.1
            }
            try:
                r = requests.post("https://api.groq.com/openai/v1/chat/completions", 
                                 json=payload, headers={"Authorization": f"Bearer {GROQ_API_KEY}"})
                ai_text = r.json()['choices'][0]['message']['content']
            except: ai_text = "Natijalarni jadvalda ko'rishingiz mumkin."
            
            st.markdown(ai_text)
            st.session_state.messages.append({"role": "assistant", "content": ai_text})

# --- 6. MONITORING VA TELEGRAM (O'ZGARISHSIZ QOLDI) ---
elif menu == "📊 Jurnal Monitoringi":
    st.title("📊 Jurnal Monitoringi")
    if "m_auth" not in st.session_state: st.session_state.m_auth = False
    if not st.session_state.m_auth:
        m_pass = st.text_input("Monitoring kodi:", type="password")
        if st.button("Kirish"):
            if m_pass == MONITORING_KODI:
                st.session_state.m_auth = True
                st.rerun()
            else: st.error("Kod xato!")
        st.stop()

    j_fayl = st.file_uploader("eMaktab faylini tanlang", type=['xlsx', 'xls'])
    if j_fayl:
        try:
            try: df_j = pd.read_excel(j_fayl, header=[0, 1])
            except:
                j_fayl.seek(0)
                df_j = pd.read_html(j_fayl, header=0)[0]
            
            st.write("✅ Monitoring fayli yuklandi")
            st.dataframe(df_j.head())
            
            if st.button("📢 Telegramga hisobotni yuborish"):
                text = f"<b>📊 {MAKTAB_NOMI}</b>\nHisobot guruhingizga yuborilmoqda..."
                requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", 
                             json={"chat_id": GURUH_ID, "text": text, "parse_mode": "HTML"})
                st.success("Telegramga yuborildi!")
        except Exception as e: st.error(f"Xato: {e}")
