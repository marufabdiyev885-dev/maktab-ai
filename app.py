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
    edge_options.add_argument("--headless")
    edge_options.add_argument("--no-sandbox")
    edge_options.add_argument("--disable-dev-shm-usage")
    
    try:
        service = Service(EdgeChromiumDriverManager().install())
        driver = webdriver.Edge(service=service, options=edge_options)
        
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

# --- YORDAMCHI FUNKSIYALAR ---
def davomatni_gsheetsga_yoz(ism, holat):
    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        df = conn.read(ttl=0)
        yangi = pd.DataFrame({
            "Sana": [hozir.strftime("%d.%m.%Y")],
            "Vaqt": [hozir.strftime("%H:%M:%S")],
            "F.I.SH": [ism],
            "Holat": [holat]
        })
        df = pd.concat([df, yangi], ignore_index=True)
        conn.update(data=df)
        return True
    except: return False

# --- LOG-IN VA SIDEBAR ---
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.title("🏫 " + MAKTAB_NOMI)
    p_in = st.text_input("Kirish paroli:", type="password")
    if st.button("Kirish", use_container_width=True):
        if p_in == ASOSIY_PAROL:
            st.session_state.authenticated = True
            st.rerun()
        else:
            st.error("Parol xato!")
    st.stop()

with st.sidebar:
    st.title("🏛 Boshqaruv")
    menu = st.radio("Bo'lim:", ["🤖 AI Muloqot", "📊 Jurnal Monitoringi", "📍 GPS Davomat", "📥 eMaktab Hisobot"])
    if st.button("🚪 Chiqish", use_container_width=True):
        st.session_state.clear()
        st.rerun()

# --- 1. AI MULOQOT (Tuzatilgan qavslar bilan) ---
if menu == "🤖 AI Muloqot":
    st.title("🤖 Maktab AI Yordamchisi")
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
    
    savol = st.chat_input("Savolingizni yozing...")
    if savol:
        st.session_state.messages.append({"role": "user", "content": savol})
        with st.chat_message("user"):
            st.markdown(savol)
        
        try:
            res = client.chat.completions.create(
                messages=[{"role": "system", "content": "Sen foydali yordamchisan."}] + st.session_state.messages[-5:],
                model="llama-3.3-70b-versatile"
            )
            ans = res.choices[0].message.content
            st.session_state.messages.append({"role": "assistant", "content": ans})
            with st.chat_message("assistant"):
                st.markdown(ans)
        except Exception as e:
            st.error(f"AI xatosi: {e}")

# --- 2. JURNAL MONITORINGI ---
elif menu == "📊 Jurnal Monitoringi":
    st.title("📊 Jurnal Monitoringi")
    j_fayl = st.file_uploader("Excel faylni yuklang", type=['xlsx', 'xls', 'html'])
    if j_fayl:
        try:
            df_j = pd.read_excel(j_fayl)
            st.dataframe(df_j, use_container_width=True)
            if st.button("📢 Telegramga yuborish"):
                st.success("Yuborildi!")
        except Exception as e:
            st.error(f"Faylni o'qishda xatolik: {e}")

# --- 3. GPS DAVOMAT ---
elif menu == "📍 GPS Davomat":
    st.title("📍 GPS Davomat")
    with st.spinner("🛰 GPS aniqlanmoqda..."):
        loc = get_geolocation()
    if loc:
        upos = (loc['coords']['latitude'], loc['coords']['longitude'])
        masofa = geodesic(upos, MAKTAB_KOORDINATASI).km
        if masofa <= RUXSAT_ETILGAN_MASOFA:
            st.success(f"📍 Hududdasiz ({round(masofa*1000)} m)")
            ism_f = st.text_input("F.I.SH (Ism-sharifingiz):")
            if st.button("Tasdiqlash", use_container_width=True):
                if ism_f and davomatni_gsheetsga_yoz(ism_f, "KELDI"):
                    st.balloons()
                    st.success("Davomat saqlandi!")
        else:
            st.error(f"Hududda emassiz! Masofa: {round(masofa*1000)} m")

# --- 4. EMAKTAB HISOBOT ---
elif menu == "📥 eMaktab Hisobot":
    st.title("📥 eMaktab Hisoboti")
    col1, col2 = st.columns(2)
    with col1:
        e_login = st.text_input("eMaktab login:", value="marufabdiyev")
        e_parol = st.text_input("eMaktab parol:", type="password")
    with col2:
        e_id = st.text_input("ID:", value="1000001352999")
        e_yil = st.selectbox("Yil:", [2025, 2026])

    if st.button("🔍 Hisobotni yangilash", use_container_width=True):
        with st.spinner("⏳ Edge orqali yuklanmoqda..."):
            df, msg, debug = kundalik_hisobot_ol_selenium(e_login, e_parol, e_id, e_yil)
            if df is not None:
                st.session_state.em_df = df
                st.dataframe(df, use_container_width=True)
            else:
                st.error(f"{msg}")
