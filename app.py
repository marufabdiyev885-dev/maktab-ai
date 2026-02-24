# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
import os
import requests
import re
import io
import datetime as dt
import pytz
from groq import Groq
from streamlit_js_eval import get_geolocation
from geopy.distance import geodesic
from streamlit_gsheets import GSheetsConnection

# --- ASOSIY SOZLAMALAR ---
MAKTAB_NOMI = "1-sonli umumta'lim maktabi"
DIREKTOR_FIO = "Mahmudov Matyoqub Narzulloyevich"
ASOSIY_PAROL = "informatika2024"
MONITORING_KODI = "admin777"

# MAKTAB KOORDINATALARI
MAKTAB_LAT = 39.4955640
MAKTAB_LON = 64.7924960
MAKTAB_KOORDINATASI = (MAKTAB_LAT, MAKTAB_LON)
RUXSAT_ETILGAN_MASOFA = 1 # 1 km (aniqlik uchun)

st.set_page_config(page_title=MAKTAB_NOMI, layout="wide", page_icon="🏫")

# --- O'ZBEKISTON VAQTINI OLISH ---
uzb_tz = pytz.timezone('Asia/Tashkent')
hozir = dt.datetime.now(uzb_tz)
hozirgi_vaqt = hozir.time()

# --- SECRETS TEKSHIRUVI ---
try:
    BOT_TOKEN = st.secrets["TELEGRAM_BOT_TOKEN"]
    GURUH_ID = st.secrets["TELEGRAM_GURUH_ID"]
    GROQ_API_KEY = st.secrets["GROQ_API_KEY"]
    client = Groq(api_key=GROQ_API_KEY)
except Exception as e:
    st.error(f"Secrets sozlamalarida xatolik: {e}")
    st.stop()

# --- EMAKTAB API FUNKSIYASI (SKRINSHOT ASOSIDA TUZATILDI) ---
def emaktab_hisobot_yukla(login, parol, school_id):
    session = requests.Session()
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    try:
        # 1. Login sahifasini ochish — TO'G'RI URL!
        session.get("https://login.emaktab.uz", headers=headers)
        
        # 2. Login qilish
        login_data = {"login": login, "password": parol}
        res = session.post(
            "https://login.emaktab.uz",  
            data=login_data, 
            headers=headers,
            allow_redirects=True
        )
        
        # 3. Kirish tekshiruvi
        if "logout" not in res.text.lower() and "chiqish" not in res.text.lower():
            return False, f"Login xato! Status: {res.status_code}"

        # 4. Hisobot yuklab olish
        yil = 2025
        urls = [
            f"https://schools.emaktab.uz/v2/reports/export?school={school_id}&report=paid-access-school&year={yil}",
            f"https://schools.emaktab.uz/v2/reports/download?school={school_id}&report=paid-access-school&year={yil}",
        ]
        
        for url in urls:
            fayl = session.get(url, headers=headers)
            if fayl.status_code == 200 and len(fayl.content) > 500:
                if b'PK' in fayl.content[:4]:  # Excel fayl belgisi
                    return True, fayl.content
        
        return False, "Fayl yuklanmadi."
        
    except Exception as e:
        return False, str(e)
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

# --- AI MULOQOT ---
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

# --- JURNAL MONITORINGI ---
elif menu == "📊 Jurnal Monitoringi":
    st.title("📊 Jurnal Monitoringi")
    if "m_auth" not in st.session_state:
        st.session_state.m_auth = False
    if not st.session_state.m_auth:
        m_input = st.text_input("Monitoring kodi:", type="password", key="mon_input")
        if st.button("Kirish", key="mon_btn"):
            if m_input == MONITORING_KODI:
                st.session_state.m_auth = True
                st.rerun()
            else: st.error("Kod xato!")
        st.stop()
    
    j_fayl = st.file_uploader("Excel faylni yuklang", type=['xlsx', 'xls', 'html'], key="uploader")
    if j_fayl:
        try:
            try:
                df_j = pd.read_excel(j_fayl, engine='openpyxl')
            except:
                j_fayl.seek(0)
                df_j = pd.read_excel(j_fayl, engine='xlrd')
            
            df_j.columns = [str(c).replace('\n', ' ').strip() for c in df_j.columns]
            kamchiliklar = []
            if len(df_j.columns) >= 6:
                for _, row in df_j.iterrows():
                    name = str(row.iloc[0])
                    val = str(row.iloc[5])
                    if any(x in name.lower() for x in ["tuman", "muassasa", "o'qituvchi", "f.i.sh"]): continue
                    nums = re.findall(r'(\d+)', val)
                    if len(nums) >= 2:
                        baho_bor, jami = int(nums[0]), int(nums[1])
                        if baho_bor < jami:
                            farq = jami - baho_bor
                            kamchiliklar.append(f"❌ **{name}**: {farq} ta jurnal chala ({val})")
                
                st.subheader("📋 Tekshiruv Natijasi:")
                st.dataframe(df_j, use_container_width=True)
                xabar_text = "✅ Barcha jurnallar baholandi! " if not kamchiliklar else "⚠️ **Kamchiliklar:**\n\n" + "\n".join(kamchiliklar)
                if not kamchiliklar: st.success(xabar_text)
                else: st.warning(xabar_text)
                
                if st.button("📢 Telegramga yuborish", key="tg_btn"):
                    requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", 
                                 json={"chat_id": GURUH_ID, "text": f"<b>📊 Monitoring</b>\n\n{xabar_text}", "parse_mode": "HTML"})
                    st.success("✅ Telegramga yuborildi!")
            else: st.error(f"Faylda ustunlar yetarli emas.")
        except Exception as e: st.error(f"Xato: {e}")

