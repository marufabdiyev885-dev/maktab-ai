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

# --- 1. ASOSIY KONFIGURATSIYA ---
MAKTAB_NOMI = "1-sonli umumta'lim maktabi"
ASOSIY_PAROL = "informatika2024"
MAKTAB_KOORDINATASI = (39.4955640, 64.7924960)

st.set_page_config(page_title=MAKTAB_NOMI, layout="wide")

# Secrets tekshiruvi
try:
    BOT_TOKEN = st.secrets["TELEGRAM_BOT_TOKEN"]
    GURUH_ID = st.secrets["TELEGRAM_GURUH_ID"]
    client = Groq(api_key=st.secrets["GROQ_API_KEY"])
except Exception as e:
    st.error(f"Secrets xatosi: {e}")
    st.stop()

# --- 2. EMAKTABDAN MA'LUMOT OLISH (FINAL VARIANT) ---
def emaktab_hisobot_skaner(login, parol, school_id):
    session = requests.Session()
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Referer': 'https://login.emaktab.uz/'
    }
    
    try:
        # 1. Login jarayoni
        session.get("https://login.emaktab.uz", headers=headers)
        res_login = session.post("https://login.emaktab.uz", data={"login": login, "password": parol}, headers=headers)
        
        if "logout" not in res_login.text.lower() and "chiqish" not in res_login.text.lower():
            return None, "❌ Login yoki parol xato! Tizimga kirib bo'lmadi."

        # 2. Turli xil URL va yillarni sinab ko'rish
        # eMaktabda yil parametri 2025 yoki 2026 bo'lishi mumkin
        years = [2026, 2025]
        reports = ["paid-access-school", "management-paid-access-school"]
        
        for year in years:
            for rep in reports:
                url = f"https://schools.emaktab.uz/v2/reports/default?school={school_id}&report={rep}&year={year}"
                resp = session.get(url, headers=headers)
                
                if resp.status_code == 200:
                    soup = BeautifulSoup(resp.content, 'html.parser')
                    data = []
                    
                    # Jadval qatorlarini filtrlash
                    rows = soup.find_all('tr')
                    for row in rows:
                        cells = row.find_all(['td', 'th'])
                        if len(cells) >= 4:
                            # 1-ustun (Sinf) va 4-ustun (Foiz)
                            col1 = cells[0].get_text(strip=True)
                            col4 = cells[3].get_text(strip=True)
                            
                            # Regex orqali sinf nomini tekshirish (Masalan: 4-A, 11-B)
                            if re.search(r'\d+-[A-ZА-Я]', col1):
                                data.append([col1, col4])
                    
                    if data:
                        df = pd.DataFrame(data, columns=['Sinf nomi', 'Foiz (%)'])
                        return df, f"✅ {year}-yil uchun {rep} hisoboti topildi."
        
        return None, "❌ Hisobot topilmadi. Hisobot sahifasi bo'sh bo'lishi yoki sizga ruxsat berilmagan bo'lishi mumkin."

    except Exception as e:
        return None, f"⚠️ Xatolik: {str(e)}"

# --- 3. LOGIN TIZIMI ---
if "auth" not in st.session_state: st.session_state.auth = False

if not st.session_state.auth:
    st.title(MAKTAB_NOMI)
    p = st.text_input("Parol:", type="password")
    if st.button("Kirish") and p == ASOSIY_PAROL:
        st.session_state.auth = True
        st.rerun()
    st.stop()

# --- 4. MENYU ---
menu = st.sidebar.radio("Bo'lim:", ["🤖 AI Muloqot", "📍 GPS Davomat", "📥 eMaktab Hisobot"])

if menu == "📥 eMaktab Hisobot":
    st.title("📥 Kundalik Ta'minlanganlik")
    col1, col2 = st.columns(2)
    with col1:
        l = st.text_input("Login", value="marufabdiyev")
        p = st.text_input("Parol", type="password")
    with col2:
        sid = st.text_input("Maktab ID", value="1000001352999")
    
    if st.button("🔍 Ma'lumotlarni yangilash", use_container_width=True):
        with st.spinner("eMaktab tizimi tekshirilmoqda..."):
            df, msg = emaktab_hisobot_skaner(l, p, sid)
            if df is not None:
                st.session_state.last_df = df
                st.success(msg)
            else:
                st.error(msg)

    if "last_df" in st.session_state:
        st.dataframe(st.session_state.last_df, use_container_width=True)
        if st.button("📢 Telegramga yuborish"):
            txt = f"<b>📊 eMaktab Hisoboti</b>\n\n<pre>{st.session_state.last_df.to_string(index=False)}</pre>"
            requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", 
                         json={"chat_id": GURUH_ID, "text": txt, "parse_mode": "HTML"})
            st.success("Yuborildi!")

elif menu == "📍 GPS Davomat":
    st.title("📍 GPS Davomat")
    loc = get_geolocation()
    if loc:
        upos = (loc['coords']['latitude'], loc['coords']['longitude'])
        dist = geodesic(upos, MAKTAB_KOORDINATASI).km
        if dist <= 1:
            st.success("Maktab hududidasiz")
            ism = st.text_input("F.I.SH:")
            if st.button("Saqlash") and ism:
                st.balloons()
        else:
            st.error(f"Tashqaridasiz! ({round(dist*1000)} m)")

elif menu == "🤖 AI Muloqot":
    st.title("🤖 AI Yordamchi")
    v = st.chat_input("Savol...")
    if v:
        res = client.chat.completions.create(messages=[{"role":"user","content":v}], model="llama-3.3-70b-versatile")
        st.write(res.choices[0].message.content)
