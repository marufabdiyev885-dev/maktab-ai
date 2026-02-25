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
                    st.warning("Aka, topolmadim. Balki ismni qisqaroq yozarmiz?")
                   # --- JURNAL MONITORINGI ---
elif menu == "📊 Jurnal Monitoringi":
    st.title("📊 Jurnal Monitoringi")
    
    if "m_auth" not in st.session_state:
        st.session_state.m_auth = False
        
    if not st.session_state.m_auth:
        m_input = st.text_input("Monitoring kodi:", type="password", key="mon_input")
        if st.button("Kirish", key="mon_btn"):
            if m_input == MONITORING_KODI:
                st.session_state.m_auth = True
                st.rerun()
            else:
                st.error("Kod xato!")
        st.stop()
    
    j_fayl = st.file_uploader("Excel faylni yuklang", type=['xlsx', 'xls', 'html'], key="uploader")
    
    if j_fayl:
        try:
            # Faylni o'qishning bir nechta usulini sinab ko'ramiz
            try:
                # 1-usul: Standart Excel (openpyxl)
                df_j = pd.read_excel(j_fayl, engine='openpyxl')
            except Exception:
                try:
                    # 2-usul: Eski Excel (.xls - xlrd)
                    j_fayl.seek(0)
                    df_j = pd.read_excel(j_fayl, engine='xlrd')
                except Exception:
                    try:
                        # 3-usul: HTML formatidagi Excel
                        j_fayl.seek(0)
                        df_j = pd.read_html(j_fayl, header=0)[0]
                    except Exception:
                        # 4-usul: Engine belgilamasdan urinish
                        j_fayl.seek(0)
                        df_j = pd.read_excel(j_fayl)

            # Ustunlarni tozalash
            df_j.columns = [str(c).replace('\n', ' ').strip() for c in df_j.columns]
            
            kamchiliklar = []
            if len(df_j.columns) >= 6:
                for _, row in df_j.iterrows():
                    name = str(row.iloc[0]) # 0-ustun: Ismlar
                    val = str(row.iloc[5])  # 5-ustun: Baholar holati
                    
                    if any(x in name.lower() for x in ["tuman", "muassasa", "o'qituvchi", "f.i.sh"]):
                        continue
                        
                    nums = re.findall(r'(\d+)', val)
                    if len(nums) >= 2:
                        baho_bor, jami = int(nums[0]), int(nums[1])
                        if baho_bor < jami:
                            farq = jami - baho_bor
                            kamchiliklar.append(f"❌ **{name}**: {farq} ta jurnal chala ({val})")
                
                st.subheader("📋 Tekshiruv Natijasi:")
                st.dataframe(df_j, use_container_width=True)
                
                xabar_text = "✅ Barcha jurnallar baholandi! " if not kamchiliklar else "⚠️ **Kamchiliklar:**\n\n" + "\n".join(kamchiliklar)
                if not kamchiliklar: st.success(xabar_text)
                else: st.warning(xabar_text)
                
                st.divider()
                if st.button("📢 Telegramga yuborish", key="tg_btn"):
                    requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", 
                                 json={"chat_id": GURUH_ID, "text": f"<b>📊 Monitoring</b>\n\n{xabar_text}", "parse_mode": "HTML"})
                    st.success("✅ Telegramga yuborildi!")
            else:
                st.error(f"Faylda ustunlar yetarli emas. Topildi: {len(df_j.columns)} ta.")
                
        except Exception as e:
            st.error(f"Faylni o'qishda kutilmagan xato: {e}")



