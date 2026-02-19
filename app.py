import streamlit as st
import pandas as pd
import os
import requests
import re
from groq import Groq

# --- 1. SOZLAMALAR ---
MAKTAB_NOMI = "1-sonli umumta'lim maktabi"
DIREKTOR_FIO = "Mahmudov Matyoqub Narzulloyevich"
TO_GRI_PAROL = "informatika2024"
MONITORING_KODI = "admin777"

st.set_page_config(page_title=MAKTAB_NOMI, layout="wide", page_icon="🏫")

try:
    BOT_TOKEN = st.secrets["TELEGRAM_BOT_TOKEN"]
    GURUH_ID = st.secrets["TELEGRAM_GURUH_ID"]
    GROQ_API_KEY = st.secrets["GROQ_API_KEY"]
    client = Groq(api_key=GROQ_API_KEY)
except Exception as e:
    st.error(f"⚠️ Secrets ma'lumotlarida xatolik: {e}")
    st.stop()

# --- 2. BAZANI YUKLASH ---
@st.cache_data(ttl=300)  # Har 5 daqiqada yangilanadi
def yuklash():
    files = [f for f in os.listdir('.') if f.lower().endswith(('.xlsx', '.xls'))]
    all_sheets = {}
    for f in files:
        try:
            sheets = pd.read_excel(f, sheet_name=None, dtype=str)
            for name, df in sheets.items():
                if not df.empty:
                    df.columns = [str(c).strip().lower() for c in df.columns]
                    all_sheets[f"{f} | {name}"] = df
        except Exception as e:
            st.warning(f"'{f}' faylini o'qib bo'lmadi: {e}")
    return all_sheets

sheets_baza = yuklash()

# --- 3. ASOSIY PAROL BILAN KIRISH ---
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.title(f"🏫 {MAKTAB_NOMI}")
        st.subheader("Tizimga kirish")
        p_in = st.text_input("Kirish paroli:", type="password", key="main_auth_key")
        if st.button("Kirish", key="main_auth_btn", use_container_width=True):
            if p_in == TO_GRI_PAROL:
                st.session_state.authenticated = True
                st.rerun()
            else:
                st.error("❌ Parol xato! Qayta urinib ko'ring.")
    st.stop()

# --- 4. SIDEBAR ---
with st.sidebar:
    st.title(f"🏛 {MAKTAB_NOMI}")
    st.write(f"👤 **Direktor:** {DIREKTOR_FIO}")
    st.divider()
    menu = st.radio("Bo'limni tanlang:", ["🤖 AI Muloqot", "📊 Jurnal Monitoringi"], key="nav_menu")
    st.divider()
    st.info("💡 Bilim - najotdir.")
    
    # Chiqish tugmasi
    if st.button("🚪 Chiqish", use_container_width=True):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()

