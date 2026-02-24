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

# GPS KOORDINATALARI (Sizning asl kodingizdagidek)
MAKTAB_LAT = 39.4955640
MAKTAB_LON = 64.7924960
MAKTAB_KOORDINATASI = (MAKTAB_LAT, MAKTAB_LON)
RUXSAT_ETILGAN_MASOFA = 1 

st.set_page_config(page_title=MAKTAB_NOMI, layout="wide", page_icon="🏫")

# --- 2. VAQT VA SECRETS ---
uzb_tz = pytz.timezone('Asia/Tashkent')
hozir = dt.datetime.now(uzb_tz)

try:
    BOT_TOKEN = st.secrets["TELEGRAM_BOT_TOKEN"]
    GURUH_ID = st.secrets["TELEGRAM_GURUH_ID"]
    GROQ_API_KEY = st.secrets["GROQ_API_KEY"]
    client = Groq(api_key=GROQ_API_KEY)
except Exception as e:
    st.error(f"Secrets xatosi: {e}")
    st.stop()

# --- 3. YORDAMCHI FUNKSIYALAR ---
def emaktab_hisobot_yukla(login, parol, school_id):
    session = requests.Session()
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    try:
        session.get("https://login.emaktab.uz", headers=headers)
        login_data = {"login": login, "password": parol}
        res = session.post("https://login.emaktab.uz", data=login_data, headers=headers)
        
        if "logout" not in res.text.lower() and "chiqish" not in res.text.lower():
            return False, "Login yoki parol xato!"

        # Operativ hisobot URL
        view_url = f"https://schools.emaktab.uz/v2/reports/default?school={school_id}&report=paid-access-school&year=2025"
        response = session.get(view_url, headers=headers)
        
        if response.status_code == 200:
            return True, response.content
        return False, "Sahifani yuklab bo'lmadi."
    except Exception as e:
        return False, str(e)

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
    except:
        return False

# --- 4. KIRISH TIZIMI ---
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    col2 = st.columns([1, 2, 1])[1]
    with col2:
        st.title("🏫 " + MAKTAB_NOMI)
        p_in = st.text_input("Parol:", type="password")
        if st.button("Kirish"):
            if p_in == ASOSIY_PAROL:
                st.session_state.authenticated = True
                st.rerun()
            else: st.error("Xato!")
    st.stop()

# --- 5. SIDEBAR ---
with st.sidebar:
    st.title("🏛 Menu")
    menu = st.radio("Bo'limni tanlang:", ["🤖 AI Muloqot", "📊 Jurnal Monitoringi", "📍 GPS Davomat", "📥 eMaktab Hisobot"])
    if st.button("🚪 Chiqish"):
        st.session_state.clear()
        st.rerun()

# --- 6. ASOSIY LOGIKA ---

if menu == "🤖 AI Muloqot":
    st.title("🤖 AI Yordamchi")
    if "messages" not in st.session_state: st.session_state.messages = []
    for m in st.session_state.messages:
        with st.chat_message(m["role"]): st.markdown(m["content"])
    savol = st.chat_input("Savol...")
    if savol:
        st.session_state.messages.append({"role": "user", "content": savol})
        with st.chat_message("user"): st.markdown(savol)
        res = client.chat.completions.create(messages=[{"role": "system", "content": "Maktab AI"}] + st.session_state.messages[-5:], model="llama-3.3-70b-versatile")
        ans = res.choices[0].message.content
        with st.chat_message("assistant"): st.markdown(ans)
        st.session_state.messages.append({"role": "assistant", "content": ans})

elif menu == "📊 Jurnal Monitoringi":
    st.title("📊 Monitoring")
    if st.text_input("Monitoring kodi:", type="password") == MONITORING_KODI:
        f = st.file_uploader("Excel yuklang", type=['xlsx', 'xls'])
        if f: st.dataframe(pd.read_excel(f))

elif menu == "📍 GPS Davomat":
    st.title("📍 GPS Davomat")
    loc = get_geolocation()
    if loc:
        upos = (loc['coords']['latitude'], loc['coords']['longitude'])
        masofa = geodesic(upos, MAKTAB_KOORDINATASI).km
        if masofa <= RUXSAT_ETILGAN_MASOFA:
            st.success(f"📍 Hududdasiz ({round(masofa*1000)} m)")
            ism = st.text_input("F.I.SH:").strip()
            if st.button("Tasdiqlash") and ism:
                if davomatni_gsheetsga_yoz(ism, "KELDI"): st.success("Saqlandi!")
        else:
            st.error("Hududdan tashqaridasiz!")

elif menu == "📥 eMaktab Hisobot":
    st.title("📥 eMaktab Operativ Hisoboti")
    if "em_df" not in st.session_state: st.session_state.em_df = None
    
    c1, c2 = st.columns(2)
    with c1: e_l = st.text_input("Login", value="marufabdiyev")
    with c2: e_p = st.text_input("Parol", type="password")
    e_id = st.text_input("Maktab ID", value="1000001352999")
    
    if st.button("🔍 Hisobotni yangilash", use_container_width=True):
        ok, content = emaktab_hisobot_yukla(e_l, e_p, e_id)
        if ok:
            try:
                # 1. BeautifulSoup orqali HTMLni tozalash
                soup = BeautifulSoup(content, 'html.parser')
                # 2. barcha tablelarni pandasga berish
                dfs = pd.read_html(io.StringIO(str(soup)), encoding='utf-8')
                
                found = False
                for df_temp in dfs:
                    # Rasmga ko'ra jadvalda Sinf va Foiz ustunlari borligini tekshirish
                    if df_temp.shape[1] >= 4:
                        # Sinf formatini (1-A, 4-B...) 0-ustundan qidiramiz
                        mask = df_temp.iloc[:, 0].astype(str).str.contains('-', na=False)
                        if mask.any():
                            # 0-ustun Sinf, 3-ustun Foiz
                            report = df_temp[mask].iloc[:, [0, 3]].copy()
                            report.columns = ['Sinf nomi', 'Kirish foizi (%)']
                            st.session_state.em_df = report
                            found = True
                            st.success("✅ Jadval topildi va tahlil qilindi!")
                            break
                if not found:
                    st.error("Jadval topilmadi. Login yoki ID ni tekshiring.")
            except Exception as e:
                st.error(f"Tahlil xatosi: {e}")
        else:
            st.error(content)

    if st.session_state.em_df is not None:
        st.table(st.session_state.em_df)
        if st.button("📢 Telegramga yuborish", use_container_width=True):
            msg = f"<b>📊 eMaktab ({hozir.strftime('%d.%m.%Y')})</b>\n\n<pre>{st.session_state.em_df.to_string(index=False)}</pre>"
            requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", 
                         json={"chat_id": GURUH_ID, "text": msg, "parse_mode": "HTML"})
            st.success("Yuborildi!")
