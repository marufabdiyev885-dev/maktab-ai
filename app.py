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
from bs4 import BeautifulSoup

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
    st.error(f"Secrets sozlamalarida xatolik: {e}")
    st.stop()

# --- EMAKTAB HISOBOT FUNKSIYASI ---
def kundalik_hisobot_ol(login, parol, school_id, yil):
    session = requests.Session()
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'uz,en;q=0.9',
    }
    try:
        # 1. Login sahifasini ochish — cookie olish
        session.get("https://login.emaktab.uz", headers=headers)

        # 2. Login POST
        res_login = session.post(
            "https://login.emaktab.uz",
            data={"login": login, "password": parol},
            headers=headers,
            allow_redirects=True
        )

        if "logout" not in res_login.text.lower() and "chiqish" not in res_login.text.lower():
            return None, "🔒 Login yoki parol xato!", None

        # 3. Cookie larni .emaktab.uz domeniga o'rnatish
        for cookie in session.cookies:
            session.cookies.set(cookie.name, cookie.value, domain='.emaktab.uz')
            session.cookies.set(cookie.name, cookie.value, domain='schools.emaktab.uz')

        # 4. Schools asosiy sahifasiga kirish
        schools_headers = {
            **headers,
            'Referer': 'https://login.emaktab.uz/',
        }
        session.get("https://schools.emaktab.uz", headers=schools_headers)

        # 5. Hisobot sahifasini ochish
        url = f"https://schools.emaktab.uz/v2/reports/default?school={school_id}&report=paid-access-school&year={yil}"
        response = session.get(url, headers=schools_headers)

        if response.status_code != 200:
            return None, f"🌐 Sahifa ochilmadi (Status: {response.status_code})", None

        soup = BeautifulSoup(response.content, 'html.parser')
        title = soup.title.string if soup.title else ""

        if "login" in title.lower() or "kirish" in title.lower():
            return None, "⚠️ Session o'tmadi, qayta urinib ko'ring!", title

        # 6. Jadval ma'lumotini o'qish
        rows_data = []
        for table in soup.find_all('table'):
            for tr in table.find_all('tr'):
                tds = tr.find_all(['td', 'th'])
                if len(tds) >= 4:
                    c1 = tds[0].get_text(strip=True)
                    c2 = tds[1].get_text(strip=True)
                    c3 = tds[2].get_text(strip=True)
                    c4 = tds[3].get_text(strip=True)
                    if re.search(r'\d+-[A-ZА-Яa-zа-я]', c1):
                        rows_data.append([c1, c2, c3, c4])

        if rows_data:
            df = pd.DataFrame(rows_data, columns=['Sinf', "O'quvchi soni", 'Kelmagan', 'Foiz (%)'])
            return df, "OK", None

        return None, "Jadval topilmadi", f"Title: {title} | Tables: {len(soup.find_all('table'))}"

    except Exception as e:
        return None, f"Xatolik: {str(e)}", None


# --- GOOGLE SHEETSGA SAQLASH FUNKSIYASI ---
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
            else:
                st.error("Parol xato!")
    st.stop()

# --- SIDEBAR ---
with st.sidebar:
    st.title("🏛 " + MAKTAB_NOMI)
    st.write(f"👤 **Direktor:** {DIREKTOR_FIO}")
    st.divider()
    menu = st.radio("Bo'limni tanlang:", [
        "🤖 AI Muloqot",
        "📊 Jurnal Monitoringi",
        "📍 GPS Davomat",
        "📥 eMaktab Hisobot"
    ])
    st.divider()
    if st.button("🚪 Chiqish", use_container_width=True):
        st.session_state.clear()
        st.rerun()


