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

# GPS KOORDINATALARI (Sizning asl koordinatalaringiz)
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
    st.error(f"Secrets sozlamalarida xatolik: {e}")
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

        # Operativ hisobot URL (2025-yil uchun)
        view_url = f"https://schools.emaktab.uz/v2/reports/default?school={school_id}&report=paid-access-school&year=2025"
        response = session.get(view_url, headers=headers)
        
        if response.status_code == 200:
            return True, response.content
        return False, f"Sahifa ochilmadi: Status {response.status_code}"
    except Exception as e:
        return False, str(e)

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
    except:
        return False

# --- 4. KIRISH TIZIMI ---
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.title("🏫 " + MAKTAB_NOMI)
        p_in = st.text_input("Kirish paroli:", type="password")
        if st.button("Kirish", use_container_width=True):
            if p_in == ASOSIY_PAROL:
                st.session_state.authenticated = True
                st.rerun()
            else:
                st.error("Parol noto'g'ri!")
    st.stop()

# --- 5. SIDEBAR ---
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

# --- 6. ASOSIY BO'LIMLAR ---

# --- 🤖 AI MULOQOT ---
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
            except:
                st.error("AI xizmati vaqtincha band.")

# --- 📊 JURNAL MONITORINGI ---
elif menu == "📊 Jurnal Monitoringi":
    st.title("📊 Jurnal Monitoringi")
    m_input = st.text_input("Monitoring kodi:", type="password")
    if m_input == MONITORING_KODI:
        j_fayl = st.file_uploader("Excel yuklang", type=['xlsx', 'xls'])
        if j_fayl:
            df_j = pd.read_excel(j_fayl)
            st.dataframe(df_j, use_container_width=True)
    elif m_input:
        st.error("Kod noto'g'ri!")

# --- 📍 GPS DAVOMAT (Sizning asl kodingiz) ---
elif menu == "📍 GPS Davomat":
    st.title("📍 GPS Davomat")
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
                    st.success("✅ Davomat saqlandi!")
                    st.balloons()
        else:
            st.error(f"Hududda emassiz! Masofa: {round(masofa*1000)} m")

# --- 📥 EMAKTAB HISOBOT (Tuzatilgan qism) ---
elif menu == "📥 eMaktab Hisobot":
    st.title("📥 eMaktab Operativ Hisoboti")
    if "em_df" not in st.session_state: st.session_state.em_df = None
    
    col_a, col_b = st.columns(2)
    with col_a: e_l = st.text_input("Login", value="marufabdiyev")
    with col_b: e_p = st.text_input("Parol", type="password")
    e_id = st.text_input("Maktab ID", value="1000001352999")
    
    if st.button("🔍 Hisobotni yangilash", use_container_width=True):
        ok, content = emaktab_hisobot_yukla(e_l, e_p, e_id)
        if ok:
            try:
                # Barcha jadvallarni o'qish
                dfs = pd.read_html(io.BytesIO(content), encoding='utf-8')
                found = False
                for df_temp in dfs:
                    if df_temp.shape[1] >= 4:
                        # 0-ustundan sinf nomini (1-A kabi) qidirish
                        mask = df_temp.iloc[:, 0].astype(str).str.contains('-', na=False)
                        if mask.any():
                            # 0-Sinf, 3-Foiz ustunlarini ajratish
                            report = df_temp[mask].iloc[:, [0, 3]].copy()
                            report.columns = ['Sinf nomi', 'Kirish foizi (%)']
                            st.session_state.em_df = report
                            found = True
                            st.success("✅ Jadval muvaffaqiyatli tahlil qilindi!")
                            break
                if not found:
                    st.error("Jadval topilmadi yoki kutilgan formatda emas.")
            except Exception as e:
                st.error(f"Tahlil xatosi: {e}")
        else:
            st.error(content)

    if st.session_state.em_df is not None:
        st.table(st.session_state.em_df)
        if st.button("📢 Telegramga yuborish", use_container_width=True):
            msg = f"<b>📊 eMaktab ({hozir.strftime('%d.%m.%Y')})</b>\n\n"
            msg += f"<pre>{st.session_state.em_df.to_string(index=False)}</pre>"
            requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", 
                         json={"chat_id": GURUH_ID, "text": msg, "parse_mode": "HTML"})
            st.success("Telegramga yuborildi!")
