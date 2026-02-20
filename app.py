# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
import os
import requests
import re
import io
from groq import Groq
from datetime import datetime
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
RUXSAT_ETILGAN_MASOFA = 0.2  # 200 metr radius

st.set_page_config(page_title=MAKTAB_NOMI, layout="wide", page_icon="🏫")

# --- SECRETS TEKSHIRUVI ---
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
    vaqt = datetime.now().strftime("%H:%M:%S")
    sana = datetime.now().strftime("%d.%m.%Y")
    yangi_malumot = pd.DataFrame([[sana, vaqt, ism, holat]], 
                                columns=["Sana", "Vaqt", "F.I.SH", "Holat"])
    
    if not os.path.isfile(DAVOMAT_FAYLI):
        yangi_malumot.to_csv(DAVOMAT_FAYLI, index=False, encoding='utf-8-sig')
    else:
        yangi_malumot.to_csv(DAVOMAT_FAYLI, mode='a', header=False, index=False, encoding='utf-8-sig')

# --- EXCEL YUKLASH FUNKSIYASI ---
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
        except Exception:
            continue
    return all_sheets

sheets_baza = yuklash()

# --- LOG-IN TIZIMI ---
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.title("🏫 " + MAKTAB_NOMI)
        st.subheader("Tizimga kirish")
        p_in = st.text_input("Kirish paroli:", type="password", key="main_auth_key")
        if st.button("Kirish", key="main_auth_btn", use_container_width=True):
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
    menu = st.radio("Bo'limni tanlang:", ["🤖 AI Muloqot", "📊 Jurnal Monitoringi", "📍 GPS Davomat"], key="nav_menu")
    st.divider()
    st.info("💡 Bilim - najotdir.")
    if st.button("🚪 Chiqish", use_container_width=True):
        for k in list(st.session_state.keys()):
            del st.session_state[k]
        st.rerun()

# =============================================
# AI MULOQOT
# =============================================
if menu == "🤖 AI Muloqot":
    st.title("🤖 Maktab AI Yordamchisi")

    if "messages" not in st.session_state:
        st.session_state.messages = []

    if st.session_state.messages:
        if st.button("Suhbatni tozalash", key="clear_chat"):
            st.session_state.messages = []
            st.rerun()

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    savol = st.chat_input("Savolingizni yozing...", key="chat_input_main")

    if savol:
        st.session_state.messages.append({"role": "user", "content": savol})
        with st.chat_message("user"):
            st.markdown(savol)

        with st.chat_message("assistant"):
            q_low = savol.lower().strip()
            topildi = False

            ijtimoiy_dict = {
                "rahmat": "Sizdan ham Alloh rozi bo'lsin! 😊",
                "salom": "Vaalaykum assalom! Xush kelibsiz. 🏛",
                "xayr": "Xayr, sog' bo'ling! 👋",
                "assalom": "Vaalaykum assalom! 😊",
            }

            for k, j in ijtimoiy_dict.items():
                if k in q_low:
                    st.markdown(j)
                    st.session_state.messages.append({"role": "assistant", "content": j})
                    topildi = True
                    break

            if not topildi:
                is_list_req = any(x in q_low for x in ["ro'yxat", "hamma", "barcha", "jadval"])
                is_teacher_req = any(x in q_low for x in ["o'qituvchi", "ustoz", "pedagog", "xodim"])
                search_word = q_low
                
                for sheet_key, df in sheets_baza.items():
                    if is_list_req and is_teacher_req:
                        if any(x in sheet_key.lower() for x in ["qituvchi", "xodim", "pedagog"]):
                            st.info("Xodimlar ro'yxati:")
                            st.dataframe(df, use_container_width=True)
                            topildi = True
                            break
                    elif len(search_word) >= 3:
                        mask = df.apply(lambda r: r.astype(str).str.contains(search_word, case=False, na=False).any(), axis=1)
                        res_df = df[mask]
                        if not res_df.empty:
                            st.success("Natijalar:")
                            st.dataframe(res_df, use_container_width=True)
                            topildi = True
                            break

            if not topildi:
                try:
                    system_prompt = f"Sen {MAKTAB_NOMI} AI yordamchisisan. O'zbek tilida qisqa javob ber."
                    res = client.chat.completions.create(
                        messages=[{"role": "system", "content": system_prompt}] + st.session_state.messages[-5:],
                        model="llama-3.3-70b-versatile",
                    )
                    ai_javob = res.choices[0].message.content
                    st.markdown(ai_javob)
                    st.session_state.messages.append({"role": "assistant", "content": ai_javob})
                except Exception as e:
                    st.error("AI band.")

