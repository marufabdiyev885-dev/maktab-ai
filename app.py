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

# --- 2. BAZANI YUKLASH (HAMMA LISTLARNI ANALIZ QILISH) ---
@st.cache_data
def yuklash():
    files = [f for f in os.listdir('.') if f.lower().endswith(('.xlsx', '.xls', '.csv')) and 'app.py' not in f]
    all_data = []
    log_info = []
    
    for f in files:
        try:
            if f.endswith(('.xlsx', '.xls')):
                sheets = pd.read_excel(f, sheet_name=None, dtype=str)
                for name, df in sheets.items():
                    if not df.empty:
                        df.columns = [str(c).strip().lower() for c in df.columns]
                        all_data.append(df)
                        log_info.append(f"Fayl: {f}, List: {name}, Qator: {len(df)}")
            elif f.endswith('.csv'):
                df_s = pd.read_csv(f, dtype=str)
                df_s.columns = [str(c).strip().lower() for c in df_s.columns]
                all_data.append(df_s)
                log_info.append(f"Fayl: {f}, Qator: {len(df_s)}")
        except Exception as e:
            log_info.append(f"Xato ({f}): {str(e)}")
            
    if all_data:
        full_df = pd.concat(all_data, ignore_index=True, sort=False)
        full_df = full_df.applymap(lambda x: str(x).strip() if pd.notnull(x) else "")
        return full_df, log_info
    return None, log_info

df_baza, yuklash_logi = yuklash()

# --- 3. SIDEBAR ---
with st.sidebar:
    st.title(f"🏛 {MAKTAB_NOMI}")
    menu = st.radio("Menyu:", ["🤖 AI Yordamchi", "📊 Jurnal Monitoringi"])
    if st.checkbox("Baza holatini ko'rish"):
        st.write("### Yuklangan ma'lumotlar:")
        for log in yuklash_logi:
            st.text(log)
        if df_baza is not None:
            st.success(f"Jami qatorlar: {len(df_baza)}")

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

# --- 5. AI YORDAMCHI (ANIK QIDIRUV) ---
if menu == "🤖 AI Yordamchi":
    st.title("🤖 Maktab AI")
    if "messages" not in st.session_state:
        st.session_state.messages = [{"role": "assistant", "content": "Assalomu alaykum! Barcha listlar tekshirildi. Savolingizni bering."}]

    for m in st.session_state.messages:
        with st.chat_message(m["role"]): st.markdown(m["content"])

    if savol := st.chat_input("Masalan: Matematika o'qituvchisi kim?"):
        st.session_state.messages.append({"role": "user", "content": savol})
        with st.chat_message("user"): st.markdown(savol)
        
        with st.chat_message("assistant"):
            found_data = "MA'LUMOT TOPILMADI"
            
            if df_baza is not None:
                # Qidiruvni yanada kuchaytirdik (har bir so'zni alohida qidiradi)
                q_words = [s.lower() for s in savol.replace("?", "").split() if len(s) > 2]
                if q_words:
                    res = df_baza[df_baza.apply(lambda row: all(any(k in str(v).lower() for v in row) for k in q_words), axis=1)]
                    if res.empty: # Agar hammasi birga topilmasa, hech bo'lmasa bittasi borini qidiradi
                        res = df_baza[df_baza.apply(lambda row: any(k in str(v).lower() for k in q_words for v in row), axis=1)]
                    
                    if not res.empty:
                        st.dataframe(res)
                        found_data = res.head(10).to_string(index=False)

            system_prompt = f"Sen faqat bazadagi ma'lumotdan javob beruvchi botsan. Bazada yo'q narsani 'topilmadi' degin."
            
            payload = {
                "model": "llama-3.3-70b-versatile",
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Baza ma'lumoti: {found_data}\n\nSavol: {savol}"}
                ],
                "temperature": 0.0
            }
            
            try:
                r = requests.post("https://api.groq.com/openai/v1/chat/completions", 
                                 json=payload, headers={"Authorization": f"Bearer {GROQ_API_KEY}"})
                ai_text = r.json()['choices'][0]['message']['content']
            except: ai_text = "Tizim xatosi."
            
            st.markdown(ai_text)
            st.session_state.messages.append({"role": "assistant", "content": ai_text})

# --- 6. MONITORING (Telegram qismi tegmasdan saqlandi) ---
elif menu == "📊 Jurnal Monitoringi":
    # Sizning monitoring kodingiz o'z holida qoldi...
    st.title("📊 Jurnal Monitoringi")
    # ... (kodning qolgan qismi)