# --- GPS DAVOMAT ---
elif menu == "📍 GPS Davomat":
    st.title("📍 GPS Davomat (Google Sheets)")
    ertalab_bosh, ertalab_tugash = dt.time(7, 30), dt.time(8, 30)
    kechki_bosh, kechki_tugash = dt.time(13, 0), dt.time(21, 0)
    is_ertalab = ertalab_bosh <= hozirgi_vaqt <= ertalab_tugash
    is_kechki = kechki_bosh <= hozirgi_vaqt <= kechki_tugash

    if is_ertalab or is_kechki:
        ish_holati = "KELDI" if is_ertalab else "KETDI"
        bugun_sana = hozir.strftime("%d.%m.%Y")
        conn = st.connection("gsheets", type=GSheetsConnection)
        df_check = conn.read(ttl=0)
        
        with st.spinner("🛰 GPS aniqlanmoqda..."):
            loc = get_geolocation()
        
        if loc and 'coords' in loc:
            upos = (loc['coords']['latitude'], loc['coords']['longitude'])
            masofa = geodesic(upos, MAKTAB_KOORDINATASI).km
            if masofa <= RUXSAT_ETILGAN_MASOFA:
                st.success(f"📍 Hududdasiz ({round(masofa*1000)} m)")
                key_name = f"submitted_{ish_holati}_{bugun_sana}"
                if key_name not in st.session_state: st.session_state[key_name] = False

                if st.session_state[key_name]:
                    st.info(f"✅ Siz qayd etilgansiz.")
                else:
                    ism = st.text_input("F.I.SH (Ism-familiyangiz):").strip()
                    if st.button(f"🔴 {ish_holati}NI TASDIQLASH", use_container_width=True):
                        if ism:
                            takroriy = df_check[(df_check['F.I.SH'] == ism) & (df_check['Sana'] == bugun_sana) & (df_check['Holat'] == ish_holati)]
                            if not takroriy.empty:
                                st.warning("⚠️ Allaqachon qayd etilgansiz!")
                                st.session_state[key_name] = True
                            elif davomatni_gsheetsga_yoz(ism, ish_holati):
                                st.session_state[key_name] = True
                                st.balloons()
                                st.success("Muvaffaqiyatli saqlandi!")
                                st.rerun()
                        else: st.error("Ismingizni yozing!")
            else: st.error(f"Hududda emassiz! ({round(masofa*1000)} m)")
    else: st.error("⚠️ Davomat yopiq!")

# --- EMAKTAB HISOBOT (SAQLANGAN VA TUZATILGAN) ---
elif menu == "📥 eMaktab Hisobot":
    st.title("📥 eMaktab Operativ Hisoboti")
    if "emaktab_df" not in st.session_state: st.session_state.emaktab_df = None
    if "emaktab_raw" not in st.session_state: st.session_state.emaktab_raw = None

    col1, col2 = st.columns(2)
    with col1:
        e_login = st.text_input("Login:", value="marufabdiyev")
        e_parol = st.text_input("Parol:", type="password")
    with col2:
        e_id = st.text_input("Maktab ID:", value="1000001352999")
        st.write(f"📅 Bugun: {hozir.strftime('%d.%m.%Y')}")

    if st.button("🔍 Hisobotni eMaktabdan olish", use_container_width=True):
        if e_parol:
            with st.spinner("Ma'lumotlar olinmoqda..."):
                ok, content = emaktab_hisobot_yukla(e_login, e_parol, e_id)
                if ok:
                    try:
                        # Skrinshotdagi jadvalga mos holda 0 va 3-ustunlarni olamiz
                        df = pd.read_excel(io.BytesIO(content), skiprows=3)
                        report_df = df.iloc[:, [0, 3]].dropna()
                        report_df.columns = ['Sinf nomi', 'Kirish foizi (%)']
                        st.session_state.emaktab_df = report_df
                        st.session_state.emaktab_raw = content
                        st.success("✅ Ma'lumotlar muvaffaqiyatli yuklandi!")
                    except:
                        st.error("Jadvalni o'qishda xato. Formatni tekshiring.")
                else:
                    st.error(content)
        else:
            st.error("Parolni kiriting!")

    if st.session_state.emaktab_df is not None:
        st.divider()
        st.dataframe(st.session_state.emaktab_df, use_container_width=True)
        
        c1, c2 = st.columns(2)
        with c1:
            if st.button("📢 Telegramga yuborish", use_container_width=True):
                f_obj = io.BytesIO(st.session_state.emaktab_raw)
                f_obj.name = f"emaktab_{hozir.strftime('%d_%m')}.xlsx"
                requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendDocument",
                             data={"chat_id": GURUH_ID, "caption": f"📊 eMaktab hisoboti ({hozir.strftime('%d.%m.%Y')})"},
                             files={"document": f_obj})
                st.success("✅ Telegramga yuborildi!")
        with c2:
            if st.button("🤖 AI Tahlil", use_container_width=True):
                with st.spinner("AI tahlil qilmoqda..."):
                    data_str = st.session_state.emaktab_df.to_string(index=False)
                    res = client.chat.completions.create(
                        messages=[{"role": "user", "content": f"Tahlil qil: {data_str}"}],
                        model="llama-3.3-70b-versatile"
                    )
                    st.info(res.choices[0].message.content)


