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

# --- 1. ASOSIY SOZLAMALAR ---
MAKTAB_NOMI = "1-sonli umumta'lim maktabi"
DIREKTOR_FIO = "Mahmudov Matyoqub Narzulloyevich"
ASOSIY_PAROL = "informatika2024"
MONITORING_KODI = "admin777"
MAKTAB_KOORDINATASI = (39.4955640, 64.7924960)
RUXSAT_ETILGAN_MASOFA = 1 

st.set_page_config(page_title=MAKTAB_NOMI, layout="wide", page_icon="🏫")

# Vaqt va Secrets
uzb_tz = pytz.timezone('Asia/Tashkent')
hozir = dt.datetime.now(uzb_tz)

try:
    BOT_TOKEN = st.secrets["TELEGRAM_BOT_TOKEN"]
    GURUH_ID = st.secrets["TELEGRAM_GURUH_ID"]
    client = Groq(api_key=st.secrets["GROQ_API_KEY"])
except Exception as e:
    st.error(f"Secrets xatosi: {e}")
    st.stop()

# --- 2. EMAKTAB TAHLIL FUNKSIYASI ---
def kundalik_hisobot_ol(login, parol, school_id):
    session = requests.Session()
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
        'Referer': 'https://login.emaktab.uz/'
    }
    try:
        # Kirish
        session.get("https://login.emaktab.uz", headers=headers)
        res = session.post("https://login.emaktab.uz", data={"login": login, "password": parol}, headers=headers)
        
        if "logout" not in res.text.lower() and "chiqish" not in res.text.lower():
            return None, "Login yoki parol noto'g'ri!"

        # Kundalik ta'minlanganlik URL (paid-access-school)
        # BU YERDA YILNI TEKSHIRING: 2025 yoki 2026? Hozirgi yilga mosladim.
        current_year = hozir.year
        url = f"https://schools.emaktab.uz/v2/reports/default?school={school_id}&report=paid-access-school&year={current_year}"
        
        response = session.get(url, headers=headers)
        if response.status_code != 200:
            return None, f"Sahifa ochilmadi. Status: {response.status_code}"

        soup = BeautifulSoup(response.content, 'html.parser')
        
        # 1-usul: Barcha 'table' teglarini tekshirish
        tables = pd.read_html(io.StringIO(str(soup)))
        
        if tables:
            for df in tables:
                # Agar jadvalda "Sinf" yoki "Класс" so'zi bo'lsa
                df_str = str(df.values)
                if "Sinf" in df_str or "Класс" in df_str or "-" in df_str:
                    # Rasmga asosan: 7-qatorda sarlavhalar boshlanadi
                    # Bizga 0-ustun (Sinf) va 3-ustun (Foiz) kerak
                    # NaN qiymatlarni olib tashlaymiz va sinf formatini qidiramiz
                    mask = df.iloc[:, 0].astype(str).str.contains('-', na=False)
                    final_df = df[mask].iloc[:, [0, 3]].copy()
                    final_df.columns = ['Sinf nomi', 'Ta\'minlanganlik (%)']
                    return final_df, "OK"
        
        # 2-usul: BeautifulSoup orqali qo'lda yig'ish (Jadval topilmasa)
        rows = []
        for tr in soup.find_all('tr'):
            tds = tr.find_all('td')
            if len(tds) >= 4:
                s_text = tds[0].get_text(strip=True)
                f_text = tds[3].get_text(strip=True)
                if "-" in s_text and any(c.isdigit() for c in s_text):
                    rows.append([s_text, f_text])
        
        if rows:
            return pd.DataFrame(rows, columns=['Sinf nomi', 'Ta\'minlanganlik (%)']), "OK"
            
        return None, "Jadval topilmadi. Maktab ID yoki hisobot turi noto'g'ri bo'lishi mumkin."

    except Exception as e:
        return None, f"Xatolik: {str(e)}"

# --- 3. LOGIN TIZIMI ---
if "authenticated" not in st.session_state: st.session_state.authenticated = False
if not st.session_state.authenticated:
    st.title("🏫 " + MAKTAB_NOMI)
    p_in = st.text_input("Parol:", type="password")
    if st.button("Kirish") and p_in == ASOSIY_PAROL:
        st.session_state.authenticated = True
        st.rerun()
    st.stop()

# --- 4. SIDEBAR ---
menu = st.sidebar.radio("Bo'lim:", ["🤖 AI Muloqot", "📊 Jurnal Monitoringi", "📍 GPS Davomat", "📥 eMaktab Hisobot"])
if st.sidebar.button("🚪 Chiqish"):
    st.session_state.clear()
    st.rerun()

# --- 5. BO'LIMLAR ---

# --- GPS DAVOMAT (SIZNING ASL KODINGIZ) ---
if menu == "📍 GPS Davomat":
    st.title("📍 GPS Davomat")
    loc = get_geolocation()
    if loc:
        upos = (loc['coords']['latitude'], loc['coords']['longitude'])
        masofa = geodesic(upos, MAKTAB_KOORDINATASI).km
        if masofa <= RUXSAT_ETILGAN_MASOFA:
            st.success(f"📍 Hududdasiz ({round(masofa*1000)} m)")
            ism = st.text_input("F.I.SH:")
            if st.button("Tasdiqlash") and ism:
                st.success("Saqlandi!")
        else:
            st.error(f"Hududda emassiz! ({round(masofa*1000)} m)")

# --- EMAKTAB HISOBOT ---
elif menu == "📥 eMaktab Hisobot":
    st.title("📥 Kundalik bilan ta'minlanganlik")
    
    col1, col2 = st.columns(2)
    with col1:
        e_l = st.text_input("Login:", value="marufabdiyev")
        e_p = st.text_input("Parol:", type="password")
    with col2:
        e_id = st.text_input("Maktab ID:", value="1000001352999")
    
    if st.button("🔍 Ma'lumotni olish", use_container_width=True):
        with st.spinner("eMaktabdan jadval qidirilmoqda..."):
            df, msg = kundalik_hisobot_ol(e_l, e_p, e_id)
            if df is not None:
                st.session_state.em_df = df
                st.success("Ma'lumotlar yuklandi!")
            else:
                st.error(msg)

    if "em_df" in st.session_state:
        st.divider()
        st.dataframe(st.session_state.em_df, use_container_width=True)
        
        if st.button("📢 Telegramga yuborish"):
            txt = f"<b>📊 Kundalik ta'minlanganlik ({hozir.strftime('%d.%m.%Y')})</b>\n\n"
            txt += f"<pre>{st.session_state.em_df.to_string(index=False)}</pre>"
            requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", 
                         json={"chat_id": GURUH_ID, "text": txt, "parse_mode": "HTML"})
            st.success("Yuborildi!")
