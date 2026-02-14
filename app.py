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
            if f.endswith(('.xlsx', '.xls')):
                # sheet_name=None hamma varaqlarni (List1, List2...) bittada o'qiydi
                sheets = pd.read_excel(f, sheet_name=None, dtype=str)
                for name, df in sheets.items():
                    if not df.empty:
                        # Ustunlarni tozalash
                        df.columns = [str(c).strip().lower() for c in df.columns]
                        all_data.append(df)
            elif f.endswith('.csv'):
                df_s = pd.read_csv(f, dtype=str)
                df_s.columns = [str(c).strip().lower() for c in df_s.columns]
                all_data.append(df_s)
        except:
            try:
                # eMaktab HTML formatidagi "Excel"lar uchun
                df_html = pd.read_html(f)[0].astype(str)
                df_html.columns = [str(c).strip().lower() for c in df_html.columns]
                all_data.append(df_html)
            except: continue
    
    if all_data:
        # Hamma listlarni bitta katta jadvalga yopishtiramiz
        full_df = pd.concat(all_data, ignore_index=True, sort=False)
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
    st.title(f"🏫 {MAKTAB_NOMI}")
    parol = st.text_input("Parol:", type="password")
    if st.button("Kirish"):
        if parol == TO_GRI_PAROL:
            st.session_state.authenticated = True
            st.rerun()
        else: st.error("Xato!")
    st.stop()

# --- 5. AI YORDAMCHI (FAQAT BAZADAN GAPIRADIGAN) ---
if menu == "🤖 AI Yordamchi":
    st.title("🤖 Maktab AI")
    if "messages" not in st.session_state:
        st.session_state.messages = [{"role": "assistant", "content": "Assalomu alaykum! Barcha listlar yuklandi. Kimni qidiramiz?"}]

    for m in st.session_state.messages:
        with st.chat_message(m["role"]): st.markdown(m["content"])

    if savol := st.chat_input("Savol yozing..."):
        st.session_state.messages.append({"role": "user", "content": savol})
        with st.chat_message("user"): st.markdown(savol)
        
        with st.chat_message("assistant"):
            found_data = "MA'LUMOT TOPILMADI"
            
            if df_baza is not None:
                q_words = [s.lower() for s in savol.split() if len(s) > 2]
                if q_words:
                    # Qidiruv: Jami bazadagi hamma ustun va qatordan qidiradi
                    res = df_baza[df_baza.apply(lambda row: any(k in str(v).lower() for k in q_words for v in row), axis=1)]
                    if not res.empty:
                        st.dataframe(res) # Topilganini jadvalda ko'rsatadi
                        found_data = res.head(15).to_string(index=False)

            # AI uchun qat'iy "Temir qoida" (System Prompt)
            system_prompt = f"""Sen faqat berilgan ma'lumotlar asosida javob beradigan yordamchisan. 
            MUHIM QOIDA: 
            1. Agar 'Baza' qismida ma'lumot bo'lmasa, FAQAT 'Kechirasiz, bazada bunday ma'lumot topilmadi' deb javob ber. 
            2. O'zingdan ISMLAR, LAVOZIMLAR yoki FANLARNI TO'QIMA!
            3. Faqat jadvalda bor narsani ayt.
            Hozirgi maktab: {MAKTAB_NOMI}."""
            
            payload = {
                "model": "llama-3.3-70b-versatile",
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Baza ma'lumoti: {found_data}\n\nSavol: {savol}"}
                ],
                "temperature": 0.0  # TO'QIMASLIGI UCHUN NOLGA TUSHIRDIK
            }
            
            try:
                r = requests.post("https://api.groq.com/openai/v1/chat/completions", 
                                 json=payload, headers={"Authorization": f"Bearer {GROQ_API_KEY}"})
                ai_text = r.json()['choices'][0]['message']['content']
            except: ai_text = "Tizimda uzilish."
            
            st.markdown(ai_text)
            st.session_state.messages.append({"role": "assistant", "content": ai_text})

# --- 6. MONITORING VA TELEGRAM (Sizning kodingiz, tegmasdan saqlandi) ---
elif menu == "📊 Jurnal Monitoringi":
    st.title("📊 Jurnal Monitoringi")
    if "m_auth" not in st.session_state: st.session_state.m_auth = False
    if not st.session_state.m_auth:
        m_pass = st.text_input("Kodi:", type="password")
        if st.button("Kirish"):
            if m_pass == MONITORING_KODI:
                st.session_state.m_auth = True
                st.rerun()
            else: st.error("Xato!")
        st.stop()

    j_fayl = st.file_uploader("Fayl yuklang", type=['xlsx', 'xls'])
    if j_fayl:
        try:
            # Excel yoki HTML o'qish (eMaktab uchun)
            try: df_j = pd.read_excel(j_fayl, header=[0, 1])
            except: 
                j_fayl.seek(0)
                df_j = pd.read_html(j_fayl, header=0)[0]
            
            st.dataframe(df_j.head())
            
            if st.button("📢 Telegramga yuborish"):
                # Telegramga yuborish buyrug'i
                requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", 
                             json={"chat_id": GURUH_ID, "text": f"📊 {MAKTAB_NOMI} hisoboti tayyor.", "parse_mode": "HTML"})
                st.success("Telegramga ketti!")
        except Exception as e: st.error(f"Xato: {e}")