# =============================================
# --- 5. AI MULOQOT ---
# =============================================
if menu == "🤖 AI Muloqot":
    st.title("🤖 Maktab AI Yordamchisi")
    st.caption("Maktab ma'lumotlari yoki umumiy savollar bo'yicha yordam beraman.")

    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Suhbatni tozalash tugmasi
    if st.session_state.messages:
        if st.button("🗑️ Suhbatni tozalash", key="clear_chat"):
            st.session_state.messages = []
            st.rerun()

    # Eski xabarlarni ko'rsatish
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    if savol := st.chat_input("Savolingizni yozing...", key="chat_input_v3"):
        st.session_state.messages.append({"role": "user", "content": savol})
        with st.chat_message("user"):
            st.markdown(savol)

        with st.chat_message("assistant"):
            q_low = savol.lower().strip()
            topildi = False

            # 1. IJTIMOIY MULOQOT
            ijtimoiy = {
                "rahmat": "Sizdan ham Alloh rozi bo'lsin! Doim xizmatingizdaman. 😊",
                "salom": "Vaalaykum assalom! Maktabimiz tizimiga xush kelibsiz. Qanday yordam kerak? 🏛",
                "xayr": "Xayr, sog' bo'ling! Ishlaringizda rivoj tilayman. 👋",
                "zo'r": "Katta rahmat! Sizga manzur bo'lganidan juda xursandman. 🌟",
                "assalomu alaykum": "Vaalaykum assalom! Xush kelibsiz. 😊",
            }

            for k, j in ijtimoiy.items():
                if k in q_low:
                    st.markdown(j)
                    st.session_state.messages.append({"role": "assistant", "content": j})
                    topildi = True
                    break

            # 2. BAZADAN QIDIRUV
            if not topildi:
                is_list_req = any(x in q_low for x in ["ro'yxat", "hamma", "barcha", "jadval", "ko'rsat"])
                is_teacher_req = any(x in q_low for x in ["o'qituvchi", "ustoz", "pedagog", "xodim"])

                # Qidiruv so'zini tozalash
                stop_words = ["top", "ber", "chiqar", "ro'yxati", "haqida", "izla", "ko'rsat", "qayerda", "kim"]
                search_word = q_low
                for w in stop_words:
                    search_word = search_word.replace(w, "").strip()

                for key, df in sheets_baza.items():
                    # Butun ro'yxat so'ralsa
                    if is_list_req and is_teacher_req:
                        if any(x in key.lower() for x in ["o'qituvchi", "xodim", "pedagog"]):
                            st.info("📋 Maktabimiz o'qituvchilari ro'yxati:")
                            st.dataframe(df, use_container_width=True)
                            javob = "📋 O'qituvchilar ro'yxati yuqorida ko'rsatildi."
                            st.session_state.messages.append({"role": "assistant", "content": javob})
                            topildi = True
                            break

                    # Aniq qidiruv
                    elif len(search_word) >= 3:
                        try:
                            mask = df.apply(
                                lambda r: r.astype(str).str.contains(search_word, case=False, na=False).any(),
                                axis=1
                            )
                            res_df = df[mask]
                            if not res_df.empty:
                                st.success(f"🔍 **'{search_word.capitalize()}'** bo'yicha natijalar:")
                                st.dataframe(res_df, use_container_width=True)
                                javob = f"🔍 '{search_word}' bo'yicha {len(res_df)} ta natija topildi."
                                st.session_state.messages.append({"role": "assistant", "content": javob})
                                topildi = True
                                break
                        except Exception:
                            continue

            # 3. GROQ AI — tarix bilan
            if not topildi:
                try:
                    system_prompt = (
                        f"Sen '{MAKTAB_NOMI}'ning aqlli AI yordamchisisang. "
                        "O'zbek tilida samimiy, qisqa va aniq javob ber. "
                        "Bazada topilmagan ma'lumotlar haqida so'ralsa, muloyimlik bilan tushuntir."
                    )
                    
                    # Oxirgi 10 xabarni yuborish (kontekst uchun)
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
                    xato = f"⚠️ AI hozirda band. Xato: {e}"
                    st.error(xato)
                    st.session_state.messages.append({"role": "assistant", "content": xato})

