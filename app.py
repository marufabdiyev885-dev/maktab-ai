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

try:
    client = Groq(api_key=st.secrets["GROQ_API_KEY"])
    BOT_TOKEN = st.secrets["TELEGRAM_BOT_TOKEN"]
    GURUH_ID = st.secrets["TELEGRAM_GURUH_ID"]
except Exception as e:
    st.error(f"Secrets xatosi: {e}")
    st.stop()

# --- EMAKTAB SUPER SCANNER ---
def kundalik_hisobot_ol(login, parol, school_id):
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
            return None, "🔒 Login yoki parol xato!"

        # 2. Mumkin bo'lgan barcha hisobot linklarini sinash
        # Ba'zan 'v2', ba'zan 'v3' ishlaydi. Ba'zan 'paid-access-school' yoki shunchaki 'paid-access'
        report_types = ["paid-access-school", "paid-access", "school-paid-access"]
        years = [2025, 2026]
        
        for year in years:
            for rep in report_types:
                # v2 versiyani sinash
                url = f"https://schools.emaktab.uz/v2/reports/default?school={school_id}&report={rep}&year={year}"
                resp = session.get(url, headers=headers)
                
                if resp.status_code == 200:
                    soup = BeautifulSoup(resp.content, 'html.parser')
                    data = []
                    
                    # Sinf-Foiz juftligini qidirish
                    for tr in soup.find_all('tr'):
                        tds = tr.find_all(['td', 'th'])
                        if len(tds) >= 4:
                            c1 = tds[0].get_text(strip=True)
                            c4 = tds[3].get_text(strip=True)
                            # Sinf formati: 1-A, 4-B, 11-G
                            if re.search(r'\d+-[A-ZА-Яa-zа-я]', c1):
                                data.append([c1, c4])
                    
                    if data:
                        df = pd.DataFrame(data, columns=['Sinf nomi', 'Ta\'minlanganlik (%)'])
                        return df, f"✅ {year}-yilgi ({rep}) jadvali topildi!"

        return None, "❌ Hisobot topilmadi. Hisobot sahifasi bo'sh yoki sizga ruxsat berilmagan."

    except Exception as e:
        return None, f"⚠️ Tizim xatosi: {str(e)}"

# --- INTERFEYS ---
if "auth" not in st.session_state: st.session_state.auth = False
if not st.session_state.auth:
    st.title("🏫 " + MAKTAB_NOMI)
    if st.text_input("Kirish paroli:", type="password") == ASOSIY_PAROL:
        if st.button("Kirish"):
            st.session_state.auth = True
            st.rerun()
    st.stop()

menu = st.sidebar.radio("Menyu:", ["📥 eMaktab Hisobot", "📍 GPS Davomat", "🤖 AI Muloqot"])

if menu == "📥 eMaktab Hisobot":
    st.title("📥 Kundalik Ta'minlanganlik")
    c1, c2 = st.columns(2)
    with c1:
        l = st.text_input("Login", value="marufabdiyev")
        p = st.text_input("Parol", type="password")
    with c2:
        sid = st.text_input("Maktab ID", value="1000001352999")
    
    if st.button("🔍 Skanerlashni boshlash", use_container_width=True):
        with st.spinner("eMaktab tizimi bo'ylab hisobot qidirilmoqda..."):
            df, msg = kundalik_hisobot_ol(l, p, sid)
            if df is not None:
                st.session_state.em_df = df
                st.success(msg)
            else:
                st.error(msg)
                st.info("💡 Maslahat: eMaktabda 'marufabdiyev' profilida hisobotlar bo'limi ochiqligini tekshiring.")

    if "em_df" in st.session_state:
        st.divider()
        st.table(st.session_state.em_df)
        if st.button("📢 Telegramga yuborish"):
            txt = f"<b>📊 Kundalik Ta'minlanganlik</b>\n\n<pre>{st.session_state.em_df.to_string(index=False)}</pre>"
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
            st.success(f"Maktabdasiz ({round(dist*1000)} m)")
            fio = st.text_input("F.I.SH:")
            if st.button("Tasdiqlash") and fio:
                st.balloons()
        else:
            st.error(f"Maktab hududidan tashqaridasiz! Masofa: {round(dist*1000)} m")

elif menu == "🤖 AI Muloqot":
    st.title("🤖 AI Yordamchi")
    v = st.chat_input("Savol...")
    if v:
        res = client.chat.completions.create(messages=[{"role":"user","content":v}], model="llama-3.3-70b-versatile")
        st.write(res.choices[0].message.content)