# --- AI MULOQOT ---
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
            try:
                res = client.chat.completions.create(
                    messages=[{"role": "system", "content": "Sen maktab yordamchisisan."}] + st.session_state.messages[-5:],
                    model="llama-3.3-70b-versatile",
                )
                ans = res.choices[0].message.content
                st.markdown(ans)
                st.session_state.messages.append({"role": "assistant", "content": ans})
            except:
                st.error("AI band.")


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
            try:
                df_j = pd.read_excel(j_fayl, engine='openpyxl')
            except Exception:
                try:
                    j_fayl.seek(0)
                    df_j = pd.read_excel(j_fayl, engine='xlrd')
                except Exception:
                    try:
                        j_fayl.seek(0)
                        df_j = pd.read_html(j_fayl, header=0)[0]
                    except Exception:
                        j_fayl.seek(0)
                        df_j = pd.read_excel(j_fayl)

            df_j.columns = [str(c).replace('\n', ' ').strip() for c in df_j.columns]
            kamchiliklar = []
            if len(df_j.columns) >= 6:
                for _, row in df_j.iterrows():
                    name = str(row.iloc[0])
                    val = str(row.iloc[5])
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
                xabar_text = "✅ Barcha jurnallar baholandi!" if not kamchiliklar else "⚠️ **Kamchiliklar:**\n\n" + "\n".join(kamchiliklar)
                if not kamchiliklar:
                    st.success(xabar_text)
                else:
                    st.warning(xabar_text)

                st.divider()
                if st.button("📢 Telegramga yuborish", key="tg_btn"):
                    requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
                                  json={"chat_id": GURUH_ID, "text": f"<b>📊 Monitoring</b>\n\n{xabar_text}", "parse_mode": "HTML"})
                    st.success("✅ Telegramga yuborildi!")
            else:
                st.error(f"Faylda ustunlar yetarli emas. Topildi: {len(df_j.columns)} ta.")
        except Exception as e:
            st.error(f"Faylni o'qishda kutilmagan xato: {e}")


