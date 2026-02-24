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
from bs4 import BeautifulSoup
import re

# --- 1. SOZLAMALAR ---
MAKTAB_NOMI = "1-sonli umumta'lim maktabi"
ASOSIY_PAROL = "informatika2024"
MAKTAB_KOORDINATASI = (39.4955640, 64.7924960)

st.set_page_config(page_title=MAKTAB_NOMI, layout="wide", page_icon="🏫")

# Vaqt va Secrets
uzb_tz = pytz.timezone('Asia/Tashkent')
hozir = dt.datetime.now(uzb_tz)

try:
    client = Groq(api_key=st.secrets["GROQ_API_KEY"])
    BOT_TOKEN = st.secrets["TELEGRAM_BOT_TOKEN"]
    GURUH_ID = st.secrets["TELEGRAM_GURUH_ID"]
except Exception as e:
    st.error(f"Secrets sozlamalarida xatolik: {e}")
    st.stop()

# --- 2. EMAKTAB TAHLIL FUNKSIYASI ---
def kundalik_hisobot_ol(login, parol, school_id, yil):
    session = requests.Session()
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Referer': 'https://login.emaktab.uz/'
    }
    try:
        # 1. Login
        session.get("https://login.emaktab.uz", headers=headers)
        res_login = session.post("https://login.emaktab.uz", data={"login": login, "password": parol}, headers=headers)
        
        if "logout" not in res_login.text.lower() and "chiqish" not in res_login.text.lower():
            return None, "🔒 Login yoki parol xato!", None

        # 2. Hisobotni yuklash
        url = f"https://schools.emaktab.uz/v2/reports/default?school={school_id}&report=paid-access-school&year={yil}"
        response = session.get(url, headers=headers)
        
        if response.status_code != 200:
            return None, f"🌐 Sahifa ochilmadi (Status: {response.status_code})", None

        soup = BeautifulSoup(response.content, 'html.parser')
        
        # 3. Ma'lumotni qidirish
        rows_data = []
        # Sahifadagi barcha jadvallarni tekshirish
        tables = soup.find_all('table')
        
        for table in tables:
            for tr in table.find_all('tr'):
                tds = tr.find_all(['td', 'th'])
                if len(tds) >= 4:
                    c1 = tds[0].get_text(strip=True)
                    c4 = tds[3].get_text(strip=True)
                    # Sinf formati (Masalan: 4-B yoki 10-A)
                    if re.search(r'\d+-[A-ZА-Яa-zа-я]', c1):
                        rows_data.append([c1, c4])

        if rows_data:
            df = pd.DataFrame(rows_data, columns=['Sinf nomi', 'Foiz (%)'])
            return df, "OK", None
        else:
            # Debug uchun sahifa sarlavhasini qaytarish
            title = soup.title.string if soup.title else "Sarlavha topilmadi"
            return None, "Jadval topilmadi", title

    except Exception as e:
        return None, f"Xatolik: {str(e)}", None

# --- 3. LOGIN TIZIMI ---
if "auth" not in st.session_state: st.session_state.auth = False
if not st.session_state.auth:
    st.title("🏫 " + MAKTAB_NOMI)
    if st.text_input("Parol:", type="password") == ASOSIY_PAROL:
        if st.button("Kirish"):
            st.session_state.auth = True
            st.rerun()
    st.stop()

# --- 4. ASOSIY QISM ---
menu = st.sidebar.radio("Menyu:", ["📥 eMaktab Hisobot", "📍 GPS Davomat", "🤖 AI Muloqot"])

if menu == "📥 eMaktab Hisobot":
    st.title("📥 Kundalik Ta'minlanganlik")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        l = st.text_input("Login", value="marufabdiyev")
        p = st.text_input("Parol", type="password")
    with col2:
        sid = st.text_input("Maktab ID", value="1000001352999")
        yil_tanlov = st.selectbox("O'quv yili:", [2025, 2026], index=0)
    with col3:
        st.info("Eslatma: Agar 2026-yil bo'sh bo'lsa, 2025-yilni tanlab ko'ring.")

    if st.button("🔍 Hisobotni yangilash", use_container_width=True):
        with st.spinner("eMaktab tizimi tekshirilmoqda..."):
            df, msg, debug_info = kundalik_hisobot_ol(l, p, sid, yil_tanlov)
            if df is not None:
                st.session_state.em_df = df
                st.success(f"✅ {yil_tanlov}-yil ma'lumotlari yuklandi!")
            else:
                st.error(f"❌ {msg}")
                if debug_info:
                    st.warning(f"Sahifa sarlavhasi: {debug_info}. (Bu sahifada jadval yo'qligini bildiradi)")

    if "em_df" in st.session_state:
        st.table(st.session_state.em_df)
        if st.button("📢 Telegramga yuborish"):
            txt = f"<b>📊 eMaktab ({yil_tanlov}-yil)</b>\n\n<pre>{st.session_state.em_df.to_string(index=False)}</pre>"
            requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", 
                         json={"chat_id": GURUH_ID, "text": txt, "parse_mode": "HTML"})
            st.success("Telegramga yuborildi!")

elif menu == "📍 GPS Davomat":
    st.title("📍 GPS Davomat")
    loc = get_geolocation()
    if loc:
        upos = (loc['coords']['latitude'], loc['coords']['longitude'])
        dist = geodesic(upos, MAKTAB_KOORDINATASI).km
        if dist <= 1:
            st.success("Maktabdasiz")
            fio = st.text_input("F.I.SH:")
            if st.button("Tasdiqlash") and fio:
                st.info(f"{fio} saqlandi.")
        else:
            st.error(f"Maktab hududidan tashqaridasiz! ({round(dist*1000)} m)")

elif menu == "🤖 AI Muloqot":
    st.title("🤖 AI Yordamchi")
    v = st.chat_input("Savol...")
    if v:
        res = client.chat.completions.create(messages=[{"role":"user","content":v}], model="llama-3.3-70b-versatile")
        st.write(res.choices[0].message.content)
