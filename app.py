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

# --- ASOSIY SOZLAMALAR ---
MAKTAB_NOMI = "1-sonli umumta'lim maktabi"
ASOSIY_PAROL = "informatika2024"
MAKTAB_KOORDINATASI = (39.4955640, 64.7924960)

st.set_page_config(page_title=MAKTAB_NOMI, layout="wide")

uzb_tz = pytz.timezone('Asia/Tashkent')
hozir = dt.datetime.now(uzb_tz)

# Secrets
try:
    client = Groq(api_key=st.secrets["GROQ_API_KEY"])
    BOT_TOKEN = st.secrets["TELEGRAM_BOT_TOKEN"]
    GURUH_ID = st.secrets["TELEGRAM_GURUH_ID"]
except Exception as e:
    st.error(f"Secrets xatosi: {e}")
    st.stop()

# --- EMAKTAB KODINI TAHLIL QILISH ---
def emaktab_tahlil(login, parol, school_id):
    session = requests.Session()
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Referer': 'https://login.emaktab.uz/'
    }
    
    try:
        # 1. Login
        session.get("https://login.emaktab.uz", headers=headers)
        login_res = session.post("https://login.emaktab.uz", data={"login": login, "password": parol}, headers=headers)
        
        if "logout" not in login_res.text.lower() and "chiqish" not in login_res.text.lower():
            return None, "❌ Login yoki parol xato!"

        # 2. Hisobot sahifasi (Rasmda ko'rsatilgan manzil)
        url = f"https://schools.emaktab.uz/v2/reports/default?school={school_id}&report=paid-access-school&year=2025"
        resp = session.get(url, headers=headers)
        
        if resp.status_code != 200:
            return None, "🌐 Sahifani yuklab bo'lmadi."

        soup = BeautifulSoup(resp.content, 'html.parser')
        rows_data = []

        # 3. Jadval qatorlarini skanerlash
        # eMaktabda jadvallar odatda 'table.it-table' yoki 'table.grid' klassiga ega bo'ladi
        tables = soup.find_all('table')
        
        for table in tables:
            for tr in table.find_all('tr'):
                tds = tr.find_all(['td', 'th'])
                if len(tds) >= 4:
                    sinf = tds[0].get_text(strip=True)
                    foiz = tds[3].get_text(strip=True)
                    
                    # Sinf formati tekshiruvi: 1-A, 4-B, 11-A
                    if re.search(r'\d+-[A-ZА-Яa-zа-я]', sinf):
                        rows_data.append([sinf, foiz])

        if rows_data:
            df = pd.DataFrame(rows_data, columns=['Sinf', 'Kundalik %'])
            return df, "✅ Jadval muvaffaqiyatli olindi!"
        
        return None, "❌ Sahifada sinflar jadvali topilmadi. Login ruxsatini tekshiring."

    except Exception as e:
        return None, f"⚠️ Xatolik: {str(e)}"

# --- INTERFEYS ---
if "auth" not in st.session_state: st.session_state.auth = False
if not st.session_state.auth:
    st.title("🏫 " + MAKTAB_NOMI)
    if st.text_input("Parol:", type="password") == ASOSIY_PAROL:
        if st.button("Kirish"):
            st.session_state.auth = True
            st.rerun()
    st.stop()

menu = st.sidebar.radio("Menyu:", ["📥 eMaktab Hisobot", "📍 GPS Davomat", "🤖 AI Muloqot"])

if menu == "📥 eMaktab Hisobot":
    st.title("📥 Kundalikka kirish. Maktab")
    
    col1, col2 = st.columns(2)
    with col1:
        l = st.text_input("Login", value="marufabdiyev")
        p = st.text_input("Parol", type="password")
    with col2:
        sid = st.text_input("Maktab ID", value="1000001352999")
    
    if st.button("🔍 Hisobotni shakllantirish", use_container_width=True):
        with st.spinner("eMaktabdan jadval olinmoqda..."):
            df, msg = emaktab_tahlil(l, p, sid)
            if df is not None:
                st.session_state.final_df = df
                st.success(msg)
            else:
                st.error(msg)

    if "final_df" in st.session_state:
        st.divider()
        st.dataframe(st.session_state.final_df, height=600, use_container_width=True)
        
        if st.button("📢 Telegramga hisobotni yuborish"):
            text = f"<b>📊 Kundalikka kirish (2025-yil)</b>\n\n<pre>{st.session_state.final_df.to_string(index=False)}</pre>"
            requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", 
                         json={"chat_id": GURUH_ID, "text": text, "parse_mode": "HTML"})
            st.success("Yuborildi!")

elif menu == "📍 GPS Davomat":
    st.title("📍 GPS Davomat")
    loc = get_geolocation()
    if loc:
        upos = (loc['coords']['latitude'], loc['coords']['longitude'])
        dist = geodesic(upos, MAKTAB_KOORDINATASI).km
        if dist <= 1:
            st.success("Hududdasiz")
            if st.button("Keldini belgilash"): st.balloons()
        else:
            st.error(f"Tashqaridasiz! ({round(dist*1000)} m)")

elif menu == "🤖 AI Muloqot":
    st.title("🤖 AI Yordamchi")
    v = st.chat_input("Savol...")
    if v:
        res = client.chat.completions.create(messages=[{"role":"user","content":v}], model="llama-3.3-70b-versatile")
        st.markdown(res.choices[0].message.content)
