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
from gtts import gTTS
from streamlit_mic_recorder import mic_recorder

# --- ASOSIY SOZLAMALAR ---
MAKTAB_NOMI = "1-sonli umumta'lim maktabi"
DIREKTOR_FIO = "Mahmudov Matyoqub Narzulloyevich"
ASOSIY_PAROL = "informatika2024"
MONITORING_KODI = "admin777"

# MAKTAB KOORDINATALARI
MAKTAB_LAT = 39.4955640
MAKTAB_LON = 64.7924960
MAKTAB_KOORDINATASI = (MAKTAB_LAT, MAKTAB_LON)
RUXSAT_ETILGAN_MASOFA = 1

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
    st.error(f"Secrets xatosi: {e}")
    st.stop()

# --- GOOGLE SHEETS FUNKSIYASI ---
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
    # YANGI BO'LIM QO'SHILDI: "👩‍🏫 AI O'qituvchi"
    menu = st.radio("Bo'limni tanlang:", ["🤖 AI Muloqot", "👩‍🏫 AI O'qituvchi", "📊 Jurnal Monitoringi", "📍 GPS Davomat"])
    st.divider()
    if st.button("🚪 Chiqish", use_container_width=True):
        st.session_state.clear()
        st.rerun()

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
            except: st.error("AI band.")

# --- 👩‍🏫 AI O'QITUVCHI (YANGI BO'LIM) ---
elif menu == "👩‍🏫 AI O'qituvchi":
    st.title("👩‍🏫 Virtual O'qituvchi (Interaktiv Dars)")
    
    if "dars_active" not in st.session_state: st.session_state.dars_active = False
    if "current_mavzu" not in st.session_state: st.session_state.current_mavzu = ""
    if "lesson_history" not in st.session_state: st.session_state.lesson_history = []

    if not st.session_state.dars_active:
        mavzu_input = st.text_input("Dars mavzusini kiriting:", placeholder="Masalan: Quyosh tizimi")
        if st.button("🚀 Darsni boshlash"):
            if mavzu_input:
                st.session_state.current_mavzu = mavzu_input
                st.session_state.dars_active = True
                st.rerun()
    else:
        col1, col2 = st.columns([1, 1])
        with col1:
            st.subheader(f"📖 Mavzu: {st.session_state.current_mavzu}")
            if st.button("⬅️ Darsni tugatish"):
                st.session_state.dars_active = False
                st.session_state.lesson_history = []
                st.rerun()
            
            # AI Tushuntirishi (Kesh bilan)
            @st.cache_data
            def get_lesson_content(mavzu):
                res = client.chat.completions.create(
                    messages=[{"role": "system", "content": "Sen mehribon o'qituvchisan. Mavzuni qiziqarli va sodda tushuntir."},
                              {"role": "user", "content": f"{mavzu} haqida dars o't."}],
                    model="llama-3.3-70b-versatile"
                )
                return res.choices[0].message.content

            dars_text = get_lesson_content(st.session_state.current_mavzu)
            st.markdown(dars_text)
            
            if st.button("🔊 Ovozli eshitish"):
                tts = gTTS(text=dars_text[:1000], lang='tr')
                fp = io.BytesIO()
                tts.write_to_fp(fp)
                st.audio(fp, format="audio/mp3", autoplay=True)

        with col2:
            st.subheader("🙋‍♂️ Savol-javob")
            for m in st.session_state.lesson_history:
                with st.chat_message(m["role"]): st.write(m["content"])
            
            audio_data = mic_recorder(start_prompt="🎤 Savol berish", stop_prompt="🛑 To'xtatish", key='lesson_mic')
            if audio_data:
                trans = client.audio.transcriptions.create(file=("audio.wav", audio_data['bytes']), model="whisper-large-v3", language="uz")
                savol = trans.text
                st.session_state.lesson_history.append({"role": "user", "content": savol})
                res_j = client.chat.completions.create(
                    messages=[{"role": "system", "content": f"Sen {st.session_state.current_mavzu} mavzusi bo'yicha o'qituvchisan."},
                              {"role": "user", "content": savol}],
                    model="llama-3.3-70b-versatile"
                )
                st.session_state.lesson_history.append({"role": "assistant", "content": res_j.choices[0].message.content})
                st.rerun()

# --- 📊 JURNAL MONITORINGI ---
elif menu == "📊 Jurnal Monitoringi":
    st.title("📊 Jurnal Monitoringi")
    if "m_auth" not in st.session_state: st.session_state.m_auth = False
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
            try: df_j = pd.read_excel(j_fayl, engine='openpyxl')
            except:
                try: df_j = pd.read_excel(j_fayl, engine='xlrd')
                except: df_j = pd.read_html(j_fayl, header=0)[0]
            
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
                            kamchiliklar.append(f"❌ **{name}**: {jami - baho_bor} ta jurnal chala ({val})")
                st.subheader("📋 Tekshiruv Natijasi:")
                st.dataframe(df_j, use_container_width=True)
                xabar_text = "✅ Barcha jurnallar baholandi! " if not kamchiliklar else "⚠️ **Kamchiliklar:**\n\n" + "\n".join(kamchiliklar)
                if not kamchiliklar: st.success(xabar_text)
                else: st.warning(xabar_text)
                if st.button("📢 Telegramga yuborish"):
                    requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", json={"chat_id": GURUH_ID, "text": f"📊 Monitoring\n\n{xabar_text}", "parse_mode": "HTML"})
                    st.success("Telegramga yuborildi!")
        except Exception as e: st.error(f"Fayl xatosi: {e}")

# --- 📍 GPS DAVOMAT ---
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
                if st.session_state[key_name]: st.info("✅ Davomatdan o'tgansiz")
                else:
                    ism = st.text_input("F.I.SH:").strip()
                    if st.button(f"🔴 {ish_holati}NI TASDIQLASH"):
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
            else: st.error(f"Hududda emassiz! Masofa: {round(masofa*1000)} m")
    else: st.error("⚠️ Davomat yopiq!")
    
    st.divider()
    if st.checkbox("Google Jadvalni ko'rish (Admin)"):
        if st.text_input("Admin kod:", type="password", key="adm_v") == MONITORING_KODI:
            conn = st.connection("gsheets", type=GSheetsConnection)
            df_gsheet = conn.read(ttl=0)
            st.dataframe(df_gsheet, use_container_width=True)
            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
                df_gsheet.to_excel(writer, index=False, sheet_name='Davomat')
            st.download_button(label="📥 Excel yuklab olish", data=buffer, file_name=f"davomat_{hozir.strftime('%d_%m_%Y')}.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