# =============================================
# --- 6. JURNAL MONITORINGI ---
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
                    st.error("❌ Kod xato!")
        st.stop()

    j_fayl = st.file_uploader(
        "📁 Excel faylni yuklang", 
        type=['xlsx', 'xls', 'html'], 
        key="uploader",
        help="Jurnal monitoring jadvalini xlsx yoki xls formatda yuklang"
    )

    if j_fayl:
        df_j = None
        try:
            for engine, reader in [
                ("openpyxl", lambda: pd.read_excel(j_fayl, engine='openpyxl')),
                ("xlrd",     lambda: (j_fayl.seek(0), pd.read_excel(j_fayl, engine='xlrd'))[1]),
                ("html",     lambda: (j_fayl.seek(0), pd.read_html(j_fayl, header=0)[0])[1]),
                ("auto",     lambda: (j_fayl.seek(0), pd.read_excel(j_fayl))[1]),
            ]:
                try:
                    df_j = reader()
                    break
                except Exception:
                    continue

            if df_j is None:
                st.error("❌ Faylni o'qib bo'lmadi. Iltimos, boshqa format sinab ko'ring.")
                st.stop()

            # Ustunlarni tozalash
            df_j.columns = [str(c).replace('\n', ' ').strip() for c in df_j.columns]

            st.subheader("📋 Yuklangan jadval:")
            st.dataframe(df_j, use_container_width=True)
            st.divider()

            kamchiliklar = []
            to_liq = []

            if len(df_j.columns) >= 6:
                o'tkazib_yuborish = ["tuman", "muassasa", "o`qituvchi", "f.i.sh", "no", "jami"]
                
                for _, row in df_j.iterrows():
                    name = str(row.iloc[0]).strip()
                    val = str(row.iloc[5]).strip()

                    if not name or name.lower() == "nan":
                        continue
                    if any(x in name.lower() for x in o'tkazib_yuborish):
                        continue

                    nums = re.findall(r'\d+', val)
                    if len(nums) >= 2:
                        baho_bor, jami = int(nums[0]), int(nums[1])
                        if jami == 0:
                            continue
                        if baho_bor < jami:
                            farq = jami - baho_bor
                            foiz = round(baho_bor / jami * 100)
                            kamchiliklar.append({
                                "O'qituvchi": name,
                                "Bajarilgan": baho_bor,
                                "Jami": jami,
                                "Farq": farq,
                                "Foiz": f"{foiz}%"
                            })
                        else:
                            to_liq.append(name)

                col1, col2 = st.columns(2)
                with col1:
                    st.metric("✅ To'liq bajarilgan", len(to_liq))
                with col2:
                    st.metric("⚠️ Kamchilik bor", len(kamchiliklar))

                st.subheader("📊 Monitoring Natijasi:")

                if not kamchiliklar:
                    st.success("✅ Barcha jurnallar to'liq to'ldirilgan!")
                    xabar_text = f"✅ {MAKTAB_NOMI}\n\nBarcha jurnallar to'liq to'ldirilgan! 🎉"
                else:
                    df_kam = pd.DataFrame(kamchiliklar)
                    st.warning(f"⚠️ {len(kamchiliklar)} ta o'qituvchida kamchilik aniqlandi:")
                    st.dataframe(
                        df_kam.style.applymap(lambda v: "background-color: #ffe0e0" if isinstance(v, int) and v > 0 else "", subset=["Farq"]),
                        use_container_width=True
                    )
                    
                    # Telegram uchun matn
                    lines = [f"📊 <b>{MAKTAB_NOMI} — Jurnal Monitoringi</b>\n"]
                    lines.append(f"✅ To'liq: {len(to_liq)} ta\n⚠️ Kamchilik: {len(kamchiliklar)} ta\n")
                    lines.append("<b>Kamchiliklar:</b>")
                    for k in kamchiliklar:
                        lines.append(f"❌ {k[\"O'qituvchi\"]}: {k['Bajarilgan']}/{k['Jami']} ({k['Foiz']})")
                    xabar_text = "\n".join(lines)

                st.divider()
                if st.button("📢 Telegramga yuborish", key="tg_btn", use_container_width=False):
                    with st.spinner("Yuborilmoqda..."):
                        resp = requests.post(
                            f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
                            json={"chat_id": GURUH_ID, "text": xabar_text, "parse_mode": "HTML"},
                            timeout=10
                        )
                    if resp.status_code == 200:
                        st.success("✅ Telegramga muvaffaqiyatli yuborildi!")
                    else:
                        st.error(f"❌ Telegram xatosi: {resp.text}")
            else:
                st.error(f"❌ Faylda ustunlar yetarli emas. Topildi: {len(df_j.columns)} ta (kamida 6 ta kerak).")
                st.info("Fayl strukturasini tekshiring: birinchi ustun — o'qituvchi ismi, oltinchi ustun — baholash holati bo'lishi kerak.")

        except Exception as e:
            st.error(f"❌ Kutilmagan xato: {e}")


