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

# Vaqt
uzb_tz = pytz.timezone('Asia/Tashkent')
hozir = dt.datetime.now(uzb_tz)

try:
    BOT_TOKEN = st.secrets["TELEGRAM_BOT_TOKEN"]
    GURUH_ID = st.secrets["TELEGRAM_GURUH_ID"]
    client = Groq(api_key=st.secrets["GROQ_API_KEY"])
except Exception as e:
    st.error(f"Secrets sozlamalarida xatolik: {e}")
    st.stop()

# --- 2. EMAKTAB UCHUN MUKAMMAL TAHLIL FUNKSIYASI ---
def kundalik_hisobot_ol(login, parol, school_id):
    session = requests.Session()
    # Brauzerni mukammal simulyatsiya qilish
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
        'Accept-Language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
        'Referer': 'https://login.emaktab.uz/'
    }
    
    try:
        # 1-qadam: Login sahifasini olish
        login_url = "https://login.emaktab.uz"
        session.get(login_url, headers=headers)
        
        # 2-qadam: Kirish (Login)
        login_data = {"login": login, "password": parol}
        res = session.post(login_url, data=login_data, headers=headers)
        
        if "logout" not in res.text.lower() and "chiqish" not in res.text.lower():
            return None, "Login yoki parol noto'g'ri. Iltimos, qayta tekshiring."

        # 3-qadam: Hisobot sahifasiga o'tish
        # Kundalik ta'minlanganlik: report=paid-access-school
        report_url = f"https://schools.emaktab.uz/v2/reports/default?school={school_id}&report=paid-access-school&year=2025"
        response = session.get(report_url, headers=headers)
        
        if response.status_code != 200:
            return None, f"Sahifa yuklanmadi. Status: {response.status_code}"

        # 4-qadam: Ma'lumotni tahlil qilish
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Jadvallarni yig'ish (BeautifulSoup orqali qo'lda)
        rows_list = []
        tables = soup.find_all('table')
        
        if tables:
            # Eng katta jadvalni tanlaymiz
            main_table = max(tables, key=lambda t: len(t.find_all('tr')))
            for tr in main_table.find_all('tr'):
                tds = tr.find_all('td')
                if len(tds) >= 4:
                    sinf = tds[0].get_text(strip=True)
                    foiz = tds[3].get_text(strip=True)
                    # Sinf nomida raqam va "-" borligini tekshirish (Masalan: 4-B)
                    if "-" in sinf and any(c.isdigit() for c in sinf):
                        rows_list.append([sinf, foiz])
        
        if rows_list:
            df = pd.DataFrame(rows_list, columns=['Sinf nomi', 'Ta\'minlanganlik (%)'])
            return df, "OK"
        else:
            # Agar BeautifulSoup topmasa, Pandas orqali harakat qilamiz
            try:
                dfs = pd.read_html(io.StringIO(str(soup)))
                for d in dfs:
                    if d.shape[1] >= 4:
                        mask = d.iloc[:, 0].astype(str).str.contains('-', na=False)
                        if mask.any():
                            clean_df = d[mask].iloc[:, [0, 3]].copy()
                            clean_df.columns = ['Sinf nomi', 'Ta\'minlanganlik (%)']
                            return clean_df, "OK"
            except:
                pass
            return None, "Hisobotda sinflar jadvali topilmadi. Maktab ID'sini tekshiring."

    except Exception as e:
        return None, f"Tizimda xatolik: {str(e)}"

# --- 3. ILOVA INTERFEYSI ---
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.title("🏫 " + MAKTAB_NOMI)
    p_in = st.text_input("Kirish paroli:", type="password")
    if st.button("Kirish"):
        if p_in == ASOSIY_PAROL:
            st.session_state.authenticated = True
            st.rerun()
        else:
            st.error("Parol xato!")
    st.stop()

# Menyu
menu = st.sidebar.radio("Bo'limni tanlang:", ["🤖 AI Muloqot", "📊 Jurnal Monitoringi", "📍 GPS Davomat", "📥 eMaktab Hisobot"])
if st.sidebar.button("🚪 Chiqish"):
    st.session_state.clear()
    st.rerun()

# --- 4. BO'LIMLAR ---

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

elif menu == "📥 eMaktab Hisobot":
    st.title("📥 Kundalik bilan ta'minlanganlik")
    
    col1, col2 = st.columns(2)
    with col1:
        e_l = st.text_input("eMaktab Login:", value="marufabdiyev")
        e_p = st.text_input("eMaktab Parol:", type="password")
    with col2:
        e_id = st.text_input("Maktab ID:", value="1000001352999")
        st.info("Hisobot 2025-o'quv yili uchun olinadi.")

    if st.button("🔍 Hisobotni yuklash", use_container_width=True):
        with st.spinner("eMaktab tizimi bilan bog'lanilmoqda..."):
            df, msg = kundalik_hisobot_ol(e_l, e_p, e_id)
            if df is not None:
                st.session_state.kundalik_df = df
                st.success("Ma'lumotlar olindi!")
            else:
                st.error(msg)

    if "kundalik_df" in st.session_state:
        st.divider()
        st.table(st.session_state.kundalik_df)
        
        if st.button("📢 Telegramga yuborish"):
            txt = f"<b>📊 Kundalik bilan ta'minlanganlik ({hozir.strftime('%d.%m.%Y')})</b>\n\n"
            txt += f"<pre>{st.session_state.kundalik_df.to_string(index=False)}</pre>"
            requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", 
                         json={"chat_id": GURUH_ID, "text": txt, "parse_mode": "HTML"})
            st.success("Xabar yuborildi!")
