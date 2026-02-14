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

# --- 5. AI MULOQOT (SALOM-ALIK VA ISM SO'RASH) ---
if menu == "🤖 AI Muloqot":
    st.title("🤖 Aqlli va Odobli Muloqot")
    
    # Ismni saqlash
    if "user_name" not in st.session_state:
        st.session_state.user_name = None 

    # Birinchi bo'lib salom berish va ism so'rash
    if "greeted" not in st.session_state:
        st.session_state.greeted = False

    if not st.session_state.greeted:
        with st.chat_message("assistant"):
            st.markdown("Assalomu alaykum! Maktabimizning sun'iy intellekt tizimiga xush kelibsiz. 😊")
            st.markdown("Kechirasiz, ismingizni bilsam bo'ladimi? Sizga qanday murojaat qilay?")
        st.session_state.greeted = True

    if savol := st.chat_input("Javobingizni yoki savolni yozing..."):
        with st.chat_message("user"): st.markdown(savol)
        
        with st.chat_message("assistant"):
            q = savol.lower().strip()
            
            # Ismni aniqlash mantiqi
            if st.session_state.user_name is None:
                # Ismni ajratib olish (Ismim Ali, Men Vali va hokazo)
                name_parts = re.search(r"(ismim|otim|men|man)\s+([a-zа-я]+)", q)
                if name_parts:
                    st.session_state.user_name = name_parts.group(2).capitalize()
                else:
                    # Agar shunchaki ismini yozsa
                    st.session_state.user_name = savol.capitalize()
                
                st.markdown(f"Tanishganimdan juda xursandman, **{st.session_state.user_name}**! Endi men sizga maktab bazasidan istalgan ma'lumotni topishda yordam berishim mumkin. Nima qidiramiz?")
            
            # O'zini tanishtirish
            elif any(x in q for x in ["o'zingni tanishtir", "kimsan", "vazifang nima"]):
                st.markdown(f"Men maktabimizning raqamli yordamchisiman. {st.session_state.user_name}, men orqali o'qituvchilar ro'yxatini, sinflarni va monitoring natijalarini ko'rishingiz mumkin.")

            # Rahmat va muloqot
            elif any(x in q for x in ["rahmat", "zo'r", "ajoyib"]):
                st.markdown(f"Arzimaydi, {st.session_state.user_name}! Har doim xizmatingizdaman.")

            # Qidiruv qismi (1 va 11 muammosi hal qilingan holda)
            elif sheets_baza:
                topildi = False
                is_teacher_req = any(x in q for x in ["o'qituvchi", "pedagog", "xodim", "ro'yxat"])
                
                if is_teacher_req:
                    for name, df in sheets_baza.items():
                        if any("pedagog" in col for col in df.columns) or "лист2" in name.lower():
                            st.success(f"{st.session_state.user_name}, mana o'qituvchilar ro'yxati:")
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
                            st.success(f"Topildi, {st.session_state.user_name}:")
                            st.dataframe(res_df, use_container_width=True)
                            topildi = True
                
                if not topildi:
                    st.warning(f"Kechirasiz {st.session_state.user_name}, bazadan topolmadim.")

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
            col_target, col_name = "Baholar qo'yilgan jurnallar somi", "O'qituvchi"
            kamchiliklar = []
            if col_target in df_j.columns:
                for _, row in df_j.iterrows():
                    nums = re.findall(r'(\d+)', str(row[col_target]))
                    if len(nums) >= 2 and int(nums[0]) < int(nums[1]):
                        kamchiliklar.append(f"❌ {row[col_name]}: {int(nums[1]) - int(nums[0])} ta jurnal chala")
            xabar_tahlili = "✅ Hammasi to'liq!" if not kamchiliklar else "⚠️ **Kamchiliklar:**\n" + "\n".join(kamchiliklar)
            st.info(xabar_tahlili)
            if st.button("📢 Telegramga yuborish"):
                requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", json={"chat_id": GURUH_ID, "text": f"<b>📊 Monitoring</b>\n\n{xabar_tahlili}", "parse_mode": "HTML"})
                st.success("✅ Yuborildi!")
        except Exception as e: st.error(f"Xato: {e}")
