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
GROQ_API_KEY = "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"
TO_GRI_PAROL = "informatika2024"
MONITORING_KODI = "admin777" 
BOT_TOKEN = "8524007504:AAFiMXSbXhe2M-84WlNM16wNpzhNolfQIf8"
GURUH_ID = "-5045481739" 

HIKMATLAR_RO_YXATI = ["Ilm — saodat kalitidir.", "Bilim — tuganmas xazina.", "Kitob — bilim manbai."]

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
    st.write(f"👤 **Maktab direktori:** \n{DIREKTOR_FIO}")
    st.divider()
    menu = st.radio("Bo'limni tanlang:", ["🤖 AI bilan muloqot", "📊 Jurnal Monitoringi"])
    st.divider()
    st.info(f"✨ **Kun hikmati:**\n*{random.choice(HIKMATLAR_RO_YXATI)}*")

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

# --- 5. AI BILAN MULOQOT ---
if menu == "🤖 AI bilan muloqot":
    st.title("🤖 Maktab sun'iy intellekti bilan muloqot")
    if savol := st.chat_input("Savolingizni kiriting..."):
        with st.chat_message("user"): st.markdown(savol)
        with st.chat_message("assistant"):
            st.markdown("**Hurmatli foydalanuvchi**, natijalar jadvalda ko'rsatiladi.")

# --- 6. JURNAL MONITORINGI (SIZ AYTGAN ANIQ MANTIQ) ---
elif menu == "📊 Jurnal Monitoringi":
    st.title("📊 Jurnal Monitoringi")
    
    if "m_auth" not in st.session_state: st.session_state.m_auth = False
    if not st.session_state.m_auth:
        m_pass = st.text_input("Monitoring kodi:", type="password")
        if st.button("Kirish"):
            if m_pass == MONITORING_KODI:
                st.session_state.m_auth = True
                st.rerun()
            else: st.error("Xato!")
        st.stop()

    j_fayl = st.file_uploader("Faylni yuklang", type=['xlsx', 'xls', 'html'])
    if j_fayl:
        try:
            try:
                df_j = pd.read_excel(j_fayl)
            except:
                j_fayl.seek(0)
                df_j = pd.read_html(j_fayl, header=0)[0]
            
            df_j.columns = [str(c).replace('\n', ' ').strip() for c in df_j.columns]
            st.dataframe(df_j)

            col_target = "Baholar qo'yilgan jurnallar soni"
            col_name = "O'qituvchi"
            
            # --- MONITORING HISOB-KITOBI ---
            kamchiliklar = []
            if col_target in df_j.columns:
                for _, row in df_j.iterrows():
                    val = str(row[col_target])
                    nums = re.findall(r'(\d+)', val)
                    if len(nums) >= 2:
                        qoyilgan = int(nums[0])
                        jami = int(nums[1])
                        if qoyilgan < jami:
                            kamchiliklar.append(f"❌ {row[col_name]}: {jami - qoyilgan} ta jurnal yozilmagan")
            
            # Xabarni shakllantirish
            if not kamchiliklar:
                xabar_tahlili = "✅ Barcha jurnallar to'liq baholangan!"
            else:
                xabar_tahlili = "⚠️ **Kamchiliklar aniqlandi:**\n" + "\n".join(kamchiliklar)

            st.info(xabar_tahlili)

            # --- TELEGRAMGA YUBORISH ---
            if st.button("📢 Telegramga hisobotni yuborish"):
                try:
                    full_msg = f"<b>📊 {MAKTAB_NOMI} Monitoringi</b>\n\n{xabar_tahlili}"
                    res = requests.post(
                        f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", 
                        json={"chat_id": GURUH_ID, "text": full_msg, "parse_mode": "HTML"}
                    )
                    if res.status_code == 200:
                        st.success("✅ Telegramga yuborildi!")
                    else:
                        st.error("❌ Xatolik yuz berdi!")
                except Exception as e:
                    st.error(f"Xato: {e}")
                    
        except Exception as e:
            st.error(f"Faylni o'qishda xato: {e}")
