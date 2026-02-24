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
    st.error(f"Secrets sozlamalarida xatolik: {e}")
    st.stop()

# --- 2. EMAKTAB TAHLIL FUNKSIYASI (KUCHAYTIRILGAN) ---
def kundalik_hisobot_ol(login, parol, school_id):
    session = requests.Session()
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    try:
        # Kirish jarayoni
        session.get("https://login.emaktab.uz", headers=headers)
        login_data = {"login": login, "password": parol}
        res = session.post("https://login.emaktab.uz", data=login_data, headers=headers)
        
        if "logout" not in res.text.lower() and "chiqish" not in res.text.lower():
            return None, "🔒 Kirish amalga oshmadi. Login yoki parol xato!"

        # Kundalik ta'minlanganlik hisoboti URL
        # report=paid-access-school - aynan kundalik ta'minlanganlik parametri
        url = f"https://schools.emaktab.uz/v2/reports/default?school={school_id}&report=paid-access-school&year=2025"
        response = session.get(url, headers=headers)
        
        if response.status_code != 200:
            return None, "🌐 Hisobot sahifasini yuklab bo'lmadi."

        soup = BeautifulSoup(response.content, 'html.parser')
        
        # JADVALNI QIDIRISH (2 xil usulda)
        rows_data = []
        
        # 1-usul: Barcha 'tr' (jadval qatorlari) bo'yicha qidirish
        all_rows = soup.find_all('tr')
        for row in all_rows:
            cols = row.find_all('td')
            if len(cols) >= 4:
                sinf = cols[0].get_text(strip=True)
                foiz = cols[3].get_text(strip=True)
                
                # Agar birinchi ustunda raqam va "-" bo'lsa (masalan: 1-A)
                if "-" in sinf and any(char.isdigit() for char in sinf):
                    rows_data.append([sinf, foiz])
        
        if rows_data:
            df = pd.DataFrame(rows_data, columns=['Sinf nomi', 'Ta\'minlanganlik (%)'])
            return df, "OK"
        else:
            # 2-usul: Agar BeautifulSoup topmasa, Pandas orqali jadvalni qidirish
            dfs = pd.read_html(io.StringIO(str(soup)))
            for d in dfs:
                if d.shape[1] >= 4:
                    mask = d.iloc[:, 0].astype(str).str.contains('-', na=False)
                    if mask.any():
                        res_df = d[mask].iloc[:, [0, 3]].copy()
                        res_df.columns = ['Sinf nomi', 'Ta\'minlanganlik (%)']
                        return res_df, "OK"
            
            return None, "❌ Hisobotda sinflar jadvali topilmadi. Hisobot hali shakllanmagan bo'lishi mumkin."

    except Exception as e:
        return None, f"⚠️ Xatolik yuz berdi: {str(e)}"

# --- 3. LOGIN VA NAVIGATSIYA ---
if "authenticated" not in st.session_state: st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.title("🏫 " + MAKTAB_NOMI)
    p_in = st.text_input("Kirish paroli:", type="password")
    if st.button("Kirish") and p_in == ASOSIY_PAROL:
        st.session_state.authenticated = True
        st.rerun()
    st.stop()

# Sidebarda menu
menu = st.sidebar.radio("Bo'lim:", ["🤖 AI Muloqot", "📊 Jurnal Monitoringi", "📍 GPS Davomat", "📥 eMaktab Hisobot"])
if st.sidebar.button("🚪 Chiqish"):
    st.session_state.clear()
    st.rerun()

# --- 4. BO'LIMLAR ---

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

# --- EMAKTAB HISOBOT (KUNDALIK TAMINLANGANLIK) ---
elif menu == "📥 eMaktab Hisobot":
    st.title("📥 Kundalik bilan ta'minlanganlik")
    
    col1, col2 = st.columns(2)
    with col1:
        e_l = st.text_input("eMaktab Login:", value="marufabdiyev")
        e_p = st.text_input("eMaktab Parol:", type="password")
    with col2:
        e_id = st.text_input("Maktab ID:", value="1000001352999")
        st.info("Hisobot avtomatik 2025-yil uchun olinadi.")

    if st.button("🔍 Hisobotni yuklash", use_container_width=True):
        with st.spinner("eMaktab tizimidan ma'lumotlar olinmoqda..."):
            df, msg = kundalik_hisobot_ol(e_l, e_p, e_id)
            if df is not None:
                st.session_state.kundalik_df = df
                st.success("Ma'lumotlar muvaffaqiyatli yuklandi!")
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
            st.success("Telegramga yuborildi!")

# (Qolgan AI va Monitoring bo'limlari o'z holicha qoladi...)
