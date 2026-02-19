# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
import os
import requests
import re
import io
from groq import Groq

# --- DOIMIY MA'LUMOTLAR ---
MAKTAB_NOMI = "1-sonli umumta'lim maktabi"
DIREKTOR_FIO = "Mahmudov Matyoqub Narzulloyevich"
ASOSIY_PAROL = "informatika2024"
MONITORING_KODI = "admin777"
MAKTAB_ID = "1000001352999"

st.set_page_config(page_title=MAKTAB_NOMI, layout="wide", page_icon="🏫")

# --- SECRETS VA CLIENT ---
try:
    BOT_TOKEN = st.secrets["TELEGRAM_BOT_TOKEN"]
    GURUH_ID = st.secrets["TELEGRAM_GURUH_ID"]
    GROQ_API_KEY = st.secrets["GROQ_API_KEY"]
    client = Groq(api_key=GROQ_API_KEY)
except Exception as e:
    st.error(f"Secrets xatolik: {str(e)}")
    st.stop()

# --- UNIVERSAL API FUNKSIYASI ---
def emaktab_so'rov(path):
    """e-Maktabning istalgan bo'limidan ma'lumot olish"""
    url = f"https://emaktab.uz{path}"
    headers = {
        'Accept': 'application/json, text/plain, */*',
        'Referer': 'https://emaktab.uz/reports/schools/filling',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36'
    }
    # BU YERGA ERTAGA YANGI COOKIE QO'YISHINGIZ KERAK
    cookies = {
        'sst': 'f598c3fd-77c6-42cc-93ba-1c9fd4cf0ca5|20/02/2026 17:44:50',
        'UZDnevnikAuth_a': 'zuMlwMAdJeMW8nMXUFIK7GG3XsDWtuZmvWdNY1w6STmgPZjQE9iO6mc0sJg2j7Z%2F%2BxaJci3q0r%2FBS6hOrqaOxiec%2F3qijz8T%2B9cwuRhchqVtB3niadsINnYhuFiLLWsM9%2BELUlIpXMXdc6W9eyzJ99nVsBFHzSZZmaIoSZd96uI6eoLjUDf18vx526OG28SGEXcAtzToybTxcuICCEk2ZFPMm1KRsr9EH94m2eYof8UYpYQZbQb5nnqdcKuRhBV%2F%2BIU2rUxwDz3N%2Fj63MQYv9RImd6g%3D',
    }
    try:
        res = requests.get(url, headers=headers, cookies=cookies, timeout=15)
        if res.status_code == 200:
            return res.json()
        return None
    except:
        return None

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

# --- AUTHENTICATION ---
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
    menu = st.radio("Bo'limni tanlang:", ["🤖 AI Muloqot", "📊 Jurnal Monitoringi", "📂 Maktab Bazasi"])

# --- AI MULOQOT --- (Sizning kodingiz o'zgarmadi)
if menu == "🤖 AI Muloqot":
    st.title("🤖 Maktab AI Yordamchisi")
    # ... (AI muloqot qismi shu yerda qoladi)

# --- JURNAL MONITORINGI (API INTEGRATSIYA) ---
elif menu == "📊 Jurnal Monitoringi":
    st.title("📊 Jurnal Monitoringi (e-Maktab Live)")
    
    if "m_auth" not in st.session_state: st.session_state.m_auth = False
    if not st.session_state.m_auth:
        m_input = st.text_input("Monitoring kodi:", type="password")
        if st.button("Tasdiqlash"):
            if m_input == MONITORING_KODI:
                st.session_state.m_auth = True
                st.rerun()
        st.stop()

    tab1, tab2 = st.tabs(["⚡️ Avtomatik (API)", "📁 Qo'lda (Excel)"])

    with tab1:
        st.info("Hisobotlar bo'limidan yozilmagan jurnallar va kamchiliklarni olish.")
        col_btn1, col_btn2 = st.columns(2)
        
        if col_btn1.button("🔍 Yozilmagan jurnallarni tekshirish"):
            data = emaktab_so'rov(f"/teachers/api/problems?userId=1000002716779&date=null")
            if data:
                st.subheader("📝 Natijalar")
                if data.get("lessonsWithoutTitle"):
                    st.error(f"Mavzusi yo'q darslar: {len(data['lessonsWithoutTitle'])} ta")
                    st.dataframe(pd.DataFrame(data['lessonsWithoutTitle']))
                if data.get("lessonsWithoutMarks"):
                    st.warning(f"Bahosiz darslar: {len(data['lessonsWithoutMarks'])} ta")
                    st.dataframe(pd.DataFrame(data['lessonsWithoutMarks']))
                if not data.get("lessonsWithoutTitle") and not data.get("lessonsWithoutMarks"):
                    st.success("Hamma jurnallar to'liq! ✅")
            else: st.error("Ulanish xatosi (Cookie yangilang)")

    with tab2:
        # Sizning avvalgi Excel yuklash kodingiz shu yerda
        j_fayl = st.file_uploader("Excel faylni yuklang", type=['xlsx', 'xls'])
        # ... (Excel tahlil qismi)

# --- MAKTAB BAZASI (O'QITUVCHI VA O'QUVCHILAR) ---
elif menu == "📂 Maktab Bazasi":
    st.title("📂 Maktab Umumiy Bazasi")
    
    st.info("Ushbu bo'lim e-maktabdan barcha o'qituvchi va o'quvchilar ro'yxatini real vaqtda oladi.")
    
    c1, c2, c3 = st.columns(3)
    
    if c1.button("👨‍🏫 O'qituvchilar ro'yxati"):
        # API yo'li o'qituvchilar uchun (Namuna)
        teachers = emaktab_so'rov(f"/api/school/{MAKTAB_ID}/teachers")
        if teachers: st.dataframe(pd.DataFrame(teachers))
        else: st.warning("Ma'lumot topilmadi yoki ruxsat yo'q.")

    if c2.button("👨‍🎓 O'quvchilar ro'yxati"):
        students = emaktab_so'rov(f"/api/school/{MAKTAB_ID}/students")
        if students: st.dataframe(pd.DataFrame(students))
        else: st.warning("Ma'lumot topilmadi.")

    if c3.button("📈 Umumiy Hisobot"):
        report = emaktab_so'rov(f"/api/reports/schools/filling/{MAKTAB_ID}")
        if report: st.json(report)
        else: st.error("Hisobotni yuklab bo'lmadi.")
