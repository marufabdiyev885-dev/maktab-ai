# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
import os
import requests
import re
import io
import datetime as dt
import pytz
import asyncio
import edge_tts
from groq import Groq
from streamlit_js_eval import get_geolocation
from geopy.distance import geodesic
from streamlit_gsheets import GSheetsConnection
from streamlit_mic_recorder import mic_recorder
from streamlit_lottie import st_lottie

# --- 1. SEO VA ASOSIY SOZLAMALAR ---
# Bu qism Google botlari saytingizni topishi va to'g'ri indekslashi uchun xizmat qiladi
MAKTAB_NOMI = "1-sonli umumta'lim maktabi"
DIREKTOR_FIO = "Mahmudov Matyoqub Narzulloyevich"
ASOSIY_PAROL = "informatika2024"
MONITORING_KODI = "admin777"

st.set_page_config(
    page_title=f"{MAKTAB_NOMI} - Rasmiy AI Boshqaruv Platformasi",
    page_icon="🏫",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'About': f"# {MAKTAB_NOMI} AI tizimi\nUshbu platforma maktab ma'muriyati, o'qituvchilari va o'quvchilari uchun raqamli yordamchi sifatida yaratilgan."
    }
)

# Google uchun yashirin kalit so'zlar (SEO)
st.markdown(f"""
    <div style="display:none">
        <h1>{MAKTAB_NOMI} AI Tizimi</h1>
        <p>Maktab boshqaruv tizimi, o'qituvchilar davomati, GPS nazorat, AI robot o'qituvchi, 
        maktab reytingi, eMaktab tahlili, {DIREKTOR_FIO}, raqamli maktab.</p>
    </div>
    """, unsafe_allow_html=True)

# MAKTAB KOORDINATALARI
MAKTAB_LAT = 39.4955640
MAKTAB_LON = 64.7924960
MAKTAB_KOORDINATASI = (MAKTAB_LAT, MAKTAB_LON)
RUXSAT_ETILGAN_MASOFA = 1 # 1 km

# --- 2. O'ZBEKISTON VAQTINI OLISH ---
uzb_tz = pytz.timezone('Asia/Tashkent')
hozir = dt.datetime.now(uzb_tz)
hozirgi_vaqt = hozir.time()

# --- 3. SECRETS TEKSHIRUVI ---
try:
    BOT_TOKEN = st.secrets["TELEGRAM_BOT_TOKEN"]
    GURUH_ID = st.secrets["TELEGRAM_GURUH_ID"]
    GROQ_API_KEY = st.secrets["GROQ_API_KEY"]
    client = Groq(api_key=GROQ_API_KEY)
except Exception as e:
    st.error("Secrets (API kalitlar) sozlanmagan. Iltimos, Streamlit Cloud sozlamalarini tekshiring.")
    st.stop()

# --- 4. ANIMATSIYA VA OVOZ FUNKSIYALARI ---
def load_lottieurl(url):
    r = requests.get(url)
    return r.json() if r.status_code == 200 else None

robot_anim = load_lottieurl("https://lottie.host/8659103c-83b3-4f93-9d56-7463f82637f8/S9v12T87p0.json")

async def generate_uz_voice(text):
    communicate = edge_tts.Communicate(text, "uz-UZ-SardorNeural")
    output_path = "output_audio.mp3"
    await communicate.save(output_path)
    return output_path

# --- 5. GOOGLE SHEETS FUNKSIYASI ---
def davomatni_gsheetsga_yoz(ism, holat):
    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        try:
            df = conn.read(ttl=0)
        except:
            df = pd.DataFrame(columns=["Sana", "Vaqt", "F.I.SH", "Holat"])
        
        yangi_qator = pd.DataFrame({
            "Sana": [hozir.strftime("%d.%m.%Y")],
            "Vaqt": [hozir.strftime("%H:%M:%S")],
            "F.I.SH": [ism],
            "Holat": [holat]
        })
        df = pd.concat([df, yangi_qator], ignore_index=True)
        conn.update(data=df)
        return True
    except Exception as e:
        st.error(f"Google Sheets xatosi: {e}")
        return False

# --- 6. LOG-IN TIZIMI ---
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.title("🏫 " + MAKTAB_NOMI)
        st.subheader("Raqamli Boshqaruv Platformasi")
        p_in = st.text_input("Kirish paroli:", type="password")
        if st.button("Tizimga kirish", use_container_width=True):
            if p_in == ASOSIY_PAROL:
                st.session_state.authenticated = True
                st.rerun()
            else:
                st.error("Parol noto'g'ri!")
    st.stop()

# --- 7. SIDEBAR MENYU ---
with st.sidebar:
    st_lottie(robot_anim, height=150, key="side_robot")
    st.title("Asosiy Menyu")
    st.write(f"👤 **Direktor:** \n{DIREKTOR_FIO}")
    st.divider()
    menu = st.radio("Bo'limni tanlang:", 
                    ["🤖 AI Muloqot", "👩‍🏫 AI O'qituvchi", "📊 Jurnal Monitoringi", "📍 GPS Davomat"])
    st.divider()
    if st.button("🚪 Chiqish", use_container_width=True):
        st.session_state.authenticated = False
        st.rerun()

# --- 8. BO'LIMLAR ---

