# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
import os
import requests
import io
import datetime as dt
import pytz
from groq import Groq
from streamlit_js_eval import get_geolocation
from geopy.distance import geodesic
from streamlit_gsheets import GSheetsConnection
from bs4 import BeautifulSoup

# --- ASOSIY SOZLAMALAR ---
MAKTAB_NOMI = "1-sonli umumta'lim maktabi"
DIREKTOR_FIO = "Mahmudov Matyoqub Narzulloyevich"
ASOSIY_PAROL = "informatika2024"
MONITORING_KODI = "admin777"

# MAKTAB KOORDINATALARI (GPS)
MAKTAB_LAT = 39.4955640
MAKTAB_LON = 64.7924960
MAKTAB_KOORDINATASI = (MAKTAB_LAT, MAKTAB_LON)
RUXSAT_ETILGAN_MASOFA = 1 

st.set_page_config(page_title=MAKTAB_NOMI, layout="wide", page_icon="🏫")

# --- VAQT VA SECRETS ---
uzb_tz = pytz.timezone('Asia/Tashkent')
hozir = dt.datetime.now(uzb_tz)

try:
    BOT_TOKEN = st.secrets["TELEGRAM_BOT_TOKEN"]
    GURUH_ID = st.secrets["TELEGRAM_GURUH_ID"]
    GROQ_API_KEY = st.secrets["GROQ_API_KEY"]
    client = Groq(api_key=GROQ_API_KEY)
except Exception as e:
    st.error(f"Secrets sozlamalarida xatolik: {e}")
    st.stop()

# --- EMAKTAB API FUNKSIYASI ---
def emaktab_hisobot_yukla(login, parol, school_id):
    session = requests.Session()
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        session.get("https://login.emaktab.uz", headers=headers)
        login_data = {"login": login, "password": parol}
        res = session.post("https://login.emaktab.uz", data=login_data, headers=headers)
        if "logout" not in res.text.lower() and "chiqish" not in res.text.lower():
            return False, "Login xato!"
        view_url = f"https://schools.emaktab.uz/v2/reports/default?school={school_id}&report=paid-access-school&year=2025"
        response = session.get(view_url, headers=headers)
        if response.status_code == 200:
            return True, response.content
        return False, "Hisobotni olib bo'lmadi"
    except Exception as e:
        return False, str(e)

# --- GOOGLE SHEETSGA YOZISH (GPS uchun) ---
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
        st.error(f"Google Sheets xatosi: {e}")
        return False

# --- LOG-IN ---
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.title("🏫 " + MAKTAB_NOMI)
        p_in = st.text_input("Kirish paroli:", type="password", key="main_auth_key")
        if st.button("Kirish", use_container_width=True):
            if p_in == ASOSIY_PAROL:
                st.session_state.authenticated = True
                st.rerun()
            else: st.error("Parol xato!")
    st.stop()

# --- SIDEBAR ---
with st.sidebar:
    st.title("🏛 " + MAKTAB_NOMI)
    st.write(f"👤 **Direktor:** {DIREKTOR_FIO}")
    st.divider()
    menu = st.radio("Bo'limni tanlang:", [
        "🤖 AI Muloqot", 
        "📊 Jurnal Monitoringi", 
        "📍 GPS Davomat",
        "📥 eMaktab Hisobot"
    ])
    st.divider()
    if st.button("🚪 Chiqish", use_container_width=True):
        st.session_state.clear()
        st.rerun()

# --- AI MULOQOT (O'ZGARISHSIZ) ---
if menu == "🤖 AI Muloqot":
    st.title("🤖 Maktab AI Yordamchisi")
    if "messages" not in st.session_state: st.session_state.messages = []
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]): st.markdown(msg["content"])
    savol = st.chat_input("Savolingizni yozing...")
    if savol:
        st.session_state.messages.append({"role": "user", "content": savol})
        with st.chat_message("user"): st.markdown(savol)
        with st.chat_message("assistant"):
            try:
                res = client.chat.completions.create(
                    messages=[{"role": "system", "content": "Sen maktab yordamchisisan."}] + st.session_state.messages[-5:],
                    model="llama-3.3-70b-versatile",
                )
                ans = res.choices[0].message.content
                st.markdown(ans)
                st.session_state.messages.append({"role": "assistant", "content": ans})
            except: st.error("AI band.")

