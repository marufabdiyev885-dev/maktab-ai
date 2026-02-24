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

# --- 1. ASOSIY SOZLAMALAR ---
MAKTAB_NOMI = "1-sonli umumta'lim maktabi"
DIREKTOR_FIO = "Mahmudov Matyoqub Narzulloyevich"
ASOSIY_PAROL = "informatika2024"
MONITORING_KODI = "admin777"
MAKTAB_KOORDINATASI = (39.4955640, 64.7924960)
RUXSAT_ETILGAN_MASOFA = 1 

st.set_page_config(page_title=MAKTAB_NOMI, layout="wide", page_icon="🏫")

# Vaqt
uzb_tz = pytz.timezone('Asia/Tashkent')
hozir = dt.datetime.now(uzb_tz)

try:
    BOT_TOKEN = st.secrets["TELEGRAM_BOT_TOKEN"]
    GURUH_ID = st.secrets["TELEGRAM_GURUH_ID"]
    client = Groq(api_key=st.secrets["GROQ_API_KEY"])
except Exception as e:
    st.error(f"Secrets xatosi: {e}")
    st.stop()

# --- 2. EMAKTAB UCHUN MUKAMMAL QIDIRUVCHISI ---
def kundalik_hisobot_ol(login, parol, school_id):
    session = requests.Session()
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
        'Accept-Language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
        'Referer': 'https://login.emaktab.uz/'
    }
    try:
        # 1. Login
        session.get("https://login.emaktab.uz", headers=headers)
        res_login = session.post("https://login.emaktab.uz", data={"login": login, "password": parol}, headers=headers)
        
        if "logout" not in res_login.text.lower() and "chiqish" not in res_login.text.lower():
            return None, "🔒 Login yoki parol xato! Tizimga kirib bo'lmadi."

        # 2. Hisobot sahifasini yuklash
        # 2026-yil bo'lgani uchun yilni dinamik olamiz
        year = hozir.year
        url = f"https://schools.emaktab.uz/v2/reports/default?school={school_id}&report=paid-access-school&year={year}"
        response = session.get(url, headers=headers)
        
        if response.status_code != 200:
            return None, f"🌐 Sahifa ochilmadi (Status: {response.status_code})"

        soup = BeautifulSoup(response.content, 'html.parser')
        rows_data = []

        # 3. AQLLI JADVAL QIDIRISH (Har qanday formatda)
        # Barcha qatorlarni (tr) qidiramiz
        for tr in soup.find_all('tr'):
            tds = tr.find_all(['td', 'th'])
            if len(tds) >= 4:
                # Birinchi va to'rtinchi ustun matnini olamiz
                col1 = tds[0].get_text(strip=True)
                col4 = tds[3].get_text(strip=True)
                
                # Sinf formatini tekshirish (Masalan: 1-A, 11-B, 4-G)
                # Regex: Raqam + chiziq + harf
                if re.search(r'\d+-[A-ZА-Я]', col1):
                    rows_data.append([col1, col4])

        if rows_data:
            df = pd.DataFrame(rows_data, columns=['Sinf nomi', 'Foiz (%)'])
            return df, "OK"
        
        # 4. Agar yuqoridagilar o'xshamasa, pandas read_html (so'nggi chora)
        try:
            dfs = pd.read_html(io.StringIO(str(soup)))
            for d in dfs:
                if d.shape[1] >= 4:
                    mask = d.iloc[:, 0].astype(str).str.contains(r'\d-', na=False)
                    if mask.any():
                        res = d[mask].iloc[:, [0, 3]].copy()
                        res.columns = ['Sinf nomi', 'Foiz (%)']
                        return res, "OK"
        except:
            pass

        return None, "❌ Ma'lumot topilmadi. Hisobot sahifasi bo'sh yoki ID noto'g'ri."

    except Exception as e:
        return None, f"⚠️ Xatolik: {str(e)}"

# --- 3. ILOVA QISMI ---
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.title("🏫 " + MAKTAB_NOMI)
    if st.text_input("Parol:", type="password") == ASOSIY_PAROL:
        if st.button("Kirish"):
            st.session_state.authenticated = True
            st.rerun()
    st.stop()

menu = st.sidebar.radio("Menyu:", ["🤖 AI Muloqot", "📍 GPS Davomat", "📥 eMaktab Hisobot"])

if menu == "📍 GPS Davomat":
    st.title("📍 GPS Davomat")
    loc = get_geolocation()
    if loc:
        upos = (loc['coords']['latitude'], loc['coords']['longitude'])
        dist = geodesic(upos, MAKTAB_KOORDINATASI).km
        if dist <= RUXSAT_ETILGAN_MASOFA:
            st.success(f"Maktabdasiz ({round(dist*1000)}m)")
            ism = st.text_input("F.I.SH:")
            if st.button("Saqlash") and ism:
                st.info(f"{ism} saqlandi (Test)")
        else:
            st.error("Maktab hududida emassiz!")

elif menu == "📥 eMaktab Hisobot":
    st.title("📥 Kundalik Ta'minlanganlik")
    c1, c2 = st.columns(2)
    with c1: l = st.text_input("Login", value="marufabdiyev")
    with c1: p = st.text_input("Parol", type="password")
    with c2: mid = st.text_input("Maktab ID", value="1000001352999")
    
    if st.button("🔄 Yangilash"):
        df, msg = kundalik_hisobot_ol(l, p, mid)
        if df is not None:
            st.session_state.em_df = df
            st.success("Hisobot olindi!")
        else:
            st.error(msg)

    if "em_df" in st.session_state:
        st.table(st.session_state.em_df)
        if st.button("📢 Telegramga"):
            txt = f"<b>📊 Kundalik ta'minlanganlik ({hozir.strftime('%d.%m.%Y')})</b>\n\n<pre>{st.session_state.em_df.to_string(index=False)}</pre>"
            requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", json={"chat_id": GURUH_ID, "text": txt, "parse_mode": "HTML"})
            st.success("Yuborildi!")
