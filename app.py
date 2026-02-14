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

# --- 2. BAZANI YUKLASH (HAMMA LISTLARNI BIRLASHTIRISH) ---
@st.cache_data
def yuklash():
    files = [f for f in os.listdir('.') if f.lower().endswith(('.xlsx', '.xls', '.csv')) and 'app.py' not in f]
    all_data = []
    for f in files:
        try:
            sheets = pd.read_excel(f, sheet_name=None, dtype=str)
            for name, df in sheets.items():
                if not df.empty:
                    df.columns = [str(c).strip().lower() for c in df.columns]
                    all_data.append(df)
        except: continue
    if all_data:
        full_df = pd.concat(all_data, ignore_index=True, sort=False)
        full_df = full_df.fillna("") 
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

# --- 5. AI YORDAMCHI (RO'YXATNI CHIQARADIGAN VARIANT) ---
if menu == "🤖 AI Yordamchi":
    st.title("🤖 Maktab AI Yordamchisi")
    if "messages" not in st.session_state:
        st.session_state.messages = []

    for m in st.session_state.messages:
        with st.chat_message(m["role"]): st.markdown(m["content"])

    if savol := st.chat_input("Masalan: O'qituvchilar ro'yxatini ber"):
        st.session_state.messages.append({"role": "user", "content": savol})
        with st.chat_message("user"): st.markdown(savol)
        
        with st.chat_message("assistant"):
            found_context = ""
            
            if df_baza is not None:
                # Qidiruv so'zlarini aniqlash
                q_words = [s.lower() for s in savol.replace("?", "").split() if len(s) > 2]
                
                # Agar foydalanuvchi "ro'yxat" yoki "hamma" desa, hamma pedagoglarni oladi
                is_list_request = any(x in savol.lower() for x in ["ro'yxat", "hamma", "list", "o'qituvchilar"])
                
                if is_list_request and "mutaxassisligi" in df_baza.columns:
                    res = df_baza[df_baza["mutaxassisligi"] != ""] # Faqat o'qituvchilar
                elif q_words:
                    mask = df_baza.apply(lambda row: any(any(k in str(v).lower() for v in row) for k in q_words), axis=1)
                    res = df_baza[mask]
                else:
                    res = pd.DataFrame()

                if not res.empty:
                    st.dataframe(res) # Jadvalni baribir ko'rsatamiz
                    # AIga ma'lumotni matn ko'rinishida beramiz
                    found_context = res.to_string(index=False)

            # AIga aniq vazifa: Ma'lumotni ro'yxat qilib ber!
            system_prompt = f"""Sen {MAKTAB_NOMI} maktabi yordamchisisan. 
            Vazifang: Senga berilgan bazadagi ma'lumotlarni chiroyli ro'yxat ko'rinishida foydalanuvchiga taqdim etish.
            Agar bazada ma'lumot bo'lsa, ularni 'F.I.SH - Lavozimi/Sinfi' formatida sanab ber.
            Bazadagi ma'lumotdan tashqariga chiqma."""
            
            payload = {
                "model": "llama-3.3-70b-versatile",
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Baza: {found_context}\n\nSavol: {savol}"}
                ], "temperature": 0.4 # Biroz erkinlik berdik, ro'yxatni chiroyli tuzishi uchun
            }
            
            try:
                r = requests.post("https://api.groq.com/openai/v1/chat/completions", 
                                 json=payload, headers={"Authorization": f"Bearer {GROQ_API_KEY}"})
                ai_text = r.json()['choices'][0]['message']['content']
            except: ai_text = "Natijalar yuqoridagi jadvalda ko'rsatildi."
            
            st.markdown(ai_text)
            st.session_state.messages.append({"role": "assistant", "content": ai_text})

# --- 6. JURNAL MONITORINGI (TELEGRAM) ---
elif menu == "📊 Jurnal Monitoringi":
    # Bu bo'lim o'sha siz ishlatayotgan Telegram yuborish kodi
    st.title("📊 Jurnal Monitoringi")
    # ... (monitoring kodi davom etadi)
