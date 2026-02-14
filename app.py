import streamlit as st
import pandas as pd
import os
import requests
import io
import random

# --- 1. ASOSIY SOZLAMALAR ---
MAKTAB_NOMI = "1-sonli umumta'lim maktabi"
DIREKTOR_FIO = "Mahmudov Matyoqub Narzulloyevich" # Direktor ism-familiyasi
GROQ_API_KEY = "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"
TO_GRI_PAROL = "informatika2024"
MONITORING_KODI = "admin777" 
BOT_TOKEN = "8524007504:AAFiMXSbXhe2M-84WlNM16wNpzhNolfQIf8"
GURUH_ID = "-5045481739" 

st.set_page_config(page_title=MAKTAB_NOMI, layout="wide")

# Hikmatli so'zlar ro'yxati
HIKMATLAR = [
    "Ilm — saodat kalitidir.",
    "Hunari yo'q kishi — mevasi yo'q daraxt.",
    "Ilm izla, igna bilan quduq qazigandek bo'lsa ham.",
    "O'qigan o'zini taniydi, o'qimagan — ko'zini.",
    "Bilim — tuganmas xazina.",
    "Kitob — bilim manbai.",
    "Aql — yoshda emas, boshda.",
    "Ilm — qalb chirog'i."
]

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

# --- 3. SIDEBAR (DIREKTOR QAYTIB KELDI) ---
with st.sidebar:
    st.title(f"🏛 {MAKTAB_NOMI}")
    st.write(f"👤 **Maktab direktori:** \n{DIREKTOR_FIO}") # Direktor nomi ekranda
    st.divider()
    menu = st.radio("Bo'limni tanlang:", ["🤖 AI bilan muloqot", "📊 Jurnal Monitoringi"])
    st.divider()
    st.info(f"✨ **Kun hikmati:**\n*{random.choice(HIKMATLAR)}*")

# --- 4. XAVFSIZLIK ---
if "authenticated" not in st.session_state:
    st.title(f"🏫 {MAKTAB_NOMI}")
    parol = st.text_input("Kirish paroli:", type="password")
    if st.button("Kirish"):
        if parol == TO_GRI_PAROL:
            st.session_state.authenticated = True
            st.rerun()
        else: st.error("Parol noto'g'ri!")
    st.stop()

# --- 5. MAKTAB SUN'IY INTELLEKTI BILAN MULOQOT ---
if menu == "🤖 AI bilan muloqot":
    st.title("🤖 Maktab sun'iy intellekti bilan muloqot")
    
    if "greeted" not in st.session_state:
        st.session_state.greeted = False

    if not st.session_state.greeted:
        with st.chat_message("assistant"):
            st.markdown(f"**Assalomu alaykum, hurmatli foydalanuvchi!**\n\n{random.choice(HIKMATLAR)}\n\nSizga qanday ma'lumot qidirib berishim mumkin?")
        st.session_state.greeted = True

    if savol := st.chat_input("Savolingizni kiriting..."):
        with st.chat_message("user"): st.markdown(savol)
        
        with st.chat_message("assistant"):
            res_df = pd.DataFrame()
            
            salomlar = ["salom", "assalom", "qalay", "yaxshimi"]
            is_greeting = any(s in savol.lower() for s in salomlar)

            if is_greeting:
                st.markdown(f"Vaalaykum assalom! **Hurmatli foydalanuvchi**, sizga xizmat qilishdan mamnunman.\n\n*Hikmat:* {random.choice(HIKMATLAR)}")
            elif sheets_baza:
                is_teacher_req = any(x in savol.lower() for x in ["o'qituvchi", "pedagog", "ro'yxat", "xodim"])
                
                if is_teacher_req and "Лист2" in sheets_baza:
                    res_df = sheets_baza["Лист2"]
                else:
                    all_df = pd.concat(sheets_baza.values(), ignore_index=True, sort=False).fillna("")
                    q = savol.lower()
                    mask = all_df.apply(lambda row: any(q in str(v).lower() for v in row), axis=1)
                    res_df = all_df[mask]

                if not res_df.empty:
                    st.success(f"Natija topildi ({len(res_df)} ta qator).")
                    st.dataframe(res_df, use_container_width=True)
                    
                    # EXCEL YUKLASH TUGMASI
                    output = io.BytesIO()
                    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                        res_df.to_excel(writer, index=False)
                    st.download_button("📥 Natijani Excelda yuklab olish", output.getvalue(), "natija.xlsx")
                else:
                    st.warning("Hurmatli foydalanuvchi, bazada bunday ma'lumot topilmadi.")

# --- 6. MONITORING (TELEGRAM QISMI O'ZGARMADI) ---
elif menu == "📊 Jurnal Monitoringi":
    st.title("📊 Jurnal Monitoringi (Telegram)")
    if "m_auth" not in st.session_state: st.session_state.m_auth = False
    if not st.session_state.m_auth:
        m_pass = st.text_input("Monitoring kodi:", type="password")
        if st.button("Kirish"):
            if m_pass == MONITORING_KODI:
                st.session_state.m_auth = True
                st.rerun()
            else: st.error("Xato!")
        st.stop()

    j_fayl = st.file_uploader("Faylni tanlang", type=['xlsx', 'xls'])
    if j_fayl:
        try:
            try: df_j = pd.read_excel(j_fayl, header=[0, 1])
            except: 
                j_fayl.seek(0)
                df_j = pd.read_html(j_fayl, header=0)[0]
            st.dataframe(df_j.head())
            if st.button("📢 Telegramga yuborish"):
                # Telegramga yuborish kodi o'z joyida
                requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", 
                             json={"chat_id": GURUH_ID, "text": f"📊 {MAKTAB_NOMI}\nMonitoring hisoboti yuborildi.", "parse_mode": "HTML"})
                st.success("✅ Telegramga yuborildi!")
        except Exception as e: st.error(f"Xato: {e}")
