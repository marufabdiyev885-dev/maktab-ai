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
RUXSAT_ETILGAN_MASOFA = 0.5 

st.set_page_config(page_title=MAKTAB_NOMI, layout="wide", page_icon="🏫")

# --- O'ZBEKISTON VAQTINI OLISH ---
uzb_tz = pytz.timezone('Asia/Tengkent') # 'Asia/Tashkent' bo'lishi kerak, lekin tizim xatosi bo'lsa 'Asia/Tashkent' deb to'g'rilang
try:
    uzb_tz = pytz.timezone('Asia/Tashkent')
except:
    uzb_tz = pytz.utc
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

# --- EDGE SELENIUM HISOBOT FUNKSIYASI (Tuzatilgan) ---
def kundalik_hisobot_ol_selenium(login, parol, school_id, yil):
    edge_options = Options()
    edge_options.add_argument("--headless")
    edge_options.add_argument("--no-sandbox")
    edge_options.add_argument("--disable-dev-shm-usage")
    edge_options.add_argument("--ignore-certificate-errors")
    edge_options.add_argument("--disable-gpu")
    edge_options.add_argument("window-size=1920,1080")
    
    # SSL xatolarini chetlab o'tish uchun muhit o'zgaruvchisi
    os.environ['WDM_SSL_VERIFY'] = '0'
    
    try:
        # Driver menejeri orqali o'rnatish
        service = Service(EdgeChromiumDriverManager().install())
        driver = webdriver.Edge(service=service, options=edge_options)
        
        driver.get("https://login.emaktab.uz")
        wait = WebDriverWait(driver, 25)
        
        # Login jarayoni
        wait.until(EC.presence_of_element_located((By.NAME, "login"))).send_keys(login)
        driver.find_element(By.NAME, "password").send_keys(parol)
        driver.find_element(By.XPATH, "//input[@type='submit' or @value='Kirish']").click()
        
        time.sleep(4)
        if "login" in driver.current_url:
            driver.quit()
            return None, "🔒 Login yoki parol xato!", None

        # Hisobot sahifasi
        url = f"https://schools.emaktab.uz/v2/reports/default?school={school_id}&report=paid-access-school&year={yil}"
        driver.get(url)
        
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
            df = pd.DataFrame(rows_data, columns=['Sinf', "O'quvchi soni", 'Kelmagan', 'Foiz (%)'])
            return df, "OK", None
        return None, "Ma'lumot topilmadi", "Jadval bo'sh"
    except Exception as e:
        if 'driver' in locals(): driver.quit()
        return None, f"Ulanish xatosi: {str(e)}", "Offline rejim yoki blokirovka"

# --- QOLGAN FUNKSIYALAR (Davomat, Login, UI) ---

def davomatni_gsheetsga_yoz(ism, holat):
    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        df = conn.read(ttl=0)
        yangi = pd.DataFrame({"Sana": [hozir.strftime("%d.%m.%Y")], "Vaqt": [hozir.strftime("%H:%M:%S")], "F.I.SH": [ism], "Holat": [holat]})
        df = pd.concat([df, yangi], ignore_index=True)
        conn.update(data=df)
        return True
    except: return False

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.title("🏫 " + MAKTAB_NOMI)
    p_in = st.text_input("Kirish paroli:", type="password")
    if st.button("Kirish", use_container_width=True):
        if p_in == ASOSIY_PAROL:
            st.session_state.authenticated = True
            st.rerun()
        else: st.error("Parol xato!")
    st.stop()

with st.sidebar:
    st.title("🏛 Menu")
    menu = st.radio("Tanlang:", ["🤖 AI Muloqot", "📊 Jurnal Monitoringi", "📍 GPS Davomat", "📥 eMaktab Hisobot"])
    if st.button("🚪 Chiqish"):
        st.session_state.clear()
        st.rerun()

# BO'LIMLAR
if menu == "🤖 AI Muloqot":
    st.title("🤖 AI Yordamchi")
    if "messages" not in st.session_state: st.session_state.messages = []
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]): st.markdown(msg["content"])
    savol = st.chat_input("Savol...")
    if savol:
        st.session_state.messages.append({"role": "user", "content": savol})
        with st.chat_message("user"): st.markdown(savol)
        res = client.chat.completions.create(messages=[{"role":"system","content":"Yordamchi"}] + st.session_state.messages[-5:], model="llama-3.3-70b-versatile")
        ans = res.choices[0].message.content
        st.session_state.messages.append({"role": "assistant", "content": ans})
        with st.chat_message("assistant"): st.markdown(ans)

elif menu == "📊 Jurnal Monitoringi":
    st.title("📊 Monitoring")
    j_fayl = st.file_uploader("Faylni yuklang", type=['xlsx', 'xls'])
    if j_fayl:
        st.dataframe(pd.read_excel(j_fayl), use_container_width=True)

elif menu == "📍 GPS Davomat":
    st.title("📍 GPS Davomat")
    loc = get_geolocation()
    if loc:
        upos = (loc['coords']['latitude'], loc['coords']['longitude'])
        masofa = geodesic(upos, MAKTAB_KOORDINATASI).km
        if masofa <= RUXSAT_ETILGAN_MASOFA:
            ism = st.text_input("Ism:")
            if st.button("Tasdiqlash"):
                if ism and davomatni_gsheetsga_yoz(ism, "OK"): st.success("Saqlandi!")
        else: st.error(f"Hududda emassiz: {round(masofa*1000)} m")

elif menu == "📥 eMaktab Hisobot":
    st.title("📥 eMaktab Hisoboti")
    e_login = st.text_input("Login:", value="marufabdiyev")
    e_parol = st.text_input("Parol:", type="password")
    e_id = st.text_input("Maktab ID:", value="1000001352999")
    if st.button("🔍 Hisobotni yangilash"):
        with st.spinner("⏳ Edge ishga tushmoqda..."):
            df, msg, debug = kundalik_hisobot_ol_selenium(e_login, e_parol, e_id, 2025)
            if df is not None:
                st.dataframe(df, use_container_width=True)
            else: st.error(f"{msg} | {debug}")
