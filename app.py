# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
import requests
import io
import datetime as dt
import pytz
from groq import Groq
from streamlit_js_eval import get_geolocation
from geopy.distance import geodesic
from streamlit_gsheets import GSheetsConnection
from bs4 import BeautifulSoup
import re

# --- 1. SOZLAMALAR ---
MAKTAB_NOMI = "1-sonli umumta'lim maktabi"
DIREKTOR_FIO = "Mahmudov Matyoqub Narzulloyevich"
ASOSIY_PAROL = "informatika2024"
MONITORING_KODI = "admin777"
MAKTAB_KOORDINATASI = (39.4955640, 64.7924960)
RUXSAT_ETILGAN_MASOFA = 1 

st.set_page_config(page_title=MAKTAB_NOMI, layout="wide", page_icon="🏫")

uzb_tz = pytz.timezone('Asia/Tashkent')
hozir = dt.datetime.now(uzb_tz)

try:
    client = Groq(api_key=st.secrets["GROQ_API_KEY"])
    BOT_TOKEN = st.secrets["TELEGRAM_BOT_TOKEN"]
    GURUH_ID = st.secrets["TELEGRAM_GURUH_ID"]
except Exception as e:
    st.error(f"Secrets sozlamalarida xatolik: {e}")
    st.stop()

# --- 2. EMAKTAB UNIVERSAL TAHLIL ---
def kundalik_hisobot_ol(login, parol, school_id):
    session = requests.Session()
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    
    try:
        # Login jarayoni
        session.get("https://login.emaktab.uz", headers=headers)
        res_login = session.post("https://login.emaktab.uz", data={"login": login, "password": parol}, headers=headers)
        
        if "logout" not in res_login.text.lower() and "chiqish" not in res_login.text.lower():
            return None, "Login yoki parol xato!"

        # 2026 va 2025 yillarni ketma-ket tekshirish
        for test_year in [2026, 2025]:
            url = f"https://schools.emaktab.uz/v2/reports/default?school={school_id}&report=paid-access-school&year={test_year}"
            response = session.get(url, headers=headers)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                rows_data = []
                
                # Barcha qatorlarni titib chiqish
                for tr in soup.find_all('tr'):
                    tds = tr.find_all(['td', 'th'])
                    if len(tds) >= 4:
                        txt1 = tds[0].get_text(strip=True)
                        txt4 = tds[3].get_text(strip=True)
                        
                        # Regex: 1-A, 10-B kabi sinf formatini qidirish
                        if re.search(r'\d+-[A-ZА-Я]', txt1):
                            rows_data.append([txt1, txt4])
                
                if rows_data:
                    df = pd.DataFrame(rows_data, columns=['Sinf nomi', 'Foiz (%)'])
                    return df, f"{test_year}-yil ma'lumotlari olindi"
        
        return None, "Hech qaysi yildan ma'lumot topilmadi (ID yoki hisobot turi xato)."

    except Exception as e:
        return None, f"Xatolik: {str(e)}"

# --- 3. LOGIN ---
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.title("🏫 " + MAKTAB_NOMI)
    if st.text_input("Parol:", type="password") == ASOSIY_PAROL:
        if st.button("Kirish"):
            st.session_state.authenticated = True
            st.rerun()
    st.stop()

# --- 4. ASOSIY INTERFEYS ---
menu = st.sidebar.radio("Menyu:", ["🤖 AI Muloqot", "📍 GPS Davomat", "📥 eMaktab Hisobot"])

if menu == "📍 GPS Davomat":
    st.title("📍 GPS Davomat")
    loc = get_geolocation()
    if loc:
        upos = (loc['coords']['latitude'], loc['coords']['longitude'])
        if geodesic(upos, MAKTAB_KOORDINATASI).km <= RUXSAT_ETILGAN_MASOFA:
            st.success("Maktab hududidasiz")
            fio = st.text_input("F.I.SH:")
            if st.button("Saqlash") and fio:
                st.info(f"{fio} kiritildi")
        else:
            st.error("Maktab hududidan tashqaridasiz")

elif menu == "📥 eMaktab Hisobot":
    st.title("📥 Kundalik Ta'minlanganlik")
    c1, c2 = st.columns(2)
    with c1: l = st.text_input("Login", value="marufabdiyev")
    with c1: p = st.text_input("Parol", type="password")
    with c2: mid = st.text_input("Maktab ID", value="1000001352999")
    
    if st.button("🔍 Hisobotni yangilash", use_container_width=True):
        res_df, msg = kundalik_hisobot_ol(l, p, mid)
        if res_df is not None:
            st.session_state.em_df = res_df
            st.success(msg)
        else:
            st.error(msg)

    if "em_df" in st.session_state:
        st.table(st.session_state.em_df)
        if st.button("📢 Telegramga yuborish"):
            txt = f"<b>📊 eMaktab Hisoboti</b>\n\n<pre>{st.session_state.em_df.to_string(index=False)}</pre>"
            requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", 
                         json={"chat_id": GURUH_ID, "text": txt, "parse_mode": "HTML"})
            st.success("Yuborildi!")
