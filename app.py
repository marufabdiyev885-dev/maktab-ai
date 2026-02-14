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

# --- 2. BAZANI YUKLASH (USTUNLARNI BIRLASHTIRISH) ---
@st.cache_data
def yuklash():
    files = [f for f in os.listdir('.') if f.lower().endswith(('.xlsx', '.xls', '.csv')) and 'app.py' not in f]
    all_data = []
    for f in files:
        try:
            sheets = pd.read_excel(f, sheet_name=None, dtype=str)
            for name, df in sheets.items():
                if not df.empty:
                    # Ustun nomlarini qat'iy tozalash
                    df.columns = [str(c).strip().lower() for c in df.columns]
                    all_data.append(df)
        except: continue
            
    if all_data:
        # Sort=False har xil ustunli jadvallarni (pedagog va o'quvchi) yonma-yon qo'shadi
        full_df = pd.concat(all_data, ignore_index=True, sort=False)
        full_df = full_df.fillna("") # Bo'sh joylarni to'ldirish
        return full_df
    return None

df_baza = yuklash()

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

# --- 5. AI YORDAMCHI (ANIK QIDIRUV MANTIQI) ---
if menu == "🤖 AI Yordamchi":
    st.title("🤖 Maktab AI")
    if "messages" not in st.session_state:
        st.session_state.messages = []

    for m in st.session_state.messages:
        with st.chat_message(m["role"]): st.markdown(m["content"])

    if savol := st.chat_input("Kimni qidiramiz?"):
        st.session_state.messages.append({"role": "user", "content": savol})
        with st.chat_message("user"): st.markdown(savol)
        
        with st.chat_message("assistant"):
            found_data = "MA'LUMOT TOPILMADI"
            
            if df_baza is not None:
                # Qidiruv: savoldagi har bir so'zni bazadan qidiradi
                q_words = [s.lower() for s in savol.replace("?", "").split() if len(s) > 2]
                if q_words:
                    # Har bir qatorda so'zlardan biri bo'lsa topadi
                    mask = df_baza.apply(lambda row: any(any(k in str(v).lower() for v in row) for k in q_words), axis=1)
                    res = df_baza[mask]
                    
                    if not res.empty:
                        st.dataframe(res)
                        # AIga faqat topilgan qatorlarning eng muhim qismini yuboramiz
                        found_data = res.head(10).to_string(index=False)

            system_prompt = f"Sen {MAKTAB_NOMI} AI yordamchisisan. Faqat bazadagi {len(df_baza)} ta qatordan foydalanib javob ber. Topilmasa, 'topilmadi' degin."
            
            payload = {
                "model": "llama-3.3-70b-versatile",
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Baza: {found_data}\n\nSavol: {savol}"}
                ], "temperature": 0.0
            }
            
            try:
                r = requests.post("https://api.groq.com/openai/v1/chat/completions", 
                                 json=payload, headers={"Authorization": f"Bearer {GROQ_API_KEY}"})
                ai_text = r.json()['choices'][0]['message']['content']
            except: ai_text = "Natijalar jadvalda ko'rsatildi."
            
            st.markdown(ai_text)
            st.session_state.messages.append({"role": "assistant", "content": ai_text})

# --- 6. JURNAL MONITORINGI (TELEGRAM) ---
elif menu == "📊 Jurnal Monitoringi":
    # Bu bo'limda sizning Telegramga yuborish kodingiz o'zgarmasdan turibdi
    st.title("📊 Jurnal Monitoringi")
    # ... (monitoring kodi)
