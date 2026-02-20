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
RUXSAT_ETILGAN_MASOFA =2 #0.2  # 200 metr

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
    # Bazaga "Keldi" yoki "Ketdi" holati yoziladi
    yangi_malumot = pd.DataFrame([[s_txt, v_txt, ism, holat]], 
                                columns=["Sana", "Vaqt", "F.I.SH", "Holat"])
    if not os.path.isfile(DAVOMAT_FAYLI):
        yangi_malumot.to_csv(DAVOMAT_FAYLI, index=False, encoding='utf-8-sig')
    else:
        yangi_malumot.to_csv(DAVOMAT_FAYLI, mode='a', header=False, index=False, encoding='utf-8-sig')

# --- LOG-IN ---
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

# --- SIDEBAR ---
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
# 🤖 AI MULOQOT
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
# 📊 JURNAL MONITORINGI
# =============================================
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
            try:
                df_j = pd.read_excel(j_fayl, engine='openpyxl')
            except:
                try: 
                    j_fayl.seek(0)
                    df_j = pd.read_excel(j_fayl, engine='xlrd')
                except:
                    j_fayl.seek(0)
                    df_j = pd.read_html(j_fayl, header=0)[0]
            
            df_j.columns = [str(c).replace('\n', ' ').strip() for c in df_j.columns]
            kamchiliklar = []
            if len(df_j.columns) >= 6:
                for _, row in df_j.iterrows():
                    name = str(row.iloc[0])
                    val = str(row.iloc[5])
                    if any(x in name.lower() for x in ["tuman", "muassasa", "o'qituvchi", "f.i.sh", "jami"]): continue
                    nums = re.findall(r'(\d+)', val)
                    if len(nums) >= 2:
                        b_bor, jami = int(nums[0]), int(nums[1])
                        if b_bor < jami:
                            kamchiliklar.append(f"❌ **{name}**: {jami - b_bor} ta chala ({val})")
                
                st.dataframe(df_j, use_container_width=True)
                res_txt = "✅ Hammasi to'liq!" if not kamchiliklar else "⚠️ **Kamchiliklar:**\n\n" + "\n".join(kamchiliklar)
                if not kamchiliklar: st.success(res_txt)
                else: st.warning(res_txt)
                
                if st.button("📢 Telegramga yuborish"):
                    clean_txt = res_txt.replace("**", "")
                    requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", 
                                  json={"chat_id": GURUH_ID, "text": f"📊 Monitoring\n\n{clean_txt}"})
                    st.success("Yuborildi!")
        except Exception as e: st.error(f"Xato: {e}")

# =============================================
# 📍 GPS DAVOMAT (Keldi/Ketdi mantiqi bilan)
# =============================================
elif menu == "📍 GPS Davomat":
    st.title("📍 Maktab Hududida Davomat")
    
    # Vaqt cheklovlari
    ertalabki_vaqt = (hozirgi_vaqt.hour < 8) or (hozirgi_vaqt.hour == 8 and hozirgi_vaqt.minute <= 30)
    kechki_vaqt = (hozirgi_vaqt.hour >= 13)

    st.write(f"🕒 **Hozirgi vaqt:** {hozirgi_vaqt.strftime('%H:%M')}")

    if ertalabki_vaqt or kechki_vaqt:
        # Holatni aniqlash
        ish_holati = "KELDI" if ertalabki_vaqt else "KETDI"
        st.success(f"🔓 Tizim ochiq (Holat: **{ish_holati}**)")
        
        with st.spinner("🛰 GPS aniqlanmoqda..."):
            loc = get_geolocation()
        
        if loc and 'coords' in loc:
            upos = (loc['coords']['latitude'], loc['coords']['longitude'])
            masofa = geodesic(upos, MAKTAB_KOORDINATASI).km
            
            if masofa <= RUXSAT_ETILGAN_MASOFA:
                st.success(f"📍 Hududdasiz ({round(masofa*1000)} m)")
                ism = st.text_input("F.I.SH (Ism-familiyangizni yozing):", key="fio_inp")
                
                if st.button(f"🔴 {ish_holati}NI TASDIQLASH", use_container_width=True):
                    if ism:
                        davomatni_saqlash(ism, ish_holati)
                        # Telegramga yuborish
                        tg_text = f"📍 #DAVOMAT\n👤 {ism}\n📅 {hozir.strftime('%d.%m.%Y')}\n⏰ {hozir.strftime('%H:%M')}\n🔄 Holat: **{ish_holati}**"
                        requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", 
                                      json={"chat_id": GURUH_ID, "text": tg_text, "parse_mode": "Markdown"})
                        st.balloons()
                        st.success(f"Muvaffaqiyatli qayd etildi: {ish_holati}")
                    else: st.error("Ismingizni yozing!")
            else: st.error(f"Maktab hududida emassiz! Masofa: {round(masofa*1000)} m")
        else: st.info("🛰 GPS signali kutilmoqda. Brauzerda ruxsat bering.")
    else:
        st.error("⚠️ Davomat yopiq (08:30 dan 13:00 gacha qabul qilinmaydi)")

    # --- ADMIN QISMI ---
    st.divider()
    with st.expander("📥 Davomat bazasini yuklab olish (Admin)"):
        if st.text_input("Admin parol:", type="password", key="ad_pass") == MONITORING_KODI:
            if os.path.exists(DAVOMAT_FAYLI):
                df_baza = pd.read_csv(DAVOMAT_FAYLI)
                st.dataframe(df_baza, use_container_width=True)
                
                buffer = io.BytesIO()
                with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                    df_baza.to_excel(writer, index=False)
                
                st.download_button(
                    label="📥 Excel faylni yuklab olish",
                    data=buffer.getvalue(),
                    file_name=f"davomat_{hozir.strftime('%d_%m')}.xlsx",
                    mime="application/vnd.ms-excel"
                )
            else: st.info("Hozircha baza bo'sh.")