elif menu == "📍 GPS Davomat":
    st.title("📍 GPS Davomat (Google Sheets)")
    
    # Vaqt chegaralari
    ertalab_bosh = dt.time(7, 30)
    ertalab_tugash = dt.time(8, 30)
    kechki_bosh = dt.time(13, 0)
    kechki_tugash = dt.time(21, 0)

    is_ertalab = ertalab_bosh <= hozirgi_vaqt <= ertalab_tugash
    is_kechki = kechki_bosh <= hozirgi_vaqt <= kechki_tugash

    if is_ertalab or is_kechki:
        ish_holati = "KELDI" if is_ertalab else "KETDI"
        bugun_sana = hozir.strftime("%d.%m.%Y")
        
        # Google Sheets-dan bugungi ma'lumotlarni o'qish (tekshirish uchun)
        conn = st.connection("gsheets", type=GSheetsConnection)
        df_check = conn.read(ttl=0)
        
        # Joriy sessiyada yoki bazada ushbu holat qayd etilganini aniqlash
        # (Bu qism xodimning ismini kiritgandan keyin ishlaydi, lekin bizga umumiy holat kerak)
        
        with st.spinner("🛰 GPS aniqlanmoqda..."):
            loc = get_geolocation()
        
        if loc and 'coords' in loc:
            upos = (loc['coords']['latitude'], loc['coords']['longitude'])
            masofa = geodesic(upos, MAKTAB_KOORDINATASI).km
            
            if masofa <= RUXSAT_ETILGAN_MASOFA:
                st.success(f"📍 Hududdasiz ({round(masofa*1000)} m)")
                
                # Ism kiritish maydoni (agar hali tasdiqlanmagan bo'lsa)
                key_name = f"submitted_{ish_holati}_{bugun_sana}"
                
                if key_name not in st.session_state:
                    st.session_state[key_name] = False

                if st.session_state[key_name]:
                    status_text = "Siz davomatdan o'tdingiz" if is_ertalab else "Siz maktabdan chiqdingiz"
                    st.info(f"✅ **{status_text}**")
                else:
                    ism = st.text_input("F.I.SH (Ism-familiyangiz):").strip()
                    
                    if st.button(f"🔴 {ish_holati}NI TASDIQLASH", use_container_width=True):
                        if ism:
                            # Bazada aynan shu odam shu holatda borligini tekshirish
                            takroriy = df_check[(df_check['F.I.SH'] == ism) & 
                                                (df_check['Sana'] == bugun_sana) & 
                                                (df_check['Holat'] == ish_holati)]
                            
                            if not takroriy.empty:
                                st.warning(f"⚠️ {ism}, siz allaqachon qayd etilgansiz!")
                                st.session_state[key_name] = True
                                st.rerun()
                            else:
                                if davomatni_gsheetsga_yoz(ism, ish_holati):
                                    # Telegramga yuborish
                                    #tg_text = f"📍 #DAVOMAT\n👤 {ism}\n📅 {bugun_sana}\n⏰ {hozir.strftime('%H:%M')}\n🔄 {ish_holati}"
                                    #requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", 
                                                 # json={"chat_id": GURUH_ID, "text": tg_text})
                                    
                                    # Sessiyani qulflash
                                    st.session_state[key_name] = True
                                    st.balloons()
                                    st.success("Muvaffaqiyatli saqlandi!")
                                    st.rerun()
                        else:
                            st.error("Ismingizni yozing!")
            else:
                st.error(f"Hududda emassiz! Masofa: {round(masofa*1000)} m")
    else:
        st.error("⚠️ Davomat yopiq! (07:30-08:30 yoki 13:00-17:00 oraliqlari ochiq)")
    # --- ADMIN VA JADVALNI YUKLAB OLISH ---
    st.divider()
    if st.checkbox("Google Jadvalni ko'rish va Yuklab olish (Admin)"):
        if st.text_input("Admin kod:", type="password", key="adm_v") == MONITORING_KODI:
            conn = st.connection("gsheets", type=GSheetsConnection)
            df_gsheet = conn.read(ttl=0)
            st.dataframe(df_gsheet, use_container_width=True)
            
            # Excel formatiga o'tkazish
            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
                df_gsheet.to_excel(writer, index=False, sheet_name='Davomat')
            
            st.download_button(
                label="📥 Jadvalni Excel shaklida yuklab olish",
                data=buffer,
                file_name=f"davomat_{hozir.strftime('%d_%m_%Y')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )






