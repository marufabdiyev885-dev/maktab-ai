# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
import os
import requests
import re
import io
import datetime as dt
import pytz  # Vaqt mintaqasi uchun
from groq import Groq
from streamlit_js_eval import get_geolocation
from geopy.distance import geodesic

# --- ASOSIY SOZLAMALAR ---
MAKTAB_NOMI = "1-sonli umumta'lim maktabi"
DIREKTOR_FIO = "Mahmudov Matyoqub Narzulloyevich"
ASOSIY_PAROL = "informatika2024"
MONITORING_KODI = "admin777"
DAVOMAT_FAYLI = "davomat_bazasi.csv"

# MAKTAB KOORDINATALARI (Qorovulbozor)
MAKTAB_LAT = 39.4955640
MAKTAB_LON = 64.7924960
MAKTAB_KOORDINATASI = (MAKTAB_LAT, MAKTAB_LON)
RUXSAT_ETILGAN_MASOFA = 0.2  # 200 metr radius

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
    st.error(f"Secrets xatolik: {e}")
    st.stop()

# --- DAVOMATNI SAQLASH FUNKSIYASI ---
def davomatni_saqlash(ism, holat):
    v_txt = hozir.strftime("%H:%M:%S")
    s_txt = hozir.strftime("%d.%m.%Y")
    yangi_malumot = pd.DataFrame([[s_txt, v_txt, ism, holat]], 
                                columns=["Sana", "Vaqt", "F.I.SH", "Holat"])
    
    if not os.path.isfile(DAVOMAT_FAYLI):
        yangi_malumot.to_csv(DAVOMAT_FAYLI, index=False, encoding='utf-8-sig')
    else:
        yangi_malumot.to_csv(DAVOMAT_FAYLI, mode='a', header=False, index=False, encoding='utf-8-sig')

# --- EXCEL YUKLASH (AI uchun) ---
@st.cache_data(ttl=300)
def yuklash():
    files = [f for f in os.listdir('.') if f.lower().endswith(('.xlsx', '.xls'))]
    all_sheets = {}
    for f in files:
        try:
            sheets = pd.read_excel(f, sheet_name=None, dtype=str)
            for name, df in sheets.items():
                if not df.empty:
                    df.columns = [str(c).strip().lower() for c in df.columns]
                    all_sheets[f + " | " + name] = df
        except: continue
    return all_sheets

sheets_baza = yuklash()

# --- LOG-IN ---
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
            else: st.error("Parol xato!")
    st.stop()

# --- SIDEBAR ---
with st.sidebar:
    st.title("🏛 " + MAKTAB_NOMI)
    st.write(f"👤 **Direktor:** {DIREKTOR_FIO}")
    st.divider()
    menu = st.radio("Bo'limni tanlang:", ["🤖 AI Muloqot", "📊 Jurnal Monitoringi", "📍 GPS Davomat"])
    st.divider()
    if st.button("🚪 Chiqish", use_container_width=True):
        st.session_state.clear()
        st.rerun()

# =============================================
# AI MULOQOT
# =============================================
if menu == "🤖 AI Muloqot":
    st.title("🤖 AI Yordamchi")
    if "messages" not in st.session_state: st.session_state.messages = []
    
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]): st.markdown(msg["content"])

    savol = st.chat_input("Savol yozing...")
    if savol:
        st.session_state.messages.append({"role": "user", "content": savol})
        with st.chat_message("user"): st.markdown(savol)
        
        # AI Logic (Qisqa)
        try:
            res = client.chat.completions.create(
                messages=[{"role": "system", "content": "Sen yordamchisan."}] + st.session_state.messages[-5:],
                model="llama-3.3-70b-versatile",
            )
            ans = res.choices[0].message.content
            st.chat_message("assistant").markdown(ans)
            st.session_state.messages.append({"role": "assistant", "content": ans})
        except: st.error("AI xatosi")

# =============================================
# JURNAL MONITORINGI
# =============================================
elif menu == "📊 Jurnal Monitoringi":
    st.title("📊 Monitoring")
    if not st.session_state.get("m_auth", False):
        m_in = st.text_input("Monitoring kodi:", type="password")
        if st.button("Kirish"):
            if m_in == MONITORING_KODI: 
                st.session_state.m_auth = True
                st.rerun()
            else: st.error("Xato")
        st.stop()

    f = st.file_uploader("Excel yuklang", type=['xlsx', 'xls'])
    if f:
        df_j = pd.read_excel(f) if not f.name.endswith('.xls') else pd.read_html(f)[0]
        st.dataframe(df_j)
        # Monitoring mantiqi (Sizning kodingizdagi re.findall qismi)
        st.info("Hisobot tahlilga tayyor.")

# =============================================
# GPS DAVOMAT (MUHIM QISM)
# =============================================
elif menu == "📍 GPS Davomat":
    st.title("📍 GPS Davomat Tizimi")
    
    # VAQTNI TEKSHIRISH
    is_morning = (hozirgi_vaqt.hour < 8) or (hozirgi_vaqt.hour == 8 and hozirgi_vaqt.minute <= 30)
    is_afternoon = (hozirgi_vaqt.hour >= 13)

    st.write(f"🕒 **Hozirgi vaqt:** {hozirgi_vaqt.strftime('%H:%M')}")

    if is_morning or is_afternoon:
        st.success("🔓 Tizim ochiq")
        loc = get_geolocation()

        if loc:
            upos = (loc['coords']['latitude'], loc['coords']['longitude'])
            masofa = geodesic(upos, MAKTAB_KOORDINATASI).km
            
            if masofa <= RUXSAT_ETILGAN_MASOFA:
                st.success(f"📍 Maktab hududidasiz ({round(masofa*1000)} m)")
                ism = st.text_input("F.I.SH:")
                if st.button("🔴 TASDIQLASH", use_container_width=True):
                    if ism:
                        holat = "KELDI" if is_morning else "KETDI"
                        davomatni_saqlash(ism, holat)
                        tg_txt = f"📍 #DAVOMAT\n👤 {ism}\n📅 {hozir.strftime('%d.%m.%Y')}\n⏰ {hozir.strftime('%H:%M:%S')}\n🔄 {holat}"
                        requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", 
                                      json={"chat_id": GURUH_ID, "text": tg_txt})
                        st.balloons()
                        st.success("Qayd etildi!")
                    else: st.error("Ism yozing")
            else: st.error(f"Maktabda emassiz! ({round(masofa*1000)} m)")
        else: st.info("GPS kutilmoqda... (Ruxsat bering)")
    else:
        st.error("⚠️ Davomat yopiq! (08:30 gacha yoki 13:00 dan keyin)")

    # ADMIN: EXCEL YUKLAB OLISH
    st.divider()
    with st.expander("📥 Bazani Excelda yuklab olish"):
        if st.text_input("Admin kod:", type="password", key="ad_d") == MONITORING_KODI:
            if os.path.exists(DAVOMAT_FAYLI):
                df_d = pd.read_csv(DAVOMAT_FAYLI)
                st.dataframe(df_d)
                out = io.BytesIO()
                df_d.to_excel(out, index=False)
                st.download_button("📥 Excelni yuklab olish", out.getvalue(), "davomat.xlsx")
