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
from streamlit_gsheets import GSheetsConnection
from bs4 import BeautifulSoup

# --- 1. SOZLAMALAR ---
MAKTAB_NOMI = "1-sonli umumta'lim maktabi"
DIREKTOR_FIO = "Mahmudov Matyoqub Narzulloyevich"
ASOSIY_PAROL = "informatika2024"
MONITORING_KODI = "admin777"
MAKTAB_KOORDINATASI = (39.4955640, 64.7924960)
RUXSAT_ETILGAN_MASOFA = 1 

st.set_page_config(page_title=MAKTAB_NOMI, layout="wide", page_icon="🏫")

uzb_tz = pytz.timezone('Asia/Tashkent')
hozir = dt.datetime.now(uzb_tz)

try:
    BOT_TOKEN = st.secrets["TELEGRAM_BOT_TOKEN"]
    GURUH_ID = st.secrets["TELEGRAM_GURUH_ID"]
    client = Groq(api_key=st.secrets["GROQ_API_KEY"])
except Exception as e:
    st.error(f"Secrets xatosi: {e}")
    st.stop()

# --- 2. EMAKTAB UCHUN MAXSUS FUNKSIYA ---
def emaktab_tahlil(login, parol, school_id):
    session = requests.Session()
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
    try:
        # Kirish
        session.get("https://login.emaktab.uz", headers=headers)
        res = session.post("https://login.emaktab.uz", data={"login": login, "password": parol}, headers=headers)
        
        if "logout" not in res.text.lower() and "chiqish" not in res.text.lower():
            return None, "Login yoki parol xato!"

        # Hisobot sahifasini olish
        url = f"https://schools.emaktab.uz/v2/reports/default?school={school_id}&report=paid-access-school&year=2025"
        response = session.get(url, headers=headers)
        
        # HTMLni BeautifulSoup bilan "yuvish"
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # 1-usul: Standart jadval qidirish
        dfs = pd.read_html(io.StringIO(str(soup)))
        for df in dfs:
            if df.shape[1] >= 4:
                # Sinf ustunini topish (1-A kabi format)
                mask = df.iloc[:, 0].astype(str).str.contains(r'\d', na=False)
                if mask.any():
                    final = df[mask].iloc[:, [0, 3]].copy()
                    final.columns = ['Sinf nomi', 'Kirish foizi (%)']
                    return final, "OK"
        
        # 2-usul: Agar jadval tegi bo'lmasa, qatorlarni qo'lda qidirish
        rows = []
        for tr in soup.find_all('tr'):
            tds = tr.find_all('td')
            if len(tds) >= 4:
                sinf = tds[0].get_text(strip=True)
                foiz = tds[3].get_text(strip=True)
                if "-" in sinf and any(char.isdigit() for char in sinf):
                    rows.append([sinf, foiz])
        
        if rows:
            df_manual = pd.DataFrame(rows, columns=['Sinf nomi', 'Kirish foizi (%)'])
            return df_manual, "OK"
            
        return None, "Jadval strukturasini o'qib bo'lmadi."
    except Exception as e:
        return None, f"Xatolik: {str(e)}"

# --- 3. LOGIN TIZIMI ---
if "authenticated" not in st.session_state: st.session_state.authenticated = False
if not st.session_state.authenticated:
    p_in = st.text_input("Parol:", type="password")
    if st.button("Kirish") and p_in == ASOSIY_PAROL:
        st.session_state.authenticated = True
        st.rerun()
    st.stop()

# --- 4. SIDEBAR ---
menu = st.sidebar.radio("Bo'lim:", ["🤖 AI Muloqot", "📊 Jurnal Monitoringi", "📍 GPS Davomat", "📥 eMaktab Hisobot"])

# --- 5. BO'LIMLAR ---
if menu == "🤖 AI Muloqot":
    st.title("🤖 AI Yordamchi")
    savol = st.chat_input("Savol...")
    if savol:
        res = client.chat.completions.create(messages=[{"role": "user", "content": savol}], model="llama-3.3-70b-versatile")
        st.write(res.choices[0].message.content)

elif menu == "📊 Jurnal Monitoringi":
    st.title("📊 Monitoring")
    if st.text_input("Kod:", type="password") == MONITORING_KODI:
        f = st.file_uploader("Excel", type=['xlsx', 'xls'])
        if f: st.dataframe(pd.read_excel(f))

elif menu == "📍 GPS Davomat":
    st.title("📍 GPS Davomat")
    loc = get_geolocation()
    if loc:
        upos = (loc['coords']['latitude'], loc['coords']['longitude'])
        if geodesic(upos, MAKTAB_KOORDINATASI).km <= RUXSAT_ETILGAN_MASOFA:
            ism = st.text_input("F.I.SH:")
            if st.button("Tasdiqlash") and ism:
                st.success(f"{ism} saqlandi!")
        else: st.error("Hududdan tashqaridasiz!")

elif menu == "📥 eMaktab Hisobot":
    st.title("📥 eMaktab Hisoboti")
    l, p = st.text_input("Login", value="marufabdiyev"), st.text_input("Parol", type="password")
    mid = st.text_input("Maktab ID", value="1000001352999")
    
    if st.button("🔍 Yangilash"):
        df, msg = emaktab_tahlil(l, p, mid)
        if df is not None:
            st.session_state.em_df = df
            st.success("Ma'lumotlar olindi!")
        else: st.error(msg)

    if "em_df" in st.session_state:
        st.table(st.session_state.em_df)
        if st.button("📢 Telegramga"):
            txt = f"<b>📊 eMaktab ({hozir.strftime('%d.%m')})</b>\n<pre>{st.session_state.em_df.to_string(index=False)}</pre>"
            requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", json={"chat_id": GURUH_ID, "text": txt, "parse_mode": "HTML"})
            st.success("Yuborildi!")
