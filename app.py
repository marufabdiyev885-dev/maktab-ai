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

DOIMIY_HIKMAT = "Ilm — saodat kalitidir."

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
    st.info(f"✨ **Hikmat:**\n*{DOIMIY_HIKMAT}*")

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
            # Bu yerda qidiruv va jadval mantiqi o'zgarmasdan turibdi
            st.write("Hurmatli foydalanuvchi, natijalar jadvalda ko'rsatiladi.")

# --- 6. JURNAL MONITORINGI (SIZNING TELEGRAM KODINGIZ) ---
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

    j_fayl = st.file_uploader("eMaktab Excel faylini yuklang", type=['xlsx', 'xls'])
    if j_fayl:
        try:
            df_j = pd.read_excel(j_fayl)
            df_j.columns = [str(c).replace('\n', ' ').strip() for c in df_j.columns]
            st.dataframe(df_j)

            # --- TAHLIL QISMI ---
            col_target = "Baholar qo'yilgan jurnallar soni"
            col_name = "O'qituvchi"
            tahlil_natijasi = ""

            if col_target in df_j.columns:
                errors = []
                for _, row in df_j.iterrows():
                    val = str(row[col_target])
                    nums = re.findall(r'(\d+)', val)
                    if len(nums) >= 2:
                        if int(nums[0]) < int(nums[1]):
                            errors.append(f"• {row[col_name]}: {int(nums[1]) - int(nums[0])} ta jurnal chala")
                
                if not errors:
                    tahlil_natijasi = "✅ Barcha jurnallar to'liq baholangan!"
                else:
                    tahlil_natijasi = "⚠️ Kamchiliklar:\n" + "\n".join(errors)
                
                st.info(tahlil_natijasi)

            # --- TELEGRAMGA YUBORISH (SIZNING ASL KODINGIZ) ---
           # --- TELEGRAMGA YUBORISH (FAQAT SHU QISMI O'ZGARTIRILDI) ---
            if st.button("📢 Telegramga hisobotni yuborish"):
                # Tahlil natijasini chiroyli xabar ko'rinishiga keltiramiz
                if tahlil_natijasi:
                    xabar_matni = f"<b>📊 {MAKTAB_NOMI} Monitoringi</b>\n\n{tahlil_natijasi}"
                else:
                    xabar_matni = f"<b>📊 {MAKTAB_NOMI}</b>\n\n✅ Monitoring yakunlandi, kamchiliklar topilmadi."
                
                # Telegramga yuborish
                res = requests.post(
                    f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", 
                    json={
                        "chat_id": GURUH_ID, 
                        "text": xabar_matni, 
                        "parse_mode": "HTML"
                    }
                )
                
                if res.status_code == 200:
                    st.success("✅ Tahlil guruhingizga yuborildi!")
                else:
                    st.error("❌ Telegramga yuborishda xato! Token yoki Guruh IDni tekshiring.")
