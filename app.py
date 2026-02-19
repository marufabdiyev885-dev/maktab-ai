# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
import os
import requests
import re
import io
from groq import Groq

MAKTAB_NOMI = "1-sonli umumta'lim maktabi"
DIREKTOR_FIO = "Mahmudov Matyoqub Narzulloyevich"
ASOSIY_PAROL = "informatika2024"
MONITORING_KODI = "admin777"

st.set_page_config(page_title=MAKTAB_NOMI, layout="wide", page_icon="🏫")

try:
    BOT_TOKEN = st.secrets["TELEGRAM_BOT_TOKEN"]
    GURUH_ID = st.secrets["TELEGRAM_GURUH_ID"]
    GROQ_API_KEY = st.secrets["GROQ_API_KEY"]
    client = Groq(api_key=GROQ_API_KEY)
except Exception as e:
    st.error("Secrets xatolik: " + str(e))
    st.stop()

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

with st.sidebar:
    st.title("🏛 " + MAKTAB_NOMI)
    st.write("👤 **Direktor:** " + DIREKTOR_FIO)
    st.divider()
    menu = st.radio("Bolimni tanlang:", ["🤖 AI Muloqot", "📊 Jurnal Monitoringi"], key="nav_menu")
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
                "rahmat": "Sizdan ham Alloh rozi bolsin! 😊",
                "salom": "Vaalaykum assalom! Xush kelibsiz. 🏛",
                "xayr": "Xayr, sog boling! 👋",
                "assalom": "Vaalaykum assalom! 😊",
            }

            for k, j in ijtimoiy_dict.items():
                if k in q_low:
                    st.markdown(j)
                    st.session_state.messages.append({"role": "assistant", "content": j})
                    topildi = True
                    break

            if not topildi:
                is_list_req = any(x in q_low for x in ["royxat", "hamma", "barcha", "jadval"])
                is_teacher_req = any(x in q_low for x in ["qituvchi", "ustoz", "pedagog", "xodim"])

                stop_list = ["top", "ber", "chiqar", "haqida", "izla", "qayerda", "kim"]
                search_word = q_low
                for w in stop_list:
                    search_word = search_word.replace(w, "").strip()

                for sheet_key, df in sheets_baza.items():
                    if is_list_req and is_teacher_req:
                        if any(x in sheet_key.lower() for x in ["qituvchi", "xodim", "pedagog"]):
                            st.info("Xodimlar royxati:")
                            st.dataframe(df, use_container_width=True)
                            javob = "Royxat korsatildi."
                            st.session_state.messages.append({"role": "assistant", "content": javob})
                            topildi = True
                            break
                    elif len(search_word) >= 3:
                        try:
                            mask = df.apply(
                                lambda r: r.astype(str).str.contains(search_word, case=False, na=False).any(),
                                axis=1
                            )
                            res_df = df[mask]
                            if not res_df.empty:
                                st.success("Natijalar:")
                                st.dataframe(res_df, use_container_width=True)
                                javob = str(len(res_df)) + " ta natija topildi."
                                st.session_state.messages.append({"role": "assistant", "content": javob})
                                topildi = True
                                break
                        except Exception:
                            continue

            if not topildi:
                try:
                    system_prompt = "Sen " + MAKTAB_NOMI + "ning AI yordamchisisang. Uzbek tilida qisqa javob ber."
                    tarix = st.session_state.messages[-10:]
                    with st.spinner("AI javob tayyorlamoqda..."):
                        res = client.chat.completions.create(
                            messages=[{"role": "system", "content": system_prompt}] + tarix,
                            model="llama-3.3-70b-versatile",
                            max_tokens=1024,
                            temperature=0.7,
                        )
                    ai_javob = res.choices[0].message.content
                    st.markdown(ai_javob)
                    st.session_state.messages.append({"role": "assistant", "content": ai_javob})
                except Exception as e:
                    xato = "AI band. Xato: " + str(e)
                    st.error(xato)
                    st.session_state.messages.append({"role": "assistant", "content": xato})

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

    j_fayl = st.file_uploader("Excel faylni yuklang", type=['xlsx', 'xls'], key="uploader")

    if j_fayl:
        df_j = None
        fayl_nomi = j_fayl.name.lower()
        fayl_bytes = j_fayl.read()

        # Avval HTML formatini tekshirish (eMaktab xls lari aslida HTML)
        if fayl_bytes[:200].strip().lower().startswith(b'<'):
            try:
                dfs = pd.read_html(io.BytesIO(fayl_bytes), header=0)
                if dfs:
                    df_j = dfs[0]
                    st.info("Fayl HTML formatida o'qildi.")
                else:
                    st.error("HTML jadval topilmadi.")
                    st.stop()
            except Exception as e:
                st.error("HTML o'qishda xato: " + str(e))
                st.stop()

        elif fayl_nomi.endswith('.xlsx'):
            try:
                df_j = pd.read_excel(io.BytesIO(fayl_bytes), engine='openpyxl')
            except Exception as e:
                st.error("xlsx o'qishda xato: " + str(e))
                st.stop()

        elif fayl_nomi.endswith('.xls'):
            try:
                df_j = pd.read_excel(io.BytesIO(fayl_bytes), engine='xlrd')
            except Exception as e:
                st.error("xls o'qishda xato: " + str(e))
                st.stop()

        if df_j is None:
            st.error("Faylni o'qib bo'lmadi.")
            st.stop()

        df_j.columns = [str(c).replace('\n', ' ').strip() for c in df_j.columns]

        st.subheader("Yuklangan jadval:")
        st.dataframe(df_j, use_container_width=True)
        st.divider()

        kamchiliklar = []
        toliq_list = []
        skip_words = ["tuman", "muassasa", "qituvchi", "f.i.sh", "jami"]

        if len(df_j.columns) >= 6:
            for _, row in df_j.iterrows():
                name = str(row.iloc[0]).strip()
                val = str(row.iloc[5]).strip()

                if not name or name.lower() == "nan":
                    continue
                if any(x in name.lower() for x in skip_words):
                    continue

                nums = re.findall(r'\d+', val)
                if len(nums) >= 2:
                    baho_bor = int(nums[0])
                    jami = int(nums[1])
                    if jami == 0:
                        continue
                    if baho_bor < jami:
                        farq = jami - baho_bor
                        foiz = round(baho_bor / jami * 100)
                        kamchiliklar.append({
                            "Xodim": name,
                            "Bajarilgan": baho_bor,
                            "Jami": jami,
                            "Farq": farq,
                            "Foiz": str(foiz) + "%"
                        })
                    else:
                        toliq_list.append(name)

            c1, c2 = st.columns(2)
            with c1:
                st.metric("Toliq bajarilgan", len(toliq_list))
            with c2:
                st.metric("Kamchilik bor", len(kamchiliklar))

            st.subheader("Monitoring Natijasi:")

            if not kamchiliklar:
                st.success("Barcha jurnallar toliq!")
                xabar_text = MAKTAB_NOMI + "\n\nBarcha jurnallar toliq! 🎉"
            else:
                df_kam = pd.DataFrame(kamchiliklar)
                st.warning(str(len(kamchiliklar)) + " ta xodimda kamchilik:")
                st.dataframe(df_kam, use_container_width=True)

                lines = ["Maktab: " + MAKTAB_NOMI, ""]
                lines.append("Toliq: " + str(len(toliq_list)) + " ta")
                lines.append("Kamchilik: " + str(len(kamchiliklar)) + " ta")
                lines.append("")
                for k in kamchiliklar:
                    lines.append("- " + k["Xodim"] + ": " + str(k["Bajarilgan"]) + "/" + str(k["Jami"]) + " (" + k["Foiz"] + ")")
                xabar_text = "\n".join(lines)

            st.divider()
            if st.button("Telegramga yuborish", key="tg_btn"):
                with st.spinner("Yuborilmoqda..."):
                    resp = requests.post(
                        "https://api.telegram.org/bot" + BOT_TOKEN + "/sendMessage",
                        json={"chat_id": GURUH_ID, "text": xabar_text},
                        timeout=10
                    )
                if resp.status_code == 200:
                    st.success("Telegramga yuborildi!")
                else:
                    st.error("Telegram xatosi: " + resp.text)
        else:
            st.error("Faylda ustunlar yetarli emas: " + str(len(df_j.columns)) + " ta topildi.")