# --- GPS DAVOMAT ---
elif menu == "📍 GPS Davomat":
    st.title("📍 GPS Davomat (Google Sheets)")

    ertalab_bosh = dt.time(7, 30)
    ertalab_tugash = dt.time(8, 30)
    kechki_bosh = dt.time(13, 0)
    kechki_tugash = dt.time(21, 0)

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
                if key_name not in st.session_state:
                    st.session_state[key_name] = False

                if st.session_state[key_name]:
                    status_text = "Siz davomatdan o'tdingiz" if is_ertalab else "Siz maktabdan chiqdingiz"
                    st.info(f"✅ **{status_text}**")
                else:
                    ism = st.text_input("F.I.SH (Ism-familiyangiz):").strip()
                    if st.button(f"🔴 {ish_holati}NI TASDIQLASH", use_container_width=True):
                        if ism:
                            takroriy = df_check[(df_check['F.I.SH'] == ism) &
                                                (df_check['Sana'] == bugun_sana) &
                                                (df_check['Holat'] == ish_holati)]
                            if not takroriy.empty:
                                st.warning(f"⚠️ {ism}, siz allaqachon qayd etilgansiz!")
                                st.session_state[key_name] = True
                                st.rerun()
                            else:
                                if davomatni_gsheetsga_yoz(ism, ish_holati):
                                    st.session_state[key_name] = True
                                    st.balloons()
                                    st.success("Muvaffaqiyatli saqlandi!")
                                    st.rerun()
                        else:
                            st.error("Ismingizni yozing!")
            else:
                st.error(f"Hududda emassiz! Masofa: {round(masofa*1000)} m")
    else:
        st.error("⚠️ Davomat yopiq! (07:30-08:30 yoki 13:00-21:00 oraliqlari ochiq)")

    st.divider()
    if st.checkbox("Google Jadvalni ko'rish va Yuklab olish (Admin)"):
        if st.text_input("Admin kod:", type="password", key="adm_v") == MONITORING_KODI:
            conn = st.connection("gsheets", type=GSheetsConnection)
            df_gsheet = conn.read(ttl=0)
            st.dataframe(df_gsheet, use_container_width=True)

            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
                df_gsheet.to_excel(writer, index=False, sheet_name='Davomat')

            st.download_button(
                label="📥 Jadvalni Excel shaklida yuklab olish",
                data=buffer,
                file_name=f"davomat_{hozir.strftime('%d_%m_%Y')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )


# --- EMAKTAB HISOBOT ---
elif menu == "📥 eMaktab Hisobot":
    st.title("📥 Kundalikga Kirish — Maktab Hisoboti")

    if "em_auth" not in st.session_state:
        st.session_state.em_auth = False

    if not st.session_state.em_auth:
        em_kod = st.text_input("Monitoring kodi:", type="password", key="em_kod")
        if st.button("Kirish", key="em_kirish"):
            if em_kod == MONITORING_KODI:
                st.session_state.em_auth = True
                st.rerun()
            else:
                st.error("Kod xato!")
        st.stop()

    col1, col2, col3 = st.columns(3)
    with col1:
        e_login = st.text_input("eMaktab login:", value="marufabdiyev")
        e_parol = st.text_input("eMaktab parol:", type="password")
    with col2:
        e_id = st.text_input("Maktab ID:", value="1000001352999")
        e_yil = st.selectbox("O'quv yili:", [2025, 2026], index=0)
    with col3:
        st.info(f"📅 Bugun: {hozir.strftime('%d.%m.%Y')}\n\n⏰ Vaqt: {hozir.strftime('%H:%M')}")

    if st.button("🔍 Hisobotni olish", use_container_width=True):
        if e_parol:
            with st.spinner("⏳ eMaktab tizimiga kirilmoqda..."):
                df, msg, debug = kundalik_hisobot_ol(e_login, e_parol, e_id, e_yil)
                if df is not None:
                    st.session_state.em_df = df
                    st.success(f"✅ {len(df)} ta sinf ma'lumoti yuklandi!")
                else:
                    st.error(f"❌ {msg}")
                    if debug:
                        st.warning(f"Debug: {debug}")
        else:
            st.error("Parolni kiriting!")

    if "em_df" in st.session_state and st.session_state.em_df is not None:
        df_show = st.session_state.em_df

        # Statistika
        st.divider()
        col1, col2, col3 = st.columns(3)
        with col1:
            jami = df_show["O'quvchi soni"].astype(str).str.extract(r'(\d+)')[0].astype(float).sum()
            st.metric("👥 Jami o'quvchi", int(jami))
        with col2:
            kelmagan = df_show['Kelmagan'].astype(str).str.extract(r'(\d+)')[0].astype(float).sum()
            st.metric("❌ Kelmagan", int(kelmagan))
        with col3:
            foiz = df_show['Foiz (%)'].astype(str).str.extract(r'([\d.]+)')[0].astype(float).mean()
            st.metric("📊 O'rtacha foiz", f"{foiz:.2f}%")

        st.divider()
        st.dataframe(df_show, use_container_width=True)

        col1, col2 = st.columns(2)
        with col1:
            if st.button("📢 Telegramga yuborish", use_container_width=True):
                txt = f"<b>📊 Kundalikga kirish hisoboti</b>\n"
                txt += f"📅 {hozir.strftime('%d.%m.%Y')} | ⏰ {hozir.strftime('%H:%M')}\n\n"
                txt += f"<pre>{df_show.to_string(index=False)}</pre>"
                res = requests.post(
                    f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
                    json={"chat_id": GURUH_ID, "text": txt, "parse_mode": "HTML"}
                )
                if res.status_code == 200:
                    st.success("✅ Telegramga yuborildi!")
                else:
                    st.error("Telegram xatolik!")

        with col2:
            if st.button("🤖 AI Tahlil", use_container_width=True):
                with st.spinner("AI tahlil qilmoqda..."):
                    data_str = df_show.to_string(index=False)
                    res = client.chat.completions.create(
                        messages=[{
                            "role": "user",
                            "content": f"Quyidagi maktab davomati ma'lumotlarini o'zbek tilida tahlil qil va muammoli sinflarni ajratib ko'rsat:\n{data_str}"
                        }],
                        model="llama-3.3-70b-versatile"
                    )
                    st.info(res.choices[0].message.content)
