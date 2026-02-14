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

# --- 2. BAZANI YUKLASH ---
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
    st.divider()
    st.write(f"👤 **Direktor:** \n{DIREKTOR_FIO}")

# --- 4. XAVFSIZLIK ---
if "authenticated" not in st.session_state:
    st.title(f"🏫 {MAKTAB_NOMI}")
    parol = st.text_input("Tizimga kirish paroli:", type="password")
    if st.button("Kirish"):
        if parol == TO_GRI_PAROL:
            st.session_state.authenticated = True
            st.rerun()
        else: st.error("Parol noto'g'ri!")
    st.stop()

# --- 5. AI YORDAMCHI (FAROSATLI VA XUSHOMADLI) ---
if menu == "🤖 AI Yordamchi":
    st.title("🤖 Aqlli Maktab Yordamchisi")
    
    if "messages" not in st.session_state:
        st.session_state.messages = [{"role": "assistant", "content": f"Assalomu alaykum, Ma'rufjon aka! Men {MAKTAB_NOMI} AI yordamchisiman. Sizga qanday ko'mak bera olaman?"}]

    for m in st.session_state.messages:
        with st.chat_message(m["role"]): st.markdown(m["content"])

    if savol := st.chat_input("Savolingizni yozing..."):
        st.session_state.messages.append({"role": "user", "content": savol})
        with st.chat_message("user"): st.markdown(savol)
        
        with st.chat_message("assistant"):
            # Qidiruv mantiqi
            res_df = pd.DataFrame()
            found_context = ""
            
            # Salomlashish yoki oddiy gaplarni aniqlash
            oddiy_gap = any(x in savol.lower() for x in ["salom", "assalom", "rahmat", "qalay", "yaxshimi", "tashakkur"])
            
            if sheets_baza and not oddiy_gap:
                is_teacher_req = any(x in savol.lower() for x in ["o'qituvchi", "pedagog", "ro'yxat", "list", "xodim"])
                if is_teacher_req and "Лист2" in sheets_baza:
                    res_df = sheets_baza["Лист2"]
                else:
                    all_df = pd.concat(sheets_baza.values(), ignore_index=True, sort=False).fillna("")
                    q = savol.lower()
                    mask = all_df.apply(lambda row: any(q in str(v).lower() for v in row), axis=1)
                    res_df = all_df[mask]

            if not res_df.empty:
                st.dataframe(res_df, use_container_width=True)
                found_context = res_df.head(15).to_string(index=False)
                # Excel tugmasi
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                    res_df.to_excel(writer, index=False)
                st.download_button("📥 Excelda yuklab olish", output.getvalue(), "natija.xlsx")

            # AI uchun farosatli Prompt
            prompt = f"""Sen {MAKTAB_NOMI}ning juda xushmuomala AI yordamchisisan. 
            1. Agar foydalanuvchi salom bersa, alik ol va xushomad qil.
            2. Agar savol bazaga oid bo'lsa, jadvalda ma'lumot borligini ayt.
            3. Bazada yo'q ismlarni aslo to'qima! 
            4. Ma'rufjon aka bilan juda do'stona gaplash.
            
            Baza ma'lumoti: {found_context if found_context else 'Topilmadi'}
            Savol: {savol}"""

            try:
                r = requests.post("https://api.groq.com/openai/v1/chat/completions", 
                                 json={"model": "llama-3.3-70b-versatile", 
                                       "messages": [{"role": "user", "content": prompt}],
                                       "temperature": 0.7}, # Farosat uchun biroz oshirdik
                                 headers={"Authorization": f"Bearer {GROQ_API_KEY}"})
                ai_javob = r.json()['choices'][0]['message']['content']
                st.markdown(ai_javob)
                st.session_state.messages.append({"role": "assistant", "content": ai_javob})
            except: st.write("Tizimda kichik uzilish, lekin jadval tayyor!")

# --- 6. MONITORING (TELEGRAM ISHLAYDI) ---
elif menu == "📊 Jurnal Monitoringi":
    st.title("📊 Telegram Monitoring")
    if "m_auth" not in st.session_state: st.session_state.m_auth = False
    if not st.session_state.m_auth:
        m_pass = st.text_input("Kirish kodi:", type="password")
        if st.button("Kirish"):
            if m_pass == MONITORING_KODI:
                st.session_state.m_auth = True
                st.rerun()
            else: st.error("Kod xato!")
        st.stop()

    j_fayl = st.file_uploader("Excel yuklang", type=['xlsx', 'xls'])
    if j_fayl:
        try:
            try: df_j = pd.read_excel(j_fayl, header=[0, 1])
            except: 
                j_fayl.seek(0)
                df_j = pd.read_html(j_fayl, header=0)[0]
            st.dataframe(df_j.head())
            if st.button("📢 Telegramga yuborish"):
                r = requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", 
                                 json={"chat_id": GURUH_ID, "text": f"📊 {MAKTAB_NOMI}\nMonitoring yakunlandi.", "parse_mode": "HTML"})
                if r.status_code == 200: st.success("Telegramga yuborildi!")
        except Exception as e: st.error(f"Xato: {e}")
