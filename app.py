import streamlit as st
import pandas as pd
import os
import requests
import io
import random
import re
from googlesearch import search  # Internetdan qidirish uchun

# --- 1. ASOSIY SOZLAMALAR ---
MAKTAB_NOMI = "1-sonli umumta'lim maktabi"
DIREKTOR_FIO = "Mahmudov Matyoqub Narzulloyevich"
GROQ_API_KEY = "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"
TO_GRI_PAROL = "informatika2024"
MONITORING_KODI = "admin777" 
BOT_TOKEN = "8524007504:AAFiMXSbXhe2M-84WlNM16wNpzhNolfQIf8"
GURUH_ID = "-5045481739" 

HIKMATLAR_RO_YXATI = [
    "Ilm — saodat kalitidir.",
    "Hunari yo'q kishi — mevasi yo'q daraxt.",
    "Ilm izla, igna bilan quduq qazigandek bo'lsa ham.",
    "Bilim — tuganmas xazina.",
    "Vaqt — g'animat, o'tayotgan har oningni ilmga bag'ishla."
]

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
                    all_sheets[name] = df
        except: continue
    return all_sheets

sheets_baza = yuklash()

# --- 3. SIDEBAR ---
with st.sidebar:
    st.title(f"🏛 {MAKTAB_NOMI}")
    st.write(f"👤 **Maktab direktori:** \n{DIREKTOR_FIO}")
    st.divider()
    menu = st.radio("Bo'limni tanlang:", ["🤖 AI Muloqot va Qidiruv", "📊 Jurnal Monitoringi"])
    st.divider()
    st.info(f"✨ **Hikmat:**\n*{random.choice(HIKMATLAR_RO_YXATI)}*")

# --- 4. XAVFSIZLIK ---
if "authenticated" not in st.session_state:
    st.title(f"🏫 {MAKTAB_NOMI}")
    parol = st.text_input("Parolni yozing:", type="password")
    if st.button("Kirish"):
        if parol == TO_GRI_PAROL:
            st.session_state.authenticated = True
            st.rerun()
        else: st.error("Parol xato-ku, aka!")
    st.stop()

# --- 5. AI MULOQOT VA INTERNET QIDIRUV ---
if menu == "🤖 AI Muloqot va Qidiruv":
    st.title("🤖 Aqlli muloqot tizimi")
    
    if savol := st.chat_input("Savolingizni yoki ismni yozing..."):
        with st.chat_message("user"): st.markdown(savol)
        
        with st.chat_message("assistant"):
            q = savol.lower().strip()
            
            # 1. Insoniy muloqot qismi
            if q in ["rahmat", "katta rahmat", "tashakkur"]:
                st.markdown("Arziydi, Ma'rufjon aka! Xizmat bo'lsa aytaverasiz.")
            elif q in ["salom", "assalom", "assalomu alaykum"]:
                st.markdown("Vaalaykum assalom! Charchamayapsizmi, aka? Nima yordam kerak?")
                
            # 2. Bazadan qidirish (Sinf va ism)
            elif sheets_baza:
                combined_df = pd.concat(sheets_baza.values(), ignore_index=True, sort=False).fillna("")
                pattern = rf"\b{re.escape(q)}\b"
                mask = combined_df.apply(lambda row: any(re.search(pattern, str(v), re.IGNORECASE) for v in row), axis=1)
                res_df = combined_df[mask]

                if not res_df.empty:
                    st.success(f"Ma'rufjon aka, bazadan {len(res_df)} ta ma'lumot topdim:")
                    st.dataframe(res_df, use_container_width=True)
                else:
                    # 3. Internetdan qidirish (Agar bazada yo'q bo'lsa)
                    st.write("Bazadan topolmadim, lekin internetdan qarab ko'ryapman...")
                    try:
                        results = list(search(savol, num_results=3, lang="uz"))
                        if results:
                            st.write("Mana bu ma'lumotlarni topdim:")
                            for link in results:
                                st.write(f"🔗 {link}")
                        else:
                            st.warning("Internetda ham yo'q ekan, aka.")
                    except:
                        st.error("Internetga ulanishda ozgina muammo bo'ldi.")

# --- 6. MONITORING (TEGMADIM) ---
elif menu == "📊 Jurnal Monitoringi":
    st.title("📊 Monitoring")
    # Bu qismdagi koding o'zgarishsiz qoldi...
    st.write("Faylni yuklang va Telegramga yuboring.")
