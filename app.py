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

# Koordinatalar
MAKTAB_LAT = 39.4955640
MAKTAB_LON = 64.7924960
MAKTAB_KOORDINATASI = (MAKTAB_LAT, MAKTAB_LON)
RUXSAT_ETILGAN_MASOFA = 1.0  # 1 km

st.set_page_config(page_title=MAKTAB_NOMI, layout="wide", page_icon="🏫")

# --- VAQT ---
uzb_tz = pytz.timezone('Asia/Tashkent')
hozir = dt.datetime.now(uzb_tz)
hozirgi_vaqt = hozir.time()

# --- SECRETS ---
try:
    BOT_TOKEN = st.secrets["TELEGRAM_BOT_TOKEN"]
    GURUH_ID = st.secrets["TELEGRAM_GURUH_ID"]
    GROQ_API_KEY = st.secrets["GROQ_API_KEY"]
    client = Groq(api_key=GROQ_API_KEY)
except Exception as e:
    st.error(f"Secrets (API kalitlar) sozlanmagan: {e}")
    st.stop()

# --- GOOGLE SHEETSGA SAQLASH ---
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

# --- LOG-IN ---
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
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
    st.title("🏛 Menu")
    menu = st.radio("Bo'limni tanlang:", ["👥 Ro'yxatlar", "🤖 AI Muloqot", "📊 Jurnal Monitoringi", "📍 GPS Davomat"])
    if st.button("🚪 Chiqish"):
        st.session_state.clear()
        st.rerun()

# --- 1. 👥 RO'YXATLAR (GitHub'dagi fayllar) ---
if menu == "👥 Ro'yxatlar":
    st.title("📋 Maktab bazasidagi ro'yxatlar")
    tab1, tab2 = st.tabs(["👨‍🏫 O'qituvchilar", "🎓 O'quvchilar"])
    
    with tab1:
        f_oqt = "baza_o'qituvchilar.xlsx"
        if os.path.exists(f_oqt):
            df = pd.read_excel(f_oqt)
            st.write(f"Jami: {len(df)}")
            st.dataframe(df, use_container_width=True)
        else: st.warning(f"{f_oqt} fayli topilmadi.")

    with tab2:
        f_oqv = "baza_o'quvchilar.xlsx"
        if os.path.exists(f_oqv):
            df = pd.read_excel(f_oqv)
            st.write(f"Jami: {len(df)}")
            st.dataframe(df, use_container_width=True)
        else: st.warning(f"{f_oqv} fayli topilmadi.")

# --- 2. 🤖 AI MULOQOT ---
elif menu == "🤖 AI Muloqot":
    st.title("🤖 Maktab AI Yordamchisi")
    if "messages" not in st.session_state: st.session_state.messages = []
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]): st.markdown(msg["content"])
    
    savol = st.chat_input("Savol...")
    if savol:
        st.session_state.messages.append({"role": "user", "content": savol})
        with st.chat_message("user"): st.markdown(savol)
        res = client.chat.completions.create(
            messages=[{"role": "system", "content": "Sen maktab yordamchisisan."}] + st.session_state.messages[-5:],
            model="llama-3.3-70b-versatile"
        )
        ans = res.choices[0].message.content
        st.session_state.messages.append({"role": "assistant", "content": ans})
        with st.chat_message("assistant"): st.markdown(ans)

# --- 3. 📊 JURNAL MONITORINGI ---
elif menu == "📊 Jurnal Monitoringi":
    st.title("📊 Monitoring (eMaktab Excel)")
    j_fayl = st.file_uploader("eMaktabdan olingan faylni yuklang", type=['xlsx', 'xls', 'html'])
    if j_fayl:
        try:
            # Faylni o'qish (HTML formatini ham hisobga oladi)
            try: df_j = pd.read_html(j_fayl)[0]
            except: df_j = pd.read_excel(j_fayl)
            
            st.dataframe(df_j, use_container_width=True)
            
            kamchiliklar = []
            for _, row in df_j.iterrows():
                name = str(row.iloc[0])
                if any(x in name.lower() for x in ["tuman", "o'qituvchi", "f.i.sh"]): continue
                
                # Regex tahlil (Baholar ustuni - 5-ustun deb faraz qilamiz)
                if len(row) >= 6:
                    val = str(row.iloc[5])
                    nums = re.findall(r'(\d+)', val)
                    if len(nums) >= 2 and int(nums[0]) < int(nums[1]):
                        kamchiliklar.append(f"❌ {name}: {int(nums[1]) - int(nums[0])} ta chala ({val})")
            
            if kamchiliklar:
                msg = "⚠️ **Monitoring Kamchiliklari:**\n\n" + "\n".join(kamchiliklar)
                st.warning(msg)
                if st.button("📢 Telegramga yuborish"):
                    requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", json={"chat_id": GURUH_ID, "text": msg})
                    st.success("Yuborildi!")
            else: st.success("✅ Kamchiliklar topilmadi.")
        except Exception as e: st.error(f"Xato: {e}")

# --- 4. 📍 GPS DAVOMAT ---
elif menu == "📍 GPS Davomat":
    st.title("📍 GPS Davomat")
    loc = get_geolocation()
    if loc:
        upos = (loc['coords']['latitude'], loc['coords']['longitude'])
        masofa = geodesic(upos, MAKTAB_KOORDINATASI).km
        if masofa <= RUXSAT_ETILGAN_MASOFA:
            st.success(f"📍 Maktab hududidasiz ({round(masofa*1000)} m)")
            ism = st.text_input("F.I.SH (Ismingizni kiriting):")
            if st.button("🔴 TASDIQLASH"):
                if ism and davomatni_gsheetsga_yoz(ism, "KELDI"):
                    st.balloons()
                    st.success("Davomat qayd etildi!")
        else: st.error(f"Siz maktab hududidan uzoqdasiz! ({round(masofa*1000)} m)")
