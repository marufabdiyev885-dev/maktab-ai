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
RUXSAT_ETILGAN_MASOFA = 0.2 

st.set_page_config(page_title=MAKTAB_NOMI, layout="wide", page_icon="🏫")

# --- O'ZBEKISTON VAQTINI OLISH ---
uzb_tz = pytz.timezone('Asia/Tashkent')
hozir = dt.datetime.now(uzb_tz)
hozirgi_vaqt = hozir.time()

try:
    BOT_TOKEN = st.secrets["TELEGRAM_BOT_TOKEN"]
    GURUH_ID = st.secrets["TELEGRAM_GURUH_ID"]
    GROQ_API_KEY = st.secrets["GROQ_API_KEY"]
    client = Groq(api_key=GROQ_API_KEY)
except Exception as e:
    st.error("Secrets xatolik: " + str(e))
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
        except Exception: continue
    return all_sheets

sheets_baza = yuklash()

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.title("🏫 " + MAKTAB_NOMI)
        p_in = st.text_input("Kirish paroli:", type="password", key="main_auth_key")
        if st.button("Kirish", key="main_auth_btn", use_container_width=True):
            if p_in == ASOSIY_PAROL:
                st.session_state.authenticated = True
                st.rerun()
            else: st.error("Parol xato!")
    st.stop()

with st.sidebar:
    st.title("🏛 " + MAKTAB_NOMI)
    st.write("👤 **Direktor:** " + DIREKTOR_FIO)
    st.divider()
    menu = st.radio("Bo'limni tanlang:", ["🤖 AI Muloqot", "📊 Jurnal Monitoringi", "📍 GPS Davomat"], key="nav_menu")
    st.divider()
    if st.button("🚪 Chiqish", use_container_width=True):
        st.session_state.clear()
        st.rerun()

# =============================================
# AI MULOQOT
# =============================================
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

# =============================================
# JURNAL MONITORINGI (TUGMA QAYTARILDI)
# =============================================
elif menu == "📊 Jurnal Monitoringi":
    st.title("📊 Jurnal Monitoringi")
    if not st.session_state.get("m_auth", False):
        m_input = st.text_input("Monitoring kodi:", type="password", key="mon_input")
        if st.button("Kirish", key="mon_btn"):
            if m_input == MONITORING_KODI:
                st.session_state.m_auth = True
                st.rerun()
            else: st.error("Kod xato!")
        st.stop()
    
    j_fayl = st.file_uploader("Excel faylni yuklang", type=['xlsx', 'xls'])
    if j_fayl:
        fayl_bytes = j_fayl.read()
        try:
            if fayl_bytes[:200].strip().lower().startswith(b'<'):
                df_j = pd.read_html(io.BytesIO(fayl_bytes), header=0)[0]
            else:
                df_j = pd.read_excel(io.BytesIO(fayl_bytes))
            
            df_j.columns = [str(c).replace('\n', ' ').strip() for c in df_j.columns]
            st.dataframe(df_j, use_container_width=True)
            
            kamchiliklar = []
            skip_words = ["tuman", "muassasa", "qituvchi", "f.i.sh", "jami"]
            
            if len(df_j.columns) >= 6:
                for _, row in df_j.iterrows():
                    name = str(row.iloc[0]).strip()
                    val = str(row.iloc[5]).strip()
                    if not name or "nan" in name.lower() or any(x in name.lower() for x in skip_words):
                        continue
                    
                    nums = re.findall(r'\d+', val)
                    if len(nums) >= 2:
                        bor, jami = int(nums[0]), int(nums[1])
                        if jami > 0 and bor < jami:
                            kamchiliklar.append({
                                "Xodim": name, 
                                "Bajarilgan": bor, 
                                "Jami": jami, 
                                "Farq": jami - bor,
                                "Foiz": f"{round(bor/jami*100)}%"
                            })
                
                if kamchiliklar:
                    st.warning(f"{len(kamchiliklar)} ta kamchilik aniqlandi.")
                    df_kam = pd.DataFrame(kamchiliklar)
                    st.dataframe(df_kam, use_container_width=True)
                    
                    # TELEGRAM TUGMASI MANA SHU YERDA:
                    if st.button("📤 Telegramga yuborish", use_container_width=True):
                        xabar = f"📊 *{MAKTAB_NOMI} Jurnal Monitoringi*\n\n"
                        for k in kamchiliklar:
                            xabar += f"❌ {k['Xodim']}: {k['Bajarilgan']}/{k['Jami']} ({k['Foiz']})\n"
                        
                        resp = requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", 
                                      json={"chat_id": GURUH_ID, "text": xabar, "parse_mode": "Markdown"})
                        if resp.status_code == 200:
                            st.success("Telegramga muvaffaqiyatli yuborildi!")
                        else: st.error("Yuborishda xatolik!")
                else:
                    st.success("Hamma jurnallar to'liq! 🎉")
            else: st.error("Fayl ustunlari mos kelmadi.")
        except Exception as e: st.error(f"Xato: {e}")

# =============================================
# GPS DAVOMAT
# =============================================
elif menu == "📍 GPS Davomat":
    st.title("📍 Maktab Hududida Davomat")
    is_morning = (hozirgi_vaqt.hour < 8) or (hozirgi_vaqt.hour == 8 and hozirgi_vaqt.minute <= 30)
    is_afternoon = (hozirgi_vaqt.hour >= 13)
    st.write(f"🕒 **Vaqt:** {hozirgi_vaqt.strftime('%H:%M')}")

    if is_morning or is_afternoon:
        with st.spinner("🛰 GPS aniqlanmoqda..."):
            loc = get_geolocation()
        if loc and 'coords' in loc:
            upos = (loc['coords']['latitude'], loc['coords']['longitude'])
            masofa = geodesic(upos, MAKTAB_KOORDINATASI).km
            if masofa <= RUXSAT_ETILGAN_MASOFA:
                st.success(f"📍 Hududdasiz ({round(masofa*1000)} m)")
                ism = st.text_input("F.I.SH:", key="fio_dav")
                if st.button("🔴 TASDIQLASH", use_container_width=True):
                    if ism:
                        holat = "KELDI" if is_morning else "KETDI"
                        davomatni_saqlash(ism, holat)
                        tg_txt = f"📍 #DAVOMAT\n👤 {ism}\n📅 {hozir.strftime('%d.%m.%Y')}\n⏰ {hozir.strftime('%H:%M:%S')}\n🔄 {holat}"
                        requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", json={"chat_id": GURUH_ID, "text": tg_txt})
                        st.balloons()
                    else: st.error("Ism yozing!")
            else: st.error(f"Tashqaridasiz! ({round(masofa*1000)} m)")
        else: st.info("GPS ruxsatini bering.")
    else: st.error("⚠️ Davomat yopiq.")

    with st.expander("📥 Admin (Baza)"):
        if st.text_input("Kod:", type="password", key="ad_p") == MONITORING_KODI:
            if os.path.exists(DAVOMAT_FAYLI):
                df_d = pd.read_csv(DAVOMAT_FAYLI)
                st.dataframe(df_d)
                out = io.BytesIO()
                df_d.to_excel(out, index=False)
                st.download_button("📥 Yuklash", out.getvalue(), "davomat.xlsx")
