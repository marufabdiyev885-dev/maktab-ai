# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
import requests
import re
import io
import datetime as dt
import pytz
from groq import Groq
from streamlit_js_eval import get_geolocation
from geopy.distance import geodesic
from streamlit_gsheets import GSheetsConnection

# --- ASOSIY SOZLAMALAR ---
MAKTAB_NOMI = "1-sonli umumta'lim maktabi"
DIREKTOR_FIO = "Mahmudov Matyoqub Narzulloyevich"
ASOSIY_PAROL = "informatika2024"
MONITORING_KODI = "admin777"
MAKTAB_LAT, MAKTAB_LON = 39.4955640, 64.7924960
MAKTAB_KOORDINATASI = (MAKTAB_LAT, MAKTAB_LON)
RUXSAT_ETILGAN_MASOFA = 1 

st.set_page_config(page_title=MAKTAB_NOMI, layout="wide", page_icon="🏫")

# --- VAQT VA SECRETS ---
uzb_tz = pytz.timezone('Asia/Tashkent')
hozir = dt.datetime.now(uzb_tz)
hozirgi_vaqt = hozir.time()

try:
    BOT_TOKEN = st.secrets["TELEGRAM_BOT_TOKEN"]
    GURUH_ID = st.secrets["TELEGRAM_GURUH_ID"]
    GROQ_API_KEY = st.secrets["GROQ_API_KEY"]
    client = Groq(api_key=GROQ_API_KEY)
except Exception as e:
    st.error(f"Secrets xatosi: {e}")
    st.stop()

# --- EMAKTAB FUNKSIYASI ---
def emaktab_hisobot_yukla(login, parol, school_id):
    session = requests.Session()
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36'}
    try:
        session.get("https://login.emaktab.uz/", headers=headers)
        login_data = {"login": login, "password": parol}
        res = session.post("https://login.emaktab.uz/login", data=login_data, headers=headers)
        if "logout" not in res.text.lower() and "chiqish" not in res.text:
            return False, "Login yoki parol xato!"
        
        # Siz yuborgan skrinshot asosida yangilangan manzillar
        yil = 2025 # O'quv yili boshi
        url = f"https://schools.emaktab.uz/v2/reports/export?school={school_id}&report=paid-access-school&year={yil}&format=xlsx"
        headers['Referer'] = f"https://schools.emaktab.uz/v2/reports/default?school={school_id}&report=paid-access-school&year={yil}"
        
        fayl = session.get(url, headers=headers)
        if fayl.status_code == 200 and len(fayl.content) > 1000:
            return True, fayl.content
        return False, "Hisobotni yuklab bo'lmadi (404 yoki Ruxsat yo'q)."
    except Exception as e:
        return False, str(e)

# --- GOOGLE SHEETS FUNKSIYASI ---
def davomatni_gsheetsga_yoz(ism, holat):
    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        df = conn.read(ttl=0)
        yangi_qator = pd.DataFrame({"Sana": [hozir.strftime("%d.%m.%Y")], "Vaqt": [hozir.strftime("%H:%M:%S")], "F.I.SH": [ism], "Holat": [holat]})
        df = pd.concat([df, yangi_qator], ignore_index=True)
        conn.update(data=df)
        return True
    except: return False

# --- AUTH ---
if "authenticated" not in st.session_state: st.session_state.authenticated = False
if not st.session_state.authenticated:
    p_in = st.text_input("Kirish paroli:", type="password")
    if st.button("Kirish"):
        if p_in == ASOSIY_PAROL:
            st.session_state.authenticated = True
            st.rerun()
    st.stop()

# --- SIDEBAR ---
menu = st.sidebar.radio("Menyu:", ["🤖 AI Muloqot", "📊 Jurnal Monitoringi", "📍 GPS Davomat", "📥 eMaktab Hisobot"])

# --- BO'LIMLAR ---
if menu == "🤖 AI Muloqot":
    st.title("🤖 Maktab AI")
    # AI kodi shu yerda...

elif menu == "📊 Jurnal Monitoringi":
    st.title("📊 Jurnal Monitoringi")
    # Jurnal kodi shu yerda...

elif menu == "📍 GPS Davomat":
    st.title("📍 GPS Davomat")
    # GPS kodi shu yerda...

elif menu == "📥 eMaktab Hisobot":
    st.title("📥 eMaktab Operativ Hisoboti")
    if "emaktab_df" not in st.session_state: st.session_state.emaktab_df = None
    
    col1, col2 = st.columns(2)
    with col1:
        e_login = st.text_input("Login:", value="marufabdiyev")
        e_parol = st.text_input("Parol:", type="password")
    with col2:
        e_id = st.text_input("Maktab ID:", value="1000001352999")
        
    if st.button("🚀 Hisobotni olish"):
        ok, content = emaktab_hisobot_yukla(e_login, e_parol, e_id)
        if ok:
            try:
                df = pd.read_excel(io.BytesIO(content), skiprows=3)
                # Skrinshotdagi jadvalga moslash (Sinf va Foiz ustunlari)
                report_df = df.iloc[:, [0, 3]].dropna()
                report_df.columns = ['Sinf', 'Kirish %']
                st.session_state.emaktab_df = report_df
                st.session_state.emaktab_raw = content
                st.success("✅ Ma'lumotlar olindi!")
            except: st.error("Ma'lumotni o'qishda xato.")
        else: st.error(content)

    if st.session_state.emaktab_df is not None:
        st.table(st.session_state.emaktab_df)
        if st.button("📢 Telegramga yuborish"):
            f_obj = io.BytesIO(st.session_state.emaktab_raw)
            f_obj.name = "hisobot.xlsx"
            requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendDocument", 
                          data={"chat_id": GURUH_ID, "caption": "📊 eMaktab Hisoboti"}, 
                          files={"document": f_obj})
            st.success("Yuborildi!")