# 🤖 AI MULOQOT
if menu == "🤖 AI Muloqot":
    st.title("🤖 Maktab AI Yordamchisi")
    st.caption("Savollaringizga AI orqali javob oling (Llama 3.3)")
    
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
    
    savol = st.chat_input("Metodik yordam yoki ma'lumot kerakmi?")
    if savol:
        st.session_state.messages.append({"role": "user", "content": savol})
        with st.chat_message("user"):
            st.markdown(savol)
        
        with st.chat_message("assistant"):
            try:
                res = client.chat.completions.create(
                    messages=[{"role": "system", "content": "Sen maktab IT yordamchisisan."}] + st.session_state.messages[-5:],
                    model="llama-3.3-70b-versatile",
                )
                ans = res.choices[0].message.content
                st.markdown(ans)
                st.session_state.messages.append({"role": "assistant", "content": ans})
            except:
                st.error("AI bilan aloqa uzildi.")

# 👩‍🏫 AI O'QITUVCHI
elif menu == "👩‍🏫 AI O'qituvchi":
    st.title("👩‍🏫 Virtual Robot O'qituvchi")
    
    if "dars_active" not in st.session_state: st.session_state.dars_active = False
    if "lesson_history" not in st.session_state: st.session_state.lesson_history = []

    if not st.session_state.dars_active:
        mavzu_input = st.text_input("Dars mavzusini kiriting:", placeholder="Masalan: Quyosh tizimi")
        if st.button("🚀 Darsni boshlash"):
            if mavzu_input:
                st.session_state.current_mavzu = mavzu_input
                st.session_state.dars_active = True
                res = client.chat.completions.create(
                    messages=[{"role": "system", "content": "Sen maktab o'qituvchisisan. Mavzuni qisqa va qiziqarli boshla."},
                              {"role": "user", "content": f"{mavzu_input} haqida darsni boshla."}],
                    model="llama-3.3-70b-versatile"
                )
                st.session_state.lesson_history.append({"role": "assistant", "content": res.choices[0].message.content})
                st.rerun()
    else:
        col_anim, col_info = st.columns([1, 2])
        with col_anim:
            st_lottie(robot_anim, height=300)
        with col_info:
            st.subheader(f"📖 Mavzu: {st.session_state.current_mavzu}")
            if st.button("❌ Darsni yakunlash"):
                st.session_state.dars_active = False
                st.session_state.lesson_history = []
                st.rerun()

        st.divider()
        for m in st.session_state.lesson_history:
            with st.chat_message(m["role"]): st.write(m["content"])

        if st.session_state.lesson_history and st.session_state.lesson_history[-1]["role"] == "assistant":
            v_text = st.session_state.lesson_history[-1]["content"][:800]
            v_file = asyncio.run(generate_uz_voice(v_text))
            st.audio(v_file, format="audio/mp3", autoplay=True)

        audio_data = mic_recorder(start_prompt="🎤 Savol berish", stop_prompt="✅ Yuborish", key='robot_mic')
        if audio_data:
            audio_bio = io.BytesIO(audio_data['bytes'])
            audio_bio.name = "audio.wav"
            trans = client.audio.transcriptions.create(file=audio_bio, model="whisper-large-v3", language="uz")
            user_say = trans.text
            if user_say:
                st.session_state.lesson_history.append({"role": "user", "content": user_say})
                res_j = client.chat.completions.create(
                    messages=[{"role": "system", "content": f"Sen {st.session_state.current_mavzu} bo'yicha ustozsan."}] + st.session_state.lesson_history[-4:],
                    model="llama-3.3-70b-versatile"
                )
                st.session_state.lesson_history.append({"role": "assistant", "content": res_j.choices[0].message.content})
                st.rerun()

# 📊 JURNAL MONITORINGI
elif menu == "📊 Jurnal Monitoringi":
    st.title("📊 eMaktab Monitoring Tizimi")
    m_input = st.text_input("Monitoring kodi:", type="password")
    if m_input == MONITORING_KODI:
        j_fayl = st.file_uploader("eMaktab Excel faylini yuklang", type=['xlsx', 'xls', 'html'])
        if j_fayl:
            try:
                df_j = pd.read_excel(j_fayl) if j_fayl.name.endswith('x') else pd.read_html(j_fayl)[0]
                st.success("Fayl tahlil qilinmoqda...")
                st.dataframe(df_j)
                if st.button("📢 Natijalarni Telegramga yuborish"):
                    requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", 
                                  json={"chat_id": GURUH_ID, "text": f"📊 {MAKTAB_NOMI}: Jurnal hisoboti yuklandi."})
                    st.success("Telegramga yuborildi!")
            except: st.error("Faylni o'qib bo'lmadi.")
    else: st.warning("Ushbu bo'lim faqat ma'muriyat uchun.")

# 📍 GPS DAVOMAT
elif menu == "📍 GPS Davomat":
    st.title("📍 Smart GPS Davomat")
    st.write(f"Bugungi sana: {hozir.strftime('%d.%m.%Y')}")
    
    with st.spinner("🛰 GPS aniqlanmoqda..."):
        loc = get_geolocation()
    
    if loc:
        upos = (loc['coords']['latitude'], loc['coords']['longitude'])
        masofa = geodesic(upos, MAKTAB_KOORDINATASI).km
        
        if masofa <= RUXSAT_ETILGAN_MASOFA:
            st.success(f"📍 Siz maktab hududidasiz! (Masofa: {round(masofa*1000)} m)")
            ism = st.text_input("To'liq ism-sharifingizni kiriting:")
            if st.button("✅ Kelganimni tasdiqlash"):
                if ism:
                    if davomatni_gsheetsga_yoz(ism, "KELDI"):
                        st.balloons()
                        st.success("Davomat saqlandi!")
                else: st.error("Ismni kiriting!")
        else:
            st.error(f"Siz maktab hududida emassiz! (Masofa: {round(masofa*1000)} m)")
    else:
        st.warning("Iltimos, brauzeringizda lokatsiyaga ruxsat bering.")
