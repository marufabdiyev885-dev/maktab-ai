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
    st.error(f"Secrets xatosi: {e}")
    st.stop()

# --- 2. EMAKTAB SUPER-SKANER FUNKSIYASI ---
def kundalik_hisobot_ol(login, parol, school_id):
    session = requests.Session()
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    
    try:
        # 1. Login
        session.get("https://login.emaktab.uz", headers=headers)
        res_login = session.post("https://login.emaktab.uz", data={"login": login, "password": parol}, headers=headers)
        
        if "logout" not in res_login.text.lower() and "chiqish" not in res_login.text.lower():
            return None, "❌ Login yoki parol xato!"

        # 2. Dinamik URLni aniqlash
        # Ba'zan report parametri o'zgarishi mumkin, shuning uchun bir nechta kombinatsiyani sinaymiz
        reports_to_try = ["paid-access-school", "management-paid-access-school"]
        years_to_try = [hozir.year, hozir.year - 1]

        for year in years_to_try:
            for rep_type in reports_to_try:
                url = f"https://schools.emaktab.uz/v2/reports/default?school={school_id}&report={rep_type}&year={year}"
                response = session.get(url, headers=headers)
                
                if response.status_code == 200:
                    soup = BeautifulSoup(response.content, 'html.parser')
                    rows_data = []
                    
                    # Jadvalni qidirish mantiqi
                    for tr in soup.find_all('tr'):
                        tds = tr.find_all(['td', 'th'])
                        if len(tds) >= 4:
                            c1 = tds[0].get_text(strip=True)
                            c4 = tds[3].get_text(strip=True)
                            
                            # Sinf nomini aniqlash (Raqam-Harf formatida)
                            if re.search(r'\d+-[A-ZА-Я]', c1):
                                rows_data.append([c1, c4])
                    
                    if rows_data:
                        df = pd.DataFrame(rows_data, columns=['Sinf nomi', 'Foiz (%)'])
                        return df, f"✅ {year}-yil ({rep_type}) ma'lumotlari yuklandi."
        
        return None, "❌ Hech qanday jadval topilmadi. Maktab ID yoki ruxsatnomani tekshiring."

    except Exception as e:
        return None, f"⚠️ Xatolik: {str(e)}"

# --- 3. LOGIN TIZIMI ---
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.title("🏫 " + MAKTAB_NOMI)
    p_in = st.text_input("Parol:", type="password")
    if st.button("Kirish"):
        if p_in == ASOSIY_PAROL:
            st.session_state.authenticated = True
            st.rerun()
        else: st.error("Parol xato!")
    st.stop()

# --- 4. SIDEBAR VA NAVIGATSIYA ---
menu = st.sidebar.radio("Menyu:", ["🤖 AI Muloqot", "📍 GPS Davomat", "📥 eMaktab Hisobot"])

if menu == "📍 GPS Davomat":
    st.title("📍 GPS Davomat")
    loc = get_geolocation()
    if loc:
        upos = (loc['coords']['latitude'], loc['coords']['longitude'])
        if geodesic(upos, MAKTAB_KOORDINATASI).km <= RUXSAT_ETILGAN_MASOFA:
            st.success("Siz maktab hududidasiz")
            fio = st.text_input("F.I.SH:")
            if st.button("Tasdiqlash") and fio:
                st.info(f"{fio} tizimga qayd etildi.")
        else: st.error("Maktab hududida emassiz!")

elif menu == "📥 eMaktab Hisobot":
    st.title("📥 Kundalik Ta'minlanganlik")
    c1, c2 = st.columns(2)
    with c1: 
        e_l = st.text_input("Login", value="marufabdiyev")
        e_p = st.text_input("Parol", type="password")
    with c2: 
        e_id = st.text_input("Maktab ID", value="1000001352999")
    
    if st.button("🔍 Jadvalni qidirish", use_container_width=True):
        with st.spinner("eMaktab tizimi skanerlanmoqda..."):
            res_df, msg = kundalik_hisobot_ol(e_l, e_p, e_id)
            if res_df is not None:
                st.session_state.em_df = res_df
                st.success(msg)
            else: st.error(msg)

    if "em_df" in st.session_state:
        st.divider()
        st.table(st.session_state.em_df)
        if st.button("📢 Telegramga yuborish"):
            txt = f"<b>📊 eMaktab Hisoboti</b>\n\n<pre>{st.session_state.em_df.to_string(index=False)}</pre>"
            requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", 
                         json={"chat_id": GURUH_ID, "text": txt, "parse_mode": "HTML"})
            st.success("Telegramga yuborildi!")
