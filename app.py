# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
import os
import requests
import re
import io
import datetime as dt
import pytz
import time
from groq import Groq
from streamlit_js_eval import get_geolocation
from geopy.distance import geodesic
from streamlit_gsheets import GSheetsConnection
from bs4 import BeautifulSoup

# Selenium uchun kutubxonalar
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# --- ASOSIY SOZLAMALAR ---
MAKTAB_NOMI = "1-sonli umumta'lim maktabi"
DIREKTOR_FIO = "Mahmudov Matyoqub Narzulloyevich"
ASOSIY_PAROL = "informatika2024"
MONITORING_KODI = "admin777"

MAKTAB_LAT, MAKTAB_LON = 39.4955640, 64.7924960
MAKTAB_KOORDINATASI = (MAKTAB_LAT, MAKTAB_LON)
RUXSAT_ETILGAN_MASOFA = 1 

st.set_page_config(page_title=MAKTAB_NOMI, layout="wide", page_icon="🏫")

# --- VAQT VA API ---
uzb_tz = pytz.timezone('Asia/Tashkent')
hozir = dt.datetime.now(uzb_tz)
hozirgi_vaqt = hozir.time()

try:
    BOT_TOKEN = st.secrets["TELEGRAM_BOT_TOKEN"]
    GURUH_ID = st.secrets["TELEGRAM_GURUH_ID"]
    GROQ_API_KEY = st.secrets["GROQ_API_KEY"]
    client = Groq(api_key=GROQ_API_KEY)
except Exception as e:
    st.error("Secrets sozlamalarida xatolik!")
    st.stop()

# --- YANGI SELENIUM FUNKSIYASI ---
def kundalik_hisobot_ol_selenium(login, parol, school_id, yil):
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")

    try:
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        
        driver.get("https://login.emaktab.uz")
        wait = WebDriverWait(driver, 20)
        
        wait.until(EC.presence_of_element_located((By.NAME, "login"))).send_keys(login)
        driver.find_element(By.NAME, "password").send_keys(parol)
        driver.find_element(By.XPATH, "//input[@type='submit' or @value='Kirish']").click()
        
        time.sleep(3)
        if "login" in driver.current_url:
            driver.quit()
            return None, "🔒 Login yoki parol xato!", None

        url = f"https://schools.emaktab.uz/v2/reports/default?school={school_id}&report=paid-access-school&year={yil}"
        driver.get(url)
        wait.until(EC.presence_of_element_located((By.TAG_NAME, "table")))
        
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        driver.quit()

        rows_data = []
        for table in soup.find_all('table'):
            for tr in table.find_all('tr'):
                tds = tr.find_all(['td', 'th'])
                if len(tds) >= 4:
                    c1, c2, c3, c4 = [t.get_text(strip=True) for t in tds[:4]]
                    if re.search(r'\d+-[A-ZА-Яa-zа-я]', c1):
                        rows_data.append([c1, c2, c3, c4])

        if rows_data:
            return pd.DataFrame(rows_data, columns=['Sinf', "O'quvchi soni", 'Kelmagan', 'Foiz (%)']), "OK", None
        return None, "Jadval topilmadi", None
    except Exception as e:
        if 'driver' in locals(): driver.quit()
        return None, f"Xatolik: {str(e)}", None

# --- YORDAMCHI FUNKSIYALAR ---
def davomatni_gsheetsga_yoz(ism, holat):
    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        df = conn.read(ttl=0)
        yangi = pd.DataFrame({"Sana": [hozir.strftime("%d.%m.%Y")], "Vaqt": [hozir.strftime("%H:%M:%S")], "F.I.SH": [ism], "Holat": [holat]})
        df = pd.concat([df, yangi], ignore_index=True)
        conn.update(data=df)
        return True
    except: return False

# --- LOG-IN VA SIDEBAR ---
if "authenticated" not in st.session_state: st.session_state.authenticated = False
if not st.session_state.authenticated:
    p_in = st.text_input("Kirish paroli:", type="password")
    if st.button("Kirish"):
        if p_in == ASOSIY_PAROL:
            st.session_state.authenticated = True
            st.rerun()
    st.stop()

with st.sidebar:
    st.title("🏛 Boshqaruv")
    menu = st.radio("Bo'lim:", ["🤖 AI Muloqot", "📊 Jurnal Monitoringi", "📍 GPS Davomat", "📥 eMaktab Hisobot"])
    if st.button("🚪 Chiqish"):
        st.session_state.clear()
        st.rerun()

# --- BO'LIMLAR ---
if menu == "🤖 AI Muloqot":
    st.title("🤖 AI Yordamchi")
    if "messages" not in st.session_state: st.session_state.messages = []
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]): st.markdown(msg["content"])
    savol = st.chat_input("Savol...")
    if savol:
        st.session_state.messages.append({"role": "user", "content": savol})
        with st.chat_message("user"): st.markdown(savol)
        res = client.chat.completions.create(messages=[{"role":"system","content":"Maktab AI"}] + st.session_state.messages[-5:], model="llama-3.3-70b-versatile")
        ans = res.choices[0].message.content
        with st.chat_message("assistant"): st.markdown(ans)
        st.session_state.messages.append({"role": "assistant", "content": ans})

elif menu == "📊 Jurnal Monitoringi":
    st.title("📊 Jurnal Monitoringi")
    j_fayl = st.file_uploader("Excel yuklang", type=['xlsx', 'xls', 'html'])
    if j_fayl:
        df_j = pd.read_excel(j_fayl)
        st.dataframe(df_j)
        if st.button("📢 Telegramga"):
            st.success("Yuborildi!")

elif menu == "📍 GPS Davomat":
    st.title("📍 GPS Davomat")
    loc = get_geolocation()
    if loc:
        upos = (loc['coords']['latitude'], loc['coords']['longitude'])
        masofa = geodesic(upos, MAKTAB_KOORDINATASI).km
        if masofa <= RUXSAT_ETILGAN_MASOFA:
            ism = st.text_input("Ism:")
            if st.button("Tasdiqlash"):
                if davomatni_gsheetsga_yoz(ism, "KELDI"): st.success("Saqlandi!")
        else: st.error("Hududda emassiz")

elif menu == "📥 eMaktab Hisobot":
    st.title("📥 eMaktab Hisoboti")
    col1, col2 = st.columns(2)
    with col1:
        e_login = st.text_input("Login:", value="marufabdiyev")
        e_parol = st.text_input("Parol:", type="password")
    with col2:
        e_id = st.text_input("ID:", value="1000001352999")
        e_yil = st.selectbox("Yil:", [2025, 2026])

    if st.button("🔍 Olish"):
        df, msg, debug = kundalik_hisobot_ol_selenium(e_login, e_parol, e_id, e_yil)
        if df is not None:
            st.session_state.em_df = df
            st.dataframe(df)
        else: st.error(msg)
