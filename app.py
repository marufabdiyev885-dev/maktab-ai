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

# --- ASOSIY SOZLAMALAR ---
MAKTAB_NOMI = "1-sonli umumta'lim maktabi"
DIREKTOR_FIO = "Mahmudov Matyoqub Narzulloyevich"
ASOSIY_PAROL = "informatika2024"
MONITORING_KODI = "admin777"

# MAKTAB KOORDINATALARI
MAKTAB_LAT = 39.4955640
MAKTAB_LON = 64.7924960
MAKTAB_KOORDINATASI = (MAKTAB_LAT, MAKTAB_LON)
RUXSAT_ETILGAN_MASOFA = 0.5 # 500 metr

st.set_page_config(page_title=MAKTAB_NOMI, layout="wide", page_icon="🏫")

# --- O'ZBEKISTON VAQTINI OLISH ---
uzb_tz = pytz.timezone('Asia/Tashkent')
hozir = dt.datetime.now(uzb_tz)
hozirgi_vaqt = hozir.time()

# --- SECRETS TEKSHIRUVI ---
try:
    BOT_TOKEN = st.secrets["TELEGRAM_BOT_TOKEN"]
    GURUH_ID = st.secrets["TELEGRAM_GURUH_ID"]
    GROQ_API_KEY = st.secrets["GROQ_API_KEY"]
    client = Groq(api_key=GROQ_API_KEY)
except Exception as e:
    st.error(f"Secrets sozlamalarida xatolik: {e}")
    st.stop()

# --- EDGE SELENIUM HISOBOT FUNKSIYASI ---
def kundalik_hisobot_ol_selenium(login, parol, school_id, yil):
    edge_options = Options()
    edge_options.add_argument("--headless")  # Brauzer oynasiz ishlashi uchun
    edge_options.add_argument("--no-sandbox")
    edge_options.add_argument("--disable-dev-shm-usage")
    
    try:
        # Edge driverni avtomatik boshqarish
        service = Service(EdgeChromiumDriverManager().install())
        driver = webdriver.Edge(service=service, options=edge_options)
        
        # 1. Login sahifasi
        driver.get("https://login.emaktab.uz")
        wait = WebDriverWait(driver, 20)
        
        wait.until(EC.presence_of_element_located((By.NAME, "login"))).send_keys(login)
        driver.find_element(By.NAME, "password").send_keys(parol)
        driver.find_element(By.XPATH, "//input[@type='submit' or @value='Kirish']").click()
        
        time.sleep(3)
        if "login" in driver.current_url:
            driver.quit()
            return None, "🔒 Login yoki parol xato!", None

        # 2. Hisobot sahifasi
        url = f"https://schools.emaktab.uz/v2/reports/default?school={school_id}&report=paid-access-school&year={yil}"
        driver.get(url)
        
        # Jadval yuklanishini kutish
        wait.until(EC.presence_of_element_located((By.TAG_NAME, "table")))
        time.sleep(2) # JS to'liq ishlashi uchun
        
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
            df = pd.DataFrame(rows_data, columns=['Sinf', "O'quvchi soni", 'Kelmagan', 'Foiz (%)'])
            return df, "OK", None
        
        return None, "Jadval topilmadi", "Dinamik kontent yuklanmadi"

    except Exception as e:
        if 'driver' in locals(): driver.quit()
        return None, f"Edge Selenium xatosi: {str(e)}", None

# --- GOOGLE SHEETS FUNKSIYASI ---
def davomatni_gsheetsga_yoz(ism, holat):
    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        df = conn.read(ttl=0)
        yangi_qator = pd.DataFrame({
            "Sana": [hozir.strftime("%d.%m.%Y")],
            "Vaqt": [hozir.strftime("%H:%M:%S")],
            "F.I.SH": [ism],
            "Holat": [holat]
        })
        df = pd.concat([df, yangi_qator], ignore_index=True)
        conn.update(data=df)
        return True
    except Exception as e:
        st.error(f"GSheets xatosi: {e}")
        return False

# --- LOG-IN ---
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.title("🏫 " + MAKTAB_NOMI)
    p_in = st.text_input("Kirish paroli:", type="password")
    if st.button("Kirish"):
        if p_in == ASOSIY_PAROL:
            st.session_state.authenticated = True
            st.rerun()
        else: st.error("Parol xato!")
    st.stop()

# --- SIDEBAR ---
with st.sidebar:
    st.title("🏛 Boshqaruv Paneli")
    menu = st.radio("Bo'limni tanlang:", ["🤖 AI Muloqot", "📊 Jurnal Monitoringi", "📍 GPS Davomat", "📥 eMaktab Hisobot"])
    if st.button("🚪 Chiqish"):
        st.session_state.clear()
        st.rerun()

# --- 1. AI MULOQOT ---
if menu == "🤖 AI Muloqot":
    st.title("🤖 Maktab AI Yordamchisi")
    if "messages" not in st.session_state: st.session_state.messages = []
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]): st.markdown(msg["content"])
    
    savol = st.chat_input("Savolingizni yozing...")
    if savol:
        st.session_state.messages.append({"role": "user", "content": savol})
        with st.chat_message("user"): st.markdown(savol)
        res = client.chat.completions.create(
            messages=[{"role": "system", "content": "Sen maktab yordamchisisan."}] + st.session_state.messages[-5:],
            model="llama-3.3-70b-versatile",
        )
        ans = res.choices[0].message.content
        with st.chat_message("assistant"): st.markdown(ans)
        st.session_state.messages.append({"role":
