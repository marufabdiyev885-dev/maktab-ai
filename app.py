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

# --- 🤖 AI MULOQOT (TEJAMKOR VARIANT) ---
# --- 🤖 AI MULOQOT (TO'G'RILANGAN VARIANT) ---
elif menu == "🤖 AI Muloqot":
    st.title("🤖 Aqlli va Farosatli Muloqot")
    
    # Ma'rufjon aka uchun maxsus salomlashish
    if "greeted" not in st.session_state:
        with st.chat_message("assistant"):
            st.markdown(f"**Assalomu alaykum, Ma'rufjon aka!** Bugun qaysi ma'lumotni titib chiqamiz?")
        st.session_state.greeted = True

    if savol := st.chat_input("Sinf (1-A) yoki ismni yozing..."):
        with st.chat_message("user"): 
            st.markdown(savol)
        
        q = savol.lower().strip()
        
        # 1. FAROSAT VA O'ZARO HURMAT (Hardcoded javoblar)
        rahmat_gaplar = ["rahmat", "zo'r", "ajoyib", "gap yo'q", "baraka top", "ishlaringga omad"]
        salom_gaplar = ["salom", "assalom", "qalaysan", "yaxshimisan"]
        xayr_gaplar = ["xayr", "sog' bo'l", "mayli", "tushunarli"]

        with st.chat_message("assistant"):
            if any(x in q for x in rahmat_gaplar):
                st.markdown(random.choice([
                    "Arzimaydi, Ma'rufjon aka! Sizga xizmat qilish — men uchun zavq.",
                    "Siz ham sog' bo'ling aka! Doim xizmatingizdaman.",
                    "Harakat qilyapmiz-da aka, sizdek odamga yordam berish bizga sharaf!"
                ]))
            elif any(x in q for x in salom_gaplar):
                st.markdown("Vaalaykum assalom! Ma'rufjon aka, o'zingiz charchamayapsizmi? Qaysi ma'lumot kerak?")
            elif any(x in q for x in xayr_gaplar):
                st.markdown("Xo'p bo'ladi aka, sog' bo'ling! Ishlaringizga omad!")
            
            # 2. QIDIRUV VA AI TAHLILI (GitHub fayllari bilan)
            else:
                topildi = False
                baza_matni = ""
                
                # Fayllarni tekshirish va qidirish
                fayllar = ["baza_o'qituvchilar.xlsx", "baza_o'quvchilar.xlsx"]
                
                for f_nomi in fayllar:
                    if os.path.exists(f_nomi):
                        try:
                            df_temp = pd.read_excel(f_nomi).astype(str)
                            # Foydalanuvchi yozgan so'z qatnashgan qatorlarni filtrlash
                            mask = df_temp.apply(lambda row: row.str.contains(q, case=False).any(), axis=1)
                            filtered_df = df_temp[mask]
                            
                            if not filtered_df.empty:
                                baza_matni += f"\nFayl: {f_nomi}\n{filtered_df.to_string(index=False)}\n"
                                topildi = True
                        except Exception as e:
                            st.error(f"Faylni o'qishda xato: {e}")

                if topildi:
                    # Token tejash uchun AI-ga faqat topilgan qatorlarni yuboramiz
                    prompt_tizim = f"Sen maktab yordamchisisan. Ma'rufjon aka '{savol}' deb so'radi. Mana bazadan topilgan ma'lumotlar:\n{baza_matni}\nUshbu ma'lumotlar asosida unga do'stona javob ber."
                    try:
                        res = client.chat.completions.create(
                            messages=[{"role": "system", "content": prompt_tizim}],
                            model="llama-3.3-70b-versatile"
                        )
                        st.markdown(res.choices[0].message.content)
                    except:
                        st.markdown("Aka, ma'lumotni topdim, lekin AI bilan bog'lanishda ozgina texnik nosozlik bo'ldi. Mana ma'lumotlar:")
                        st.write(baza_matni)
                else:
                    st.warning("Aka, topolmadim. Balki ismni qisqaroq yozarmiz?")# --- 3. 📊 JURNAL MONITORINGI ---
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
    
    # Lokatsiyani olish
    loc = get_geolocation()
    
    if loc is None:
        st.warning("📍 Lokatsiya aniqlanmoqda yoki ruxsat berilmagan. Iltimos, brauzerda lokatsiyaga ruxsat bering.")
    else:
        try:
            # Ma'lumot borligini tekshirish (KeyError oldini olish)
            if 'coords' in loc:
                lat = loc['coords']['latitude']
                lon = loc['coords']['longitude']
                upos = (lat, lon)
                
                # Masofani hisoblash
                masofa = geodesic(upos, MAKTAB_KOORDINATASI).km
                
                if masofa <= RUXSAT_ETILGAN_MASOFA:
                    st.success(f"📍 Maktab hududidasiz ({round(masofa*1000)} m)")
                    ism = st.text_input("F.I.SH (Ismingizni kiriting):")
                    
                    if st.button("🔴 TASDIQLASH"):
                        if ism:
                            if davomatni_gsheetsga_yoz(ism, "KELDI"):
                                st.balloons()
                                st.success("Davomat qayd etildi!")
                        else:
                            st.error("Iltimos, ismingizni kiriting!")
                else:
                    st.error(f"Siz maktab hududidan uzoqdasiz! ({round(masofa, 2)} km)")
                    st.info(f"Sizning manzilingiz: {lat}, {lon}")
            else:
                st.error("GPS ma'lumotlarini o'qib bo'lmadi.")
        except Exception as e:
            st.error(f"GPS xatoligi: {e}")



