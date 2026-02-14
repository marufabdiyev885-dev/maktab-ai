import streamlit as st
import pandas as pd
import os
import requests
import io
import random
import re

# --- 1. ASOSIY SOZLAMALAR ---
MAKTAB_NOMI = "1-sonli umumta'lim maktabi"
DIREKTOR_FIO = "Mahmudov Matyoqub Narzulloyevich"
TO_GRI_PAROL = "informatika2024"
MONITORING_KODI = "admin777" 
BOT_TOKEN = "8524007504:AAFiMXSbXhe2M-84WlNM16wNpzhNolfQIf8"
GURUH_ID = "-5045481739" 

HIKMATLAR_RO_YXATI = [
    "Ilm — saodat kalitidir.",
    "Hunari yo'q kishi — mevasi yo'q daraxt.",
    "Ilm izla, igna bilan quduq qazigandek bo'lsa ham.",
    "Bilim — tuganmas xazina.",
    "Odob — har bir kishining ziynatidir."
]

st.set_page_config(page_title=MAKTAB_NOMI, layout="wide")

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

# --- SIDEBAR ---
with st.sidebar:
    st.title(f"🏛 {MAKTAB_NOMI}")
    st.write(f"👤 **Direktor:** \n{DIREKTOR_FIO}")
    st.divider()
    menu = st.radio("Bo'limni tanlang:", ["🤖 AI Muloqot", "📊 Jurnal Monitoringi"])
    st.divider()
    st.info(f"✨ **Kun hikmati:**\n*{random.choice(HIKMATLAR_RO_YXATI)}*")

# --- XAVFSIZLIK ---
if "authenticated" not in st.session_state:
    st.title(f"🏫 {MAKTAB_NOMI}")
    parol = st.text_input("Kirish paroli:", type="password")
    if st.button("Kirish"):
        if parol == TO_GRI_PAROL:
            st.session_state.authenticated = True
            st.rerun()
        else: st.error("Parol xato!")
    st.stop()

# --- 5. AI MULOQOT (ISMGA MOSLASHISH VA TANISHTIRISH) ---
if menu == "🤖 AI Muloqot":
    st.title("🤖 Aqlli va Farosatli Muloqot")
    
    # Foydalanuvchi ismini saqlash uchun session_state
    if "user_name" not in st.session_state:
        st.session_state.user_name = "aka" # Default

    if "greeted" not in st.session_state:
        st.session_state.greeted = False
    if not st.session_state.greeted:
        with st.chat_message("assistant"):
            st.markdown(f"**Assalomu alaykum!** Men maktabimizning aqlli yordamchisiman. Ismingiz nima?")
        st.session_state.greeted = True

    if savol := st.chat_input("Savol yozing yoki ismingizni ayting..."):
        with st.chat_message("user"): st.markdown(savol)
        
        with st.chat_message("assistant"):
            q = savol.lower().strip()
            
            # Ismni aniqlash (Farosat qismi)
            name_match = re.search(r"(ismim|ismimni|otim|otimni)\s+([a-zа-я]+)", q)
            if name_match:
                st.session_state.user_name = name_match.group(2).capitalize()
                st.markdown(f"Tanishganimdan xursandman, {st.session_state.user_name}! Endi sizga qanday yordam bera olaman?")
            
            # O'zini tanishtirish
            elif any(x in q for x in ["o'zingni tanishtir", "kimsan", "nima qilasan", "isming nima"]):
                st.markdown(f"Men **{MAKTAB_NOMI}** uchun maxsus yaratilgan Sun'iy Intellekt yordamchisiman. Vazifam — bazadan o'qituvchi va o'quvchilarni topish, jurnal monitoringini yuritish va siz bilan suhbatlashish. Xizmatingizdaman, {st.session_state.user_name}!")

            # Rahmat va boshqa gaplar
            elif any(x in q for x in ["rahmat", "zo'r", "ajoyib", "baraka top"]):
                st.markdown(f"Arzimaydi, {st.session_state.user_name}! Sizga foydam tekkanidan xursandman. 😊")
                
            elif any(x in q for x in ["salom", "assalom"]):
                st.markdown(f"Vaalaykum assalom! Sog'liklar yaxshimi, {st.session_state.user_name}?")

            # Qidiruv qismi (O'zgarishsiz)
            elif sheets_baza:
                topildi = False
                is_teacher_req = any(x in q for x in ["o'qituvchi", "pedagog", "xodim", "ro'yxat"])
                
                if is_teacher_req:
                    for name, df in sheets_baza.items():
                        if any("pedagog" in col for col in df.columns) or "лист2" in name.lower():
                            st.success(f"{st.session_state.user_name}, o'qituvchilar ro'yxati topildi:")
                            st.dataframe(df, use_container_width=True)
                            topildi = True
                            break
                
                if not topildi:
                    for name, df in sheets_baza.items():
                        if re.match(r'^\d{1,2}-[a-zа-я]$', q):
                            pattern = rf"\b{re.escape(q)}\b"
                            mask = df.apply(lambda row: any(re.search(pattern, str(v).lower()) for v in row), axis=1)
                        else:
                            mask = df.apply(lambda row: q in str(v).lower() for v in row)
                        
                        res_df = df[mask]
                        if not res_df.empty:
                            st.success(f"Mana, {st.session_state.user_name}, topildi:")
                            st.dataframe(res_df, use_container_width=True)
                            topildi = True
                
                if not topildi:
                    st.warning(f"Kechirasiz {st.session_state.user_name}, topolmadim.")

# --- MONITORING (O'ZGARISHSIZ) ---
elif menu == "📊 Jurnal Monitoringi":
    st.title("📊 Jurnal Monitoringi")
    if "m_auth" not in st.session_state: st.session_state.m_auth = False
    if not st.session_state.m_auth:
        if st.text_input("Monitoring kodi:", type="password") == MONITORING_KODI:
            if st.button("Kirish"):
                st.session_state.m_auth = True
                st.rerun()
        st.stop()
    j_fayl = st.file_uploader("Excel yuklang", type=['xlsx', 'xls', 'html'])
    if j_fayl:
        try:
            try: df_j = pd.read_excel(j_fayl)
            except:
                j_fayl.seek(0)
                df_j = pd.read_html(j_fayl, header=0)[0]
            df_j.columns = [str(c).replace('\n', ' ').strip() for c in df_j.columns]
            st.dataframe(df_j)
            col_target, col_name = "Baholar qo'yilgan jurnallar soni", "O'qituvchi"
            kamchiliklar = []
            if col_target in df_j.columns:
                for _, row in df_j.iterrows():
                    nums = re.findall(r'(\d+)', str(row[col_target]))
                    if len(nums) >= 2 and int(nums[0]) < int(nums[1]):
                        kamchiliklar.append(f"❌ {row[col_name]}: {int(nums[1]) - int(nums[0])} ta jurnal chala")
            xabar_tahlili = "✅ Barcha jurnallar to'liq!" if not kamchiliklar else "⚠️ **Kamchiliklar:**\n" + "\n".join(kamchiliklar)
            st.info(xabar_tahlili)
            if st.button("📢 Telegramga yuborish"):
                requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", json={"chat_id": GURUH_ID, "text": f"<b>📊 Monitoring</b>\n\n{xabar_tahlili}", "parse_mode": "HTML"})
                st.success("✅ Yuborildi!")
        except Exception as e: st.error(f"Xato: {e}")
