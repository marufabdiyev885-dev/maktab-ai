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

# --- 2. BAZANI YUKLASH (HAMMA VARAQLARNI O'QISH) ---
@st.cache_data
def yuklash():
    files = [f for f in os.listdir('.') if f.lower().endswith(('.xlsx', '.xls', '.csv')) and 'app.py' not in f]
    all_sheets = {}
    for f in files:
        try:
            sheets = pd.read_excel(f, sheet_name=None, dtype=str)
            for name, df in sheets.items():
                if not df.empty:
                    df.columns = [str(c).strip().lower() for c in df.columns]
                    all_sheets[name] = df
        except: continue
    return all_sheets

sheets_baza = yuklash()

# --- 3. SIDEBAR ---
with st.sidebar:
    st.title(f"🏛 {MAKTAB_NOMI}")
    menu = st.radio("Bo'lim:", ["🤖 AI Yordamchi", "📊 Jurnal Monitoringi"])

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

# --- 5. AI YORDAMCHI (RO'YXATNI ANIQU CHIQARISH) ---
if menu == "🤖 AI Yordamchi":
    st.title("🤖 Maktab AI")
    
    if savol := st.chat_input("Savol yozing (masalan: O'qituvchilar ro'yxati)"):
        with st.chat_message("user"): st.markdown(savol)
        
        with st.chat_message("assistant"):
            found_context = ""
            
            # Agar o'qituvchi/pedagog so'ralsa, Лист2 ma'lumotlarini to'liq beramiz
            is_teacher_req = any(x in savol.lower() for x in ["o'qituvchi", "pedagog", "ro'yxat", "list"])
            
            if sheets_baza:
                if is_teacher_req and "Лист2" in sheets_baza:
                    res = sheets_baza["Лист2"]
                    st.dataframe(res)
                    found_context = res.to_string(index=False)
                else:
                    # Umumiy qidiruv (o'quvchi yoki boshqa narsa so'ralsa)
                    all_df = pd.concat(sheets_baza.values(), ignore_index=True, sort=False).fillna("")
                    q = savol.lower()
                    mask = all_df.apply(lambda row: any(q in str(v).lower() for v in row), axis=1)
                    res = all_df[mask]
                    if not res.empty:
                        st.dataframe(res)
                        found_context = res.to_string(index=False)

            # AI uchun qat'iy ko'rsatma
            prompt = f"""Sen faqat berilgan bazadagi ma'lumotdan foydalanasan.
            Agar Baza bo'sh bo'lmasa, undagi ismlarni chiroyli ro'yxat qilib foydalanuvchiga ber.
            Agar Baza bo'sh bo'lsa, 'Kechirasiz, topilmadi' degin.
            O'zingdan ism to'qima!
            
            Baza: {found_context if found_context else 'BO`SH'}
            Savol: {savol}"""

            payload = {
                "model": "llama-3.3-70b-versatile",
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.0 # To'qimasligi uchun
            }
            
            try:
                r = requests.post("https://api.groq.com/openai/v1/chat/completions", 
                                 json=payload, headers={"Authorization": f"Bearer {GROQ_API_KEY}"})
                st.markdown(r.json()['choices'][0]['message']['content'])
            except: st.error("AI ulanmadi.")

# --- 6. MONITORING (TELEGRAM QISMI) ---
elif menu == "📊 Jurnal Monitoringi":
    st.title("📊 Jurnal Monitoringi")
    # Telegram yuborish kodingiz o'z holida (BOT_TOKEN va GURUH_ID bilan) turibdi...
