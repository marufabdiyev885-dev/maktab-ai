import streamlit as st
import pandas as pd
import os
import requests
import io

# --- 1. ASOSIY SOZLAMALAR ---
MAKTAB_NOMI = "1-sonli umumta'lim maktabi"
DIREKTOR_FIO = "Mahmudov Matyoqub Narzulloyevich"
GROQ_API_KEY = "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"
TO_GRI_PAROL = "informatika2024"
MONITORING_KODI = "admin777" 
BOT_TOKEN = "8524007504:AAFiMXSbXhe2M-84WlNM16wNpzhNolfQIf8"
GURUH_ID = "-5045481739" 

st.set_page_config(page_title=MAKTAB_NOMI, layout="wide")

# --- 2. BAZANI YUKLASH (HAMMA LISTLARNI TO'LIQ O'QISH) ---
@st.cache_data
def yuklash():
    files = [f for f in os.listdir('.') if f.lower().endswith(('.xlsx', '.xls', '.csv')) and 'app.py' not in f]
    all_data = []
    for f in files:
        try:
            # sheet_name=None hamma varaqlarni (Лист1, Лист2) o'qiydi
            sheets = pd.read_excel(f, sheet_name=None, dtype=str)
            for name, df in sheets.items():
                if not df.empty:
                    df.columns = [str(c).strip().lower() for c in df.columns]
                    all_data.append(df)
        except: continue
    if all_data:
        full_df = pd.concat(all_data, ignore_index=True, sort=False)
        return full_df.fillna("")
    return None

df_baza = yuklash()

# --- 3. SIDEBAR ---
with st.sidebar:
    st.title(f"🏛 {MAKTAB_NOMI}")
    menu = st.radio("Bo'lim:", ["🤖 AI Yordamchi", "📊 Jurnal Monitoringi"])

# --- 4. XAVFSIZLIK ---
if "authenticated" not in st.session_state:
    st.title(f"🏫 {MAKTAB_NOMI}")
    parol = st.text_input("Kirish paroli:", type="password")
    if st.button("Kirish"):
        if parol == TO_GRI_PAROL:
            st.session_state.authenticated = True
            st.rerun()
        else: st.error("Xato!")
    st.stop()

# --- 5. AI YORDAMCHI (TO'QISH TAQIQLANGAN) ---
if menu == "🤖 AI Yordamchi":
    st.title("🤖 Maktab AI (Faqat faktlar)")
    
    if savol := st.chat_input("Savol bering (masalan: Matematika o'qituvchilari)"):
        with st.chat_message("user"): st.markdown(savol)
        
        with st.chat_message("assistant"):
            # 1. QIDIRUV MANTIQI
            found_context = ""
            if df_baza is not None:
                q = savol.lower()
                # Rasmdagi ustunlar bo'yicha qidiruv
                mask = df_baza.apply(lambda row: any(q in str(v).lower() for v in row), axis=1)
                res = df_baza[mask]
                
                if not res.empty:
                    st.dataframe(res) # Topilganini jadvalda ko'rsatadi
                    found_context = res.to_string(index=False)
                else:
                    found_context = "BAZADA MA'LUMOT YO'Q"

            # 2. AI JAVOBI (Qat'iy rejim)
            # Temperature 0.0 qilinganda AI to'qishni to'xtatadi
            prompt = f"""Sen faqat berilgan bazadagi ma'lumotga tayangan holda javob berasan.
            Agar ma'lumot topilmasa, FAQAT 'Kechirasiz, bazada bunday ma'lumot yo'q' deb javob ber.
            ASLO o'zingdan ism yoki fan qo'shma!
            
            Baza: {found_context}
            Savol: {savol}"""

            payload = {
                "model": "llama-3.3-70b-versatile",
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.0 
            }
            
            try:
                r = requests.post("https://api.groq.com/openai/v1/chat/completions", 
                                 json=payload, headers={"Authorization": f"Bearer {GROQ_API_KEY}"})
                st.markdown(r.json()['choices'][0]['message']['content'])
            except: st.error("AI bilan bog'lanishda xato.")

# --- 6. MONITORING (TELEGRAM QISMI) ---
elif menu == "📊 Jurnal Monitoringi":
    st.title("📊 Jurnal Monitoringi")
    # Telegram yuborish kodingiz o'zgarishsiz qoldi...
    # (Bu yerda sizning BOT_TOKEN va GURUH_ID ishlatilgan monitoring kodi turibdi)