# --- JURNAL MONITORINGI (O'ZGARISHSIZ) ---
elif menu == "📊 Jurnal Monitoringi":
    st.title("📊 Jurnal Monitoringi")
    if "m_auth" not in st.session_state: st.session_state.m_auth = False
    if not st.session_state.m_auth:
        m_input = st.text_input("Monitoring kodi:", type="password", key="mon_input")
        if st.button("Kirish", key="mon_btn"):
            if m_input == MONITORING_KODI:
                st.session_state.m_auth = True
                st.rerun()
            else: st.error("Kod xato!")
        st.stop()
    
    j_fayl = st.file_uploader("Excel yuklang", type=['xlsx', 'xls', 'html'], key="uploader")
    if j_fayl:
        try:
            df_j = pd.read_excel(j_fayl)
            df_j.columns = [str(c).strip() for c in df_j.columns]
            st.dataframe(df_j, use_container_width=True)
        except Exception as e: st.error(f"Xato: {e}")

# --- GPS DAVOMAT (ASL HOLI) ---
elif menu == "📍 GPS Davomat":
    st.title("📍 GPS Davomat")
    bugun_sana = hozir.strftime("%d.%m.%Y")
    with st.spinner("🛰 GPS aniqlanmoqda..."):
        loc = get_geolocation()
    if loc and 'coords' in loc:
        upos = (loc['coords']['latitude'], loc['coords']['longitude'])
        masofa = geodesic(upos, MAKTAB_KOORDINATASI).km
        if masofa <= RUXSAT_ETILGAN_MASOFA:
            st.success(f"📍 Hududdasiz ({round(masofa*1000)} m)")
            ism = st.text_input("F.I.SH:").strip()
            if st.button("Tasdiqlash") and ism:
                if davomatni_gsheetsga_yoz(ism, "KELDI"):
                    st.success("✅ Saqlandi!")
                    st.balloons()
        else: st.error(f"Hududda emassiz! ({round(masofa*1000)} m)")

# --- EMAKTAB HISOBOT (RASMGA ASOSAN 7-QATORDAN O'QIYDIGAN TUZATILGAN QISM) ---
elif menu == "📥 eMaktab Hisobot":
    st.title("📥 eMaktab Operativ Hisoboti")
    if "em_df" not in st.session_state: st.session_state.em_df = None
    
    col1, col2 = st.columns(2)
    with col1:
        e_l, e_p = st.text_input("Login", value="marufabdiyev"), st.text_input("Parol", type="password")
    with col2:
        e_id = st.text_input("Maktab ID", value="1000001352999")
    
    if st.button("🔍 Hisobotni olish", use_container_width=True):
        ok, content = emaktab_hisobot_yukla(e_l, e_p, e_id)
        if ok:
            try:
                soup = BeautifulSoup(content, 'html.parser')
                tables = soup.find_all('table')
                if tables:
                    main_table_html = str(max(tables, key=lambda t: len(t.find_all('tr'))))
                    # Rasmda jadval 7-qator atrofida boshlangani uchun header=None qilib, keyin filtrlaymiz
                    df = pd.read_html(io.StringIO(main_table_html), header=None)[0]
                    
                    # 1-ustundan (index 0) "1-A" kabi sinf nomlarini qidiramiz
                    mask = df.iloc[:, 0].astype(str).str.contains('-', na=False)
                    df_final = df[mask].copy()
                    
                    if not df_final.empty:
                        # 0-ustun: Sinf nomi, 3-ustun: Foiz (rasmga qarab)
                        report = df_final.iloc[:, [0, 3]].copy()
                        report.columns = ['Sinf nomi', 'Kirish foizi (%)']
                        st.session_state.em_df = report
                        st.success("✅ Hisobot tayyor!")
                    else: st.error("Sinf ma'lumotlari topilmadi.")
                else: st.error("Jadval topilmadi.")
            except Exception as e: st.error(f"Tahlil xatosi: {e}")
        else: st.error(content)

    if st.session_state.em_df is not None:
        st.table(st.session_state.em_df)
        if st.button("📢 Telegramga yuborish"):
            msg = f"<b>📊 eMaktab ({hozir.strftime('%d.%m')})</b>\n\n<pre>{st.session_state.em_df.to_string(index=False)}</pre>"
            requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", json={"chat_id": GURUH_ID, "text": msg, "parse_mode": "HTML"})
            st.success("Yuborildi!")
