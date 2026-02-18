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
    st.error("⚠️ Secrets bo'limida ma'lumotlar xato!")
    st.stop()

# --- 2. HIKMATLAR ---
HIKMATLAR = ["Ilm - najotdir.", "Ustoz - otangdek ulug'.", "Kitob - bilim manbai."]

# --- 3. BAZANI YUKLASH ---
@st.cache_data
def yuklash():
    files = [f for f in os.listdir('.') if f.lower().endswith(('.xlsx', '.xls'))]
    all_sheets = {}
    for f in files:
        try:
            sheets = pd.read_excel(f, sheet_name=None, dtype=str)
            for name, df in sheets.items():
                if not df.empty:
                    # Ustun nomlarini qidiruvga qulay qilish
                    df.columns = [str(c).strip().lower() for c in df.columns]
                    all_sheets[f"{f} | {name}"] = df
        except: continue
    return all_sheets

sheets_baza = yuklash()

# --- 4. KIRISH TIZIMI ---
st.set_page_config(page_title=MAKTAB_NOMI, layout="wide")

if "authenticated" not in st.session_state:
    st.title(f"🏫 {MAKTAB_NOMI}")
    p_input = st.text_input("Kirish paroli:", type="password", key="login_pass_field")
    if st.button("Kirish", key="login_submit_btn"):
        if p_input == TO_GRI_PAROL:
            st.session_state.authenticated = True
            st.rerun()
        else: st.error("Xato!")
    st.stop()

# --- 5. SIDEBAR (MENYU) ---
with st.sidebar:
    st.title(f"🏛 {MAKTAB_NOMI}")
    st.write(f"👤 **Direktor:** {DIREKTOR_FIO}")
    st.divider()
    # Unikal key: main_nav_radio
    menu = st.radio("Bo'limni tanlang:", ["🤖 AI Muloqot", "📊 Jurnal Monitoringi"], key="main_nav_radio")
    st.divider()
    st.info(f"💡 {random.choice(HIKMATLAR)}")
# --- 6. AI MULOQOT (TARTIBLI QIDIRUV) ---
if menu == "🤖 AI Muloqot":
    st.title("🤖 Maktab AI yordamchisi")
    if "messages" not in st.session_state: st.session_state.messages = []
    
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]): st.markdown(msg["content"])

    if savol := st.chat_input("Ism yozing yoki savol bering...", key="ai_chat_final_fix"):
        st.session_state.messages.append({"role": "user", "content": savol})
        with st.chat_message("user"): st.markdown(savol)
        
        with st.chat_message("assistant"):
            q_lower = savol.lower().strip()
            
            # Oddiy suhbat so'zlarini bazadan qidirmaslik uchun filtr
            suhbat_sozlari = ["salom", "yaxshi", "rahmat", "ahvoling", "qalay", "nima gap", "ok", "ha", "yo'q"]
            
            topildi = False
            
            # Agar bu shunchaki suhbat bo'lsa, to'g'ridan-to'g'ri AI javob bersin
            if q_lower in suhbat_sozlari or len(q_lower) < 3:
                pass # Bu qismda bazadan qidirmaydi, pastdagi Groq AI ishlaydi
            else:
                # Bazadan qidirish (Faqat mazmunli so'z bo'lsa)
                if sheets_baza:
                    for key, df in sheets_baza.items():
                        mask = df.apply(lambda row: row.astype(str).str.contains(savol, case=False, na=False).any(), axis=1)
                        res_df = df[mask]
                        if not res_df.empty:
                            st.success(f"🔍 '{savol}' bo'yicha bazadan topildi:")
                            st.dataframe(res_df, use_container_width=True)
                            topildi = True
            
            # Agar bazadan qidirish shart bo'lmasa yoki topilmasa - Groq AI suhbatlashadi
            if not topildi:
                try:
                    chat_completion = client.chat.completions.create(
                        messages=[{"role": "system", "content": f"Sen {MAKTAB_NOMI} AI yordamchisisan. Samimiy suhbatlash. Agar ism so'rashsa, bazada yo'qligini ayt."},
                                 {"role": "user", "content": savol}],
                        model="llama-3.3-70b-versatile",
                    )
                    javob = chat_completion.choices[0].message.content
                    st.markdown(javob)
                    st.session_state.messages.append({"role": "assistant", "content": javob})
                except:
                    st.error("AI hozir ulanishda qiynalyapti.")
# --- 7. MONITORING (MUTLAQO TEGILMADI) ---
elif menu == "📊 Jurnal Monitoringi":
    st.title("📊 Jurnal Monitoringi")
    if "m_auth" not in st.session_state: st.session_state.m_auth = False
    if not st.session_state.m_auth:
        m_in = st.text_input("Monitoring kodi:", type="password", key="mon_pass_field")
        if st.button("Kirish", key="mon_login_btn"):
            if m_in == MONITORING_KODI: st.session_state.m_auth = True; st.rerun()
            else: st.error("Kod xato!")
        st.stop()
    
    j_fayl = st.file_uploader("Excel yuklang", type=['xlsx', 'xls', 'html'], key="mon_file_up")
    if j_fayl:
        try:
            try: df_j = pd.read_excel(j_fayl)
            except: 
                j_fayl.seek(0)
                df_j = pd.read_html(j_fayl, header=0)[0]
            
            df_j.columns = [str(c).replace('\n', ' ').strip() for c in df_j.columns]
            kamchiliklar = []
            if len(df_j.columns) >= 6:
                for _, row in df_j.iterrows():
                    name, val = str(row.iloc[0]), str(row.iloc[5])
                    if any(x in name.lower() for x in ["tuman", "muassasa", "o'qituvchi"]): continue
                    nums = re.findall(r'(\d+)', val)
                    if len(nums) >= 2:
                        if int(nums[0]) < int(nums[1]):
                            kamchiliklar.append(f"❌ **{name}**: {int(nums[1])-int(nums[0])} ta chala ({val})")
                
                st.subheader("📋 Natija:")
                st.dataframe(df_j, use_container_width=True)
                xabar = "✅ Hammasi to'liq!" if not kamchiliklar else "⚠️ **Kamchiliklar:**\n\n" + "\n".join(kamchiliklar)
                st.warning(xabar) if kamchiliklar else st.success(xabar)
                
                if st.button("📢 Telegramga yuborish", key="mon_tg_send"):
                    requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", 
                                 json={"chat_id": GURUH_ID, "text": f"📊 <b>Monitoring:</b>\n\n{xabar}", "parse_mode": "HTML"})
                    st.success("Yuborildi!")
        except Exception as e: st.error(f"Xato: {e}")


