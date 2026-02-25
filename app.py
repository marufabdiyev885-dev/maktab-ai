# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
import os
import requests
import re
import io
import time
import datetime as dt
import pytz
from groq import Groq
from streamlit_js_eval import get_geolocation
from geopy.distance import geodesic
from streamlit_gsheets import GSheetsConnection
from bs4 import BeautifulSoup

# Selenium Edge uchun kutubxonalar
from selenium import webdriver
from selenium.webdriver.edge.service import Service
from selenium.webdriver.edge.options import Options
from webdriver_manager.microsoft import EdgeChromiumDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Driver yuklashda SSL xatosini chetlab o'tish uchun (Offline xatosiga qarshi)
os.environ['WDM_SSL_VERIFY'] = '0'

# --- ASOSIY SOZLAMALAR ---
MAKTAB_NOMI = "1-sonli umumta'lim maktabi"
DIREKTOR_FIO = "Mahmudov Matyoqub Narzulloyevich"
ASOSIY_PAROL = "informatika2024"

MAKTAB_LAT, MAKTAB_LON = 39.4955640, 64.7924960
MAKTAB_KOORDINATASI = (MAKTAB_LAT, MAKTAB_LON)
RUXSAT_ETILGAN_MASOFA = 0.5 

st.set_page_config(page_title=MAKTAB_NOMI, layout="wide", page_icon="🏫")

# --- VAQT ---
try:
    uzb_tz = pytz.timezone('Asia/Tashkent')
    hozir = dt.datetime.now(uzb_tz)
except:
    hozir = dt.datetime.now()

# --- SECRETS ---
try:
    BOT_TOKEN = st.secrets["TELEGRAM_BOT_TOKEN"]
    GURUH_ID = st.secrets["TELEGRAM_GURUH_ID"]
    GROQ_API_KEY = st.secrets["GROQ_API_KEY"]
    client = Groq(api_key=GROQ_API_KEY)
except Exception as e:
    st.error("Secrets sozlamalari topilmadi!")
    st.stop()

# --- EDGE SELENIUM FUNKSIYASI ---
def kundalik_hisobot_ol_selenium(login, parol, school_id, yil):
    edge_options = Options()
    edge_options.add_argument("--headless")
    edge_options.add_argument("--no-sandbox")
    edge_options.add_argument("--disable-dev-shm-usage")
    edge_options.add_argument("--ignore-certificate-errors")
    edge_options.add_argument("--disable-ssl-tracker")
    
    try:
        # Driverni o'rnatish va ulanish
        with st.spinner("📦 Driver yuklanmoqda va ulanish o'rnatilmoqda..."):
            service = Service(EdgeChromiumDriverManager().install())
            driver = webdriver.Edge(service=service, options=edge_options)
        
        driver.set_page_load_timeout(40)
        driver.get("https://login.emaktab.uz")
        
        wait = WebDriverWait(driver, 25)
        
        # Login
        wait.until(EC.presence_of_element_located((By.NAME, "login"))).send_keys(login)
        driver.find_element(By.NAME, "password").send_keys(parol)
        driver.find_element(By.XPATH, "//input[@type='submit' or @value='Kirish']").click()
        
        time.sleep(5)
        if "login" in driver.current_url:
            driver.quit()
            return None, "🔒 Login yoki parol xato!"

        # Hisobot sahifasiga o'tish
        report_url = f"https://schools.emaktab.uz/v2/reports/default?school={school_id}&report=paid-access-school&year={yil}"
        driver.get(report_url)
        
        # Jadvalni kutish
        wait.until(EC.presence_of_element_located((By.TAG_NAME, "table")))
        time.sleep(3)
        
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        driver.quit()

        rows_data = []
        for table in soup.find_all('table'):
            for tr in table.find_all('tr'):
                tds = tr.find_all(['td', 'th'])
                if len(tds) >= 4:
                    c1 = tds[0].get_text(strip=True)
                    c2 = tds[1].get_text(strip=True)
                    c3 = tds[2].get_text(strip=True)
                    c4 = tds[3].get_text(strip=True)
                    if re.search(r'\d+-[A-ZА-Яa-zа-я]', c1):
                        rows_data.append([c1, c2, c3, c4])

        if rows_data:
            return pd.DataFrame(rows_data, columns=['Sinf', "O'quvchi soni", 'Kelmagan', 'Foiz (%)']), "OK"
        return None, "Ma'lumot topilmadi!"
        
    except Exception as e:
        if 'driver' in locals(): driver.quit()
        return None, f"⚠️ Ulanishda muammo: {str(e)}"

# --- INTERFEYS ---
if "auth" not in st.session_state: st.session_state.auth = False

if not st.session_state.auth:
    st.title("🏫 " + MAKTAB_NOMI)
    p_in = st.text_input("Parol:", type="password")
    if st.button("Kirish"):
        if p_in == ASOSIY_PAROL:
            st.session_state.auth = True
            st.rerun()
        else: st.error("Xato!")
    st.stop()

with st.sidebar:
    st.title("🏛 Menu")
    menu = st.radio("Tanlang:", ["🤖 AI Muloqot", "📊 Jurnal Monitoringi", "📍 GPS Davomat", "📥 eMaktab Hisobot"])
    if st.button("🚪 Chiqish"):
        st.session_state.clear()
        st.rerun()

# --- BO'LIMLAR ---
if menu == "🤖 AI Muloqot":
    st.title("🤖 AI Yordamchi")
    if "msgs" not in st.session_state: st.session_state.msgs = []
    for m in st.session_state.msgs:
        with st.chat_message(m["role"]): st.markdown(m["content"])
    
    u_inp = st.chat_input("Xabar...")
    if u_inp:
        st.session_state.msgs.append({"role": "user", "content": u_inp})
        with st.chat_message("user"): st.markdown(u_inp)
        res = client.chat.completions.create(messages=[{"role":"system","content":"Yordamchi"}] + st.session_state.msgs[-5:], model="llama-3.3-70b-versatile")
        ans = res.choices[0].message.content
        st.session_state.msgs.append({"role": "assistant", "content": ans})
        with st.chat_message("assistant"): st.markdown(ans)

elif menu == "📊 Jurnal Monitoringi":
    st.title("📊 Monitoring")
    f = st.file_uploader("Excel:", type=['xlsx'])
    if f: st.dataframe(pd.read_excel(f))

elif menu == "📍 GPS Davomat":
    st.title("📍 GPS Davomat")
    loc = get_geolocation()
    if loc:
        upos = (loc['coords']['latitude'], loc['coords']['longitude'])
        m = geodesic(upos, MAKTAB_KOORDINATASI).km
        if m <= RUXSAT_ETILGAN_MASOFA:
            st.success("Maktabdasiz")
            ism = st.text_input("F.I.SH:")
            if st.button("Tasdiqlash"): st.success("Saqlandi!")
        else: st.error(f"Uzoqdasiz: {round(m*1000)} m")

elif menu == "📥 eMaktab Hisobot":
    st.title("📥 eMaktab Hisoboti")
    c1, c2 = st.columns(2)
    with c1:
        l = st.text_input("Login:", value="marufabdiyev")
        p = st.text_input("Parol:", type="password")
    with c2:
        sid = st.text_input("ID:", value="1000001352999")
        yil = st.selectbox("Yil:", [2025, 2026])
    
    if st.button("🔍 Yangilash"):
        res_df, res_msg = kundalik_hisobot_ol_selenium(l, p, sid, yil)
        if res_df is not None:
            st.dataframe(res_df, use_container_width=True)
            st.success("Tayyor!")
        else:
            st.error(res_msg)
