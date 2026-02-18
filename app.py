import streamlit as st
import pandas as pd
import os
import requests
import re
import random
from groq import Groq

# --- 1. SOZLAMALAR ---
try:
    MAKTAB_NOMI = "1-sonli umumta'lim maktabi"
    DIREKTOR_FIO = "Mahmudov Matyoqub Narzulloyevich"
    TO_GRI_PAROL = "informatika2024"
    MONITORING_KODI = "admin777"
    
    BOT_TOKEN = st.secrets["TELEGRAM_BOT_TOKEN"]
    GURUH_ID = st.secrets["TELEGRAM_GURUH_ID"]
    GROQ_API_KEY = st.secrets["GROQ_API_KEY"]
    
    client = Groq(api_key=GROQ_API_KEY)
except Exception:
    st.error("⚠️ Secrets ma'lumotlarida xatolik bor!")
    st.stop()

# --- 2. BAZANI YUKLASH ---
@st.cache_data
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
        except: continue
    return all_sheets

sheets_baza = yuklash()

# --- 3. DIZAYN VA KIRISH ---
st.set_page_config(page_title=MAKTAB_NOMI, layout="wide")

if "authenticated" not in st.session_state:
    st.title(f"🏫 {MAKTAB_NOMI}")
    p_in = st.text_input("Kirish paroli:", type="password", key="main_auth_key")
    if st.button("Kirish", key="main_auth_btn"):
        if p_in == TO_GRI_PAROL:
            st.session_state.authenticated = True
            st.rerun()
        else: st.error("Xato!")
    st.stop()

# --- 4. SIDEBAR ---
with st.sidebar:
    st.title(f"🏛 {MAKTAB_NOMI}")
    st.write(f"👤 **Direktor:** {DIREKTOR_FIO}")
    menu = st.radio("Bo'limni tanlang:", ["🤖 AI Muloqot", "📊 Jurnal Monitoringi"], key="nav_menu")
    st.divider()
    st.info("💡 Bilim - najotdir.")

# --- 5. AI MULOQOT (MUKAMMAL VA FAROSATLI VARIANT) ---
if menu == "🤖 AI Muloqot":
    st.title("🤖 Maktab AI yordamchisi")
    
    # Xotira (Suhbat tarixini saqlash)
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    if savol := st.chat_input("Qanday yordam bera olaman?", key="chat_input_unique"):
        st.session_state.messages.append({"role": "user", "content": savol})
        with st.chat_message("user"):
            st.markdown(savol)
        
        with st.chat_message("assistant"):
            q_low = savol.lower().strip()
            
            # 1-QADAM: Odob-axloq va ijtimoiy so'zlarni filtrlash (Inson omili)
            ijtimoiy_sozlar = {
                "rahmat": ["Arzimaydi, doim xizmatingizdaman! 😊", "Sizdan ham Alloh rozi bo'lsin!", "Sizga yordam berishdan xursandman! ✨"],
                "salom": ["Assalomu alaykum! Maktabimizning aqlli tizimiga xush kelibsiz. Qanday yordam bera olaman? 🏛", "Vaalaykum assalom! Sog'-salomatmisiz?"],
                "xayr": ["Xayr, sog' bo'ling! Ishlaringizga rivoj tilayman. 👋", "Yaxshi boring, ertaga ko'rishguncha!"],
                "zo'r": ["Rahmat! Sizga manzur bo'lganidan xursandman. 🌟", "Sizning kayfiyatingiz - bizning yutug'imiz!"],
                "yaxshi": ["Shukur, yaxshi yuribman. Sizchi? Ishlaringiz joyidami? 😊"]
            }

            topildi = False
            for kalit, javoblar in ijtimoiy_sozlar.items():
                if kalit in q_low:
                    javob = random.choice(javoblar)
                    st.markdown(javob)
                    st.session_state.messages.append({"role": "assistant", "content": javob})
                    topildi = True
                    break

            # 2-QADAM: Agar ijtimoiy muloqot bo'lmasa, BAZADAN QIDIRISH
            if not topildi:
                # Gapdan qidiruv so'zini ajratib olish (Smart Search)
                ortiqcha_sozlar = ["top", "ber", "chiqar", "ro'yxati", "haqida", "izla", "ko'rsat", "o'qituvchilar", "muallim", "ustoz"]
                search_word = q_low
                for w in ortiqcha_sozlar:
                    search_word = search_word.replace(w, "").strip()

                if len(search_word) >= 3:
                    for key, df in sheets_baza.items():
                        mask = df.apply(lambda r: r.astype(str).str.contains(search_word, case=False, na=False).any(), axis=1)
                        res_df = df[mask]
                        if not res_df.empty:
                            msg = f"🔍 **{search_word.capitalize()}** bo'yicha ma'lumotlarni topdim:"
                            st.info(msg)
                            st.dataframe(res_df, use_container_width=True)
                            st.session_state.messages.append({"role": "assistant", "content": msg})
                            topildi = True
                            break

            # 3-QADAM: Agar bazada ham bo'lmasa, MUKAMMAL AI FIKRLASHI (Groq)
            if not topildi:
                try:
                    res = client.chat.completions.create(
                        messages=[
                            {"role": "system", "content": f"Sen {MAKTAB_NOMI}ning juda aqlli, madaniyatli va farosatli yordamchisisan. Foydalanuvchi bilan o'zbekona lutf, samimiyat va hurmat bilan gaplash. Agar u bazadan topilmagan ma'lumotni so'rasa, uzr so'rab, o'zing bilgan umumiy tavsiyalarni ber."},
                            {"role": "user", "content": savol}
                        ],
                        model="llama-3.3-70b-versatile"
                    )
                    ai_javob = res.choices[0].message.content
                    st.markdown(ai_javob)
                    st.session_state.messages.append({"role": "assistant", "content": ai_javob})
                except:
                    st.error("AI hozirda biroz band bo'lib qoldi. Birozdan so'ng urinib ko'ring.")
# --- 6. MONITORING (SENING MANTIQING) ---
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
                    name, val = str(row.iloc[0]), str(row.iloc[5])
                    if any(x in name.lower() for x in ["tuman", "muassasa", "f.i.sh"]): continue
                    nums = re.findall(r'(\d+)', val)
                    if len(nums) >= 2 and int(nums[0]) < int(nums[1]):
                        kamchiliklar.append(f"❌ **{name}**: {int(nums[1])-int(nums[0])} ta chala ({val})")
                
                st.dataframe(df_j, use_container_width=True)
                xabar_text = "✅ Hammasi to'liq!" if not kamchiliklar else "⚠️ **Kamchiliklar:**\n\n" + "\n".join(kamchiliklar)
                st.warning(xabar_text) if kamchiliklar else st.success(xabar_text)
                
                if st.button("📢 Telegramga yuborish", key="tg_btn"):
                    requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", 
                                 json={"chat_id": GURUH_ID, "text": f"📊 <b>Monitoring</b>\n\n{xabar_text}", "parse_mode": "HTML"})
                    st.success("✅ Telegramga yuborildi!")
        except Exception as e: st.error(f"Xato: {e}")

