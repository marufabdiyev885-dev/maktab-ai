# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
import os
import requests
import re
import random
import datetime as dt
import pytz
from groq import Groq
from streamlit_js_eval import get_geolocation
from geopy.distance import geodesic
from streamlit_gsheets import GSheetsConnection

# --- ASOSIY SOZLAMALAR ---
MAKTAB_NOMI = "1-sonli umumta'lim maktabi"
ASOSIY_PAROL = "informatika2024"
MAKTAB_KOORDINATASI = (39.4955640, 64.7924960)
RUXSAT_ETILGAN_MASOFA = 1.0 

st.set_page_config(page_title=MAKTAB_NOMI, layout="wide", page_icon="🏫")

# --- VAQT ---
uzb_tz = pytz.timezone('Asia/Tashkent')
hozir = dt.datetime.now(uzb_tz)

# --- SECRETS ---
try:
    client = Groq(api_key=st.secrets["GROQ_API_KEY"])
    BOT_TOKEN = st.secrets["TELEGRAM_BOT_TOKEN"]
    GURUH_ID = st.secrets["TELEGRAM_GURUH_ID"]
except:
    st.error("API kalitlar topilmadi!")
    st.stop()

# --- LOG-IN ---
if "auth" not in st.session_state: st.session_state.auth = False
if not st.session_state.auth:
    st.title("🏫 " + MAKTAB_NOMI)
    if st.text_input("Kirish paroli:", type="password") == ASOSIY_PAROL:
        if st.button("Kirish"):
            st.session_state.auth = True
            st.rerun()
    st.stop()

# --- SIDEBAR ---
menu = st.sidebar.radio("Bo'lim:", ["👥 Ro'yxatlar", "🤖 AI Muloqot", "📊 Monitoring", "📍 GPS Davomat"])

# --- 1. 👥 RO'YXATLAR ---
if menu == "👥 Ro'yxatlar":
    st.title("📋 Maktab bazasi")
    f_oqt, f_oqv = "baza_o'qituvchilar.xlsx", "baza_o'quvchilar.xlsx"
    t1, t2 = st.tabs(["O'qituvchilar", "O'quvchilar"])
    with t1:
        if os.path.exists(f_oqt): st.dataframe(pd.read_excel(f_oqt), use_container_width=True)
    with t2:
        if os.path.exists(f_oqv): st.dataframe(pd.read_excel(f_oqv), use_container_width=True)

# --- 2. 🤖 AI MULOQOT (SUPER-YORDAMCHI) ---
elif menu == "🤖 AI Muloqot":
    st.title("🚀 Maktab Super-AI")
    if "greeted" not in st.session_state:
        st.chat_message("assistant").markdown("**Assalomu alaykum, Ma'rufjon aka!** Bugun qanday darsga slayd yoki o'yin qidiramiz?")
        st.session_state.greeted = True

    if savol := st.chat_input("Mavzu yoki ismni yozing..."):
        st.chat_message("user").markdown(savol)
        q = savol.lower().strip()

        with st.chat_message("assistant"):
            # Resurslar (Slayd/Video/O'yin)
            if any(x in q for x in ["slayd", "o'yin", "video", "dars"]):
                st.markdown("✅ **Foydali manbalar topildi:**")
                c1, c2, c3 = st.columns(3)
                c1.markdown(f"[📊 Slaydlar](https://www.slideshare.net/search/slideshow?q={q.replace(' ','+')})")
                c2.markdown(f"[🎯 O'yinlar](https://wordwall.net/uz/community?searchterm={q.replace(' ','+')})")
                c3.markdown(f"[🎥 Videolar](https://www.youtube.com/results?search_query={q.replace(' ','+')})")
                st.divider()

            # Baza qidiruvi (Token tejash uchun faqat kerakli qatorlar)
            baza_context = ""
            for f in ["baza_o'qituvchilar.xlsx", "baza_o'quvchilar.xlsx"]:
                if os.path.exists(f):
                    df = pd.read_excel(f).astype(str)
                    match = df[df.apply(lambda r: r.str.contains(q, case=False).any(), axis=1)]
                    if not match.empty: baza_context += match.head(5).to_string(index=False)

            # AI Javobi
            prompt = f"Sen maktab yordamchisisan. Ma'rufjon aka '{savol}' dedi. Baza: {baza_context}. Metodik yordam ber."
            res = client.chat.completions.create(messages=[{"role":"system","content":prompt}], model="llama-3.3-70b-versatile")
            ans = res.choices[0].message.content
            st.markdown(ans)
            
            # Yuklab olish uchun oddiy matn fayli
            st.download_button("📝 Dars ishlanmasini yuklab olish (TXT)", ans, file_name="dars_ishlanma.txt")

# --- 3. MONITORING VA 4. GPS (Oldingi kodlardek davom etadi) ---
# ... (Monitoring va GPS kodingizni o'zgartirmasdan qo'shing)
