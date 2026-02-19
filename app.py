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

# --- UNIVERSAL API FUNKSIYASI (TUZATILGAN) ---
def emaktab_sorov(path):
    """e-Maktabning istalgan bo'limidan ma'lumot olish"""
    url = f"https://emaktab.uz{path}"
    headers = {
        'Accept': 'application/json, text/plain, */*',
        'Referer': 'https://emaktab.uz/reports/schools/filling',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36'
    }
    # DIQQAT: Cookie va sst qiymatlari har 24 soatda yangilanishi kerak
    cookies = {
        'sst': 'f598c3fd-77c6-42cc-93ba-1c9fd4cf0ca5|20/02/2026 17:44:50',
        'UZDnevnikAuth_a': 'zuMlwMAdJeMW8nMXUFIK7GG3XsDWtuZmvWdNY1w6STmgPZjQE9iO6mc0sJg2j7Z%2F%2BxaJci3q0r%2FBS6hOrqaOxiec%2F3qijz8T%2B9cwuRhchqVtB3niadsINnYhuFiLLWsM9%2BELUlIpXMXdc6W9eyzJ99nVsBFHzSZZmaIoSZd96uI6eoLjUDf18vx526OG28SGEXcAtzToybTxcuICCEk2ZFPMm1KRsr9EH94m2eYof8UYpYQZbQb5nnqdcKuRhBV%2F%2BIU2rUxwDz3N%2Fj63MQYv9RImd6g%3D',
    }
    try:
        res = requests.get(url, headers=headers, cookies=cookies, timeout=15)
        if res.status_code == 200:
            return res.json()
        return None
    except Exception as e:
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
        except:
            continue
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
            else:
                st.error("Parol xato!")
    st.stop()

# --- SIDEBAR ---
with st.sidebar:
    st.title("🏛 " + MAKTAB_NOMI)
    st.write(f"👤 **Direktor:** {DIREKTOR_FIO}")
    st.divider()
    menu = st.radio("Bo'limni tanlang:", ["🤖 AI Muloqot", "📊 Jurnal Monitoringi", "📂 Maktab Bazasi"])
    st.divider()
    if st.button("🚪 Chiqish", use_container_width=True):
        st.session_state.authenticated = False
        st.rerun()

# --- 🤖 AI MULOQOT ---
if menu == "🤖 AI Muloqot":
    st.title("🤖 Maktab AI Yordamchisi")
    if "messages" not in st.session_state:
        st.session_state.messages = []

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    savol = st.chat_input("Savolingizni yozing...")
    if savol:
        st.session_state.messages.append({"role": "user", "content": savol})
        with st.chat_message("user"):
            st.markdown(savol)

        with st.chat_message("assistant"):
            system_prompt = f"Sen {MAKTAB_NOMI}ning AI yordamchisisan. O'zbek tilida qisqa va metodik javob ber."
            res = client.chat.completions.create(
                messages=[{"role": "system", "content": system_prompt}] + st.session_state.messages[-5:],
                model="llama-3.3-70b-versatile",
            )
            ai_javob = res.choices[0].message.content
            st.markdown(ai_javob)
            st.session_state.messages.append({"role": "assistant", "content": ai_javob})

# --- 📊 JURNAL MONITORINGI ---
elif menu == "📊 Jurnal Monitoringi":
    st.title("📊 Jurnal Monitoringi (e-Maktab Live)")
    
    if "m_auth" not in st.session_state:
        st.session_state.m_auth = False

    if not st.session_state.m_auth:
        m_input = st.text_input("Monitoring kodi:", type="password")
        if st.button("Tasdiqlash"):
            if m_input == MONITORING_KODI:
                st.session_state.m_auth = True
                st.rerun()
        st.stop()

    tab1, tab2 = st.tabs(["⚡️ Avtomatik (API)", "📁 Qo'lda (Excel)"])

    with tab1:
        st.info("e-Maktabdan yozilmagan jurnallar va kamchiliklarni olish.")
        if st.button("🔍 Yozilmagan jurnallarni tekshirish", use_container_width=True):
            with st.spinner("e-Maktab tahlil qilinmoqda..."):
                data = emaktab_sorov(f"/teachers/api/problems?userId=1000002716779&date=null")
                if data:
                    c1, c2 = st.columns(2)
                    m_count = len(data.get('lessonsWithoutTitle', []))
                    b_count = len(data.get('lessonsWithoutMarks', []))
                    c1.metric("Mavzusiz darslar", m_count)
                    c2.metric("Bahosiz darslar", b_count)

                    if m_count > 0:
                        st.subheader("📝 Mavzusi yo'q darslar")
                        st.dataframe(pd.DataFrame(data['lessonsWithoutTitle']), use_container_width=True)
                    if b_count > 0:
                        st.subheader("🚫 Baho qo'yilmagan darslar")
                        st.dataframe(pd.DataFrame(data['lessonsWithoutMarks']), use_container_width=True)
                    if m_count == 0 and b_count == 0:
                        st.success("Tabriklaymiz! Hamma jurnallar to'liq. 🎉")
                else:
                    st.error("Ulanish xatosi. Cookie muddati tugagan bo'lishi mumkin.")

    with tab2:
        j_fayl = st.file_uploader("Excel faylni yuklang", type=['xlsx', 'xls'])
        if j_fayl:
            # Excel tahlil qilish logikasi (Sizning avvalgi kodingiz)
            st.success("Fayl yuklandi. Tahlil qilish uchun kodingizni bu yerga ulang.")

# --- 📂 MAKTAB BAZASI ---
elif menu == "📂 Maktab Bazasi":
    st.title("📂 Maktab Umumiy Bazasi")
    st.write("e-Maktabdan olingan real vaqt rejimidagi ma'lumotlar.")
    
    col_a, col_b, col_c = st.columns(3)
    
    if col_a.button("👨‍🏫 O'qituvchilar"):
        with st.spinner("Yuklanmoqda..."):
            res = emaktab_sorov(f"/api/school/{MAKTAB_ID}/teachers")
            if res: st.dataframe(pd.DataFrame(res), use_container_width=True)
            else: st.warning("Ma'lumot topilmadi.")

    if col_b.button("👨‍🎓 O'quvchilar"):
        with st.spinner("Yuklanmoqda..."):
            res = emaktab_sorov(f"/api/school/{MAKTAB_ID}/students")
            if res: st.dataframe(pd.DataFrame(res), use_container_width=True)
            else: st.warning("Ma'lumot topilmadi.")

    if col_c.button("📊 To'ldirish Hisoboti"):
        with st.spinner("Hisobot olinmoqda..."):
            res = emaktab_sorov(f"/api/reports/schools/filling/{MAKTAB_ID}")
            if res: st.json(res)
            else: st.error("Hisobotni yuklab bo'lmadi.")