# =============================================
# JURNAL MONITORINGI
# =============================================
elif menu == "📊 Jurnal Monitoringi":
    st.title("📊 Jurnal Monitoringi")

    if "m_auth" not in st.session_state:
        st.session_state.m_auth = False

    if not st.session_state.m_auth:
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            m_input = st.text_input("Monitoring kodi:", type="password", key="mon_input")
            if st.button("Kirish", key="mon_btn", use_container_width=True):
                if m_input == MONITORING_KODI:
                    st.session_state.m_auth = True
                    st.rerun()
                else:
                    st.error("Kod xato!")
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
            toliq_count = 0
            
            if len(df_j.columns) >= 6:
                for _, row in df_j.iterrows():
                    name = str(row.iloc[0]).strip()
                    val = str(row.iloc[5]).strip()
                    if "nan" in name.lower() or "jami" in name.lower(): continue
                    
                    nums = re.findall(r'\d+', val)
                    if len(nums) >= 2:
                        bor, jami = int(nums[0]), int(nums[1])
                        if jami > 0 and bor < jami:
                            kamchiliklar.append({"Xodim": name, "Bajarilgan": bor, "Jami": jami, "Foiz": f"{round(bor/jami*100)}%"})
                        elif jami > 0:
                            toliq_count += 1
                
                st.metric("To'liq bajarganlar", toliq_count)
                st.metric("Kamchiligi borlar", len(kamchiliklar))
                
                if kamchiliklar:
                    df_k = pd.DataFrame(kamchiliklar)
                    st.warning("Kamchiliklar ro'yxati:")
                    st.dataframe(df_k, use_container_width=True)
                    
                    if st.button("Telegramga yuborish"):
                        xabar = f"📊 *{MAKTAB_NOMI} Jurnal Monitoringi*\n\n"
                        for k in kamchiliklar:
                            xabar += f"❌ {k['Xodim']}: {k['Bajarilgan']}/{k['Jami']} ({k['Foiz']})\n"
                        requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", json={"chat_id": GURUH_ID, "text": xabar, "parse_mode": "Markdown"})
                        st.success("Yuborildi!")
        except Exception as e:
            st.error(f"Xato: {e}")

# =============================================
# GPS DAVOMAT (YANGI)
# =============================================
elif menu == "📍 GPS Davomat":
    st.title("📍 Maktab Hududida Davomat")
    
    hozir = datetime.now()
    hozirgi_vaqt = hozir.time()
    is_morning = (hozirgi_vaqt.hour < 8) or (hozirgi_vaqt.hour == 8 and hozirgi_vaqt.minute <= 30)
    is_afternoon = (hozirgi_vaqt.hour >= 13)

    if is_morning or is_afternoon:
        st.info(f"🕒 Hozirgi vaqt: {hozirgi_vaqt.strftime('%H:%M')}")
        loc = get_geolocation()

        if loc:
            user_pos = (loc['coords']['latitude'], loc['coords']['longitude'])
            masofa = geodesic(user_pos, MAKTAB_KOORDINATASI).km
            
            if masofa <= RUXSAT_ETILGAN_MASOFA:
                st.success(f"Siz maktab hududidasiz ✅ ({round(masofa*1000)} m)")
                ism_f = st.text_input("F.I.SH:")
                
                if st.button("🔴 TASDIQLASH", use_container_width=True):
                    if ism_f:
                        holat = "KELDI" if is_morning else "KETDI"
                        davomatni_saqlash(ism_f, holat)
                        
                        tg_txt = f"📍 #DAVOMAT\n👤 Xodim: {ism_f}\n📅 Sana: {hozir.strftime('%d.%m.%Y')}\n⏰ Vaqt: {hozir.strftime('%H:%M:%S')}\n🔄 Holat: {holat}"
                        requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", json={"chat_id": GURUH_ID, "text": tg_txt})
                        
                        st.balloons()
                        st.success("Muvaffaqiyatli qayd etildi!")
                    else:
                        st.error("Ismingizni kiriting!")
            else:
                st.error(f"Siz maktab hududida emassiz! ❌ ({round(masofa*1000)} m)")
        else:
            st.warning("GPS signali kutilmoqda... Brauzerda 'Allow' bosing.")
    else:
        st.error("⚠️ Davomat yopiq! (08:30 gacha yoki 13:00 dan keyin ochiladi)")

    # ADMIN UCHUN YUKLAB OLISH
    st.divider()
    with st.expander("📥 Davomat ro'yxatini yuklab olish (Admin)"):
        ad_p = st.text_input("Kod:", type="password")
        if ad_p == MONITORING_KODI:
            if os.path.exists(DAVOMAT_FAYLI):
                df_d = pd.read_csv(DAVOMAT_FAYLI)
                st.dataframe(df_d, use_container_width=True)
                
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    df_d.to_excel(writer, index=False)
                st.download_button("Excel yuklash", data=output.getvalue(), file_name="davomat.xlsx")
