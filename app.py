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
RUXSAT_ETILGAN_MASOFA = 1#0.5  # 500 metr (aniqlik uchun biroz kengaytirildi)

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

# --- GOOGLE SHEETSGA SAQLASH FUNKSIYASI ---
def davomatni_gsheetsga_yoz(ism, holat):
    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        # Jadvalni o'qish
        try:
            df = conn.read(ttl=0)
        except:
            df = pd.DataFrame(columns=["Sana", "Vaqt", "F.I.SH", "Holat"])
        
        # Yangi qator
        yangi_qator = pd.DataFrame({
            "Sana": [hozir.strftime("%d.%m.%Y")],
            "Vaqt": [hozir.strftime("%H:%M:%S")],
            "F.I.SH": [ism],
            "Holat": [holat]
        })
        
        # Birlashtirish va yangilash
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
    menu = st.radio("Bo'limni tanlang:", ["🤖 AI Muloqot", "📊 Jurnal Monitoringi", "📍 GPS Davomat"])
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
    if "m_auth" not in st.session_state: st.session_state.m_auth = False
    if not st.session_state.m_auth:
        m_input = st.text_input("Monitoring kodi:", type="password")
        if st.button("Kirish"):
            if m_input == MONITORING_KODI:
                st.session_state.m_auth = True
                st.rerun()
            else: st.error("Kod xato!")
        st.stop()
    
    j_fayl = st.file_uploader("Excel faylni yuklang", type=['xlsx', 'xls', 'html'])
    if j_fayl:
        try:
            df_j = pd.read_excel(j_fayl)
            st.dataframe(df_j, use_container_width=True)
            if st.button("📢 Telegramga yuborish"):
                st.success("Yuborildi!")
        except Exception as e: st.error(f"Xato: {e}")

# --- GPS DAVOMAT ---
elif menu == "📍 GPS Davomat":
    st.title("📍 GPS Davomat (Google Sheets)")
    
    ertalab = (hozirgi_vaqt.hour < 8) or (hozirgi_vaqt.hour == 8 and hozirgi_vaqt.minute <= 30)
    kechki = (hozirgi_vaqt.hour >= 13)

    if ertalab or kechki:
        ish_holati = "KELDI" if ertalab else "KETDI"
        st.success(f"🔓 Tizim ochiq (Holat: **{ish_holati}**)")
        
        with st.spinner("🛰 GPS aniqlanmoqda..."):
            loc = get_geolocation()
        
        if loc and 'coords' in loc:
            upos = (loc['coords']['latitude'], loc['coords']['longitude'])
            masofa = geodesic(upos, MAKTAB_KOORDINATASI).km
            
            if masofa <= RUXSAT_ETILGAN_MASOFA:
                st.success(f"📍 Hududdasiz ({round(masofa*1000)} m)")
                ism = st.text_input("F.I.SH (Ism-familiyangiz):")
                
                if st.button(f"🔴 {ish_holati}NI TASDIQLASH", use_container_width=True):
                    if ism:
                        if davomatni_gsheetsga_yoz(ism, ish_holati):
                            tg_text = f"📍 #DAVOMAT\n👤 {ism}\n📅 {hozir.strftime('%d.%m.%Y')}\n⏰ {hozir.strftime('%H:%M')}\n🔄 {ish_holati}"
                            requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", 
                                          json={"chat_id": GURUH_ID, "text": tg_text})
                            st.balloons()
                            st.success("Google Sheets-ga saqlandi!")
                    else: st.error("Ismingizni yozing!")
            else: st.error(f"Hududda emassiz! Masofa: {round(masofa*1000)} m")
        else: st.warning("🛰 GPS signali kutilmoqda...")
    else:
        st.error("⚠️ Davomat yopiq (08:30 - 13:00)")

    # ADMIN VIEW
    st.divider()
    if st.checkbox("Google Jadvalni ko'rish (Admin)"):
        if st.text_input("Admin kod:", type="password", key="adm_v") == MONITORING_KODI:
            conn = st.connection("gsheets", type=GSheetsConnection)
            st.dataframe(conn.read(ttl=0), use_container_width=True)

