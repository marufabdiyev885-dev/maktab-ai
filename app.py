import streamlit as st
import pandas as pd
import os
import requests
import re
import random
from groq import Groq
from datetime import datetime

# --- 1. ASOSIY SOZLAMALAR ---
MAKTAB_NOMI = "1-sonli umumta'lim maktabi"
DIREKTOR_FIO = "Mahmudov Matyoqub Narzulloyevich"
TO_GRI_PAROL = "informatika2024"
MONITORING_KODI = "admin777"
BOT_TOKEN = "8524007504:AAFiMXSbXhe2M-84WlNM16wNpzhNolfQIf8"
GURUH_ID = "-5045481739"

# API kalitni Streamlit Secrets'dan xavfsiz o'qiymiz
try:
    GROQ_API_KEY = st.secrets["GROQ_API_KEY"]
    client = Groq(api_key=GROQ_API_KEY)
except Exception:
    st.warning("⚠️ Diqqat: API kalit topilmadi. Streamlit Secrets bo'limiga kalitni qo'shing.")

HIKMATLAR_RO_YXATI = [
    "Ilm — saodat kalitidir.",
    "Hunari yo'q kishi — mevasi yo'q daraxt.",
    "Ilm izla, igna bilan quduq qazigandek bo'lsa ham.",
    "Bilim — tuganmas xazina.",
    "Odob — har bir kishining ziynatidir."
]

st.set_page_config(page_title=MAKTAB_NOMI, layout="wide")

@st.cache_data
def yuklash():
    files = [f for f in os.listdir('.') if f.lower().endswith(('.xlsx', '.xls', '.csv')) and 'app.py' not in f]
    all_sheets = {}
    for f in files:
        try:
            sheets = pd.read_excel(f, sheet_name=None, dtype=str)
            for name, df in sheets.items():
                if not df.empty:
                    df.columns = [str(c).strip().lower() for c in df.columns]
                    all_sheets[name] = df
        except:
            continue
    return all_sheets

sheets_baza = yuklash()

# --- SIDEBAR ---
with st.sidebar:
    st.title(f"🏛 {MAKTAB_NOMI}")
    st.write(f"👤 **Direktor:** \n{DIREKTOR_FIO}")
    st.divider()
    menu = st.radio("Bo'limni tanlang:", ["🤖 AI Muloqot", "📊 Jurnal Monitoringi"])
    st.divider()
    st.info(f"✨ **Kun hikmati:**\n*{random.choice(HIKMATLAR_RO_YXATI)}*")

# --- XAVFSIZLIK ---
if "authenticated" not in st.session_state:
    st.title(f"🏫 {MAKTAB_NOMI}")
    parol = st.text_input("Kirish paroli:", type="password")
    if st.button("Kirish"):
        if parol == TO_GRI_PAROL:
            st.session_state.authenticated = True
            st.rerun()
        else:
            st.error("Parol xato!")
    st.stop()

# --- 5. AI MULOQOT (Qidiruv tubdan yaxshilandi) ---
if menu == "🤖 AI Muloqot":
    st.title("🤖 Maktab AI yordamchisi")
    
    if "messages" not in st.session_state:
        st.session_state.messages = []

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if savol := st.chat_input("Xabaringizni yozing..."):
        st.session_state.messages.append({"role": "user", "content": savol})
        with st.chat_message("user"):
            st.markdown(savol)
        
        with st.chat_message("assistant"):
            q = savol.lower().strip()
            topildi = False
            
            # 1. Aniq sinf qidiruvi (9-a kabi)
            sinf_match = re.search(r'(\d{1,2})[- \s]?([a-zа-я])', q)
            if sinf_match:
                sinf_nomi = f"{sinf_match.group(1)}-{sinf_match.group(2)}"
                for name, df in sheets_baza.items():
                    mask = df.apply(lambda row: row.astype(str).str.contains(rf"\b{sinf_nomi}\b", case=False, regex=True).any(), axis=1)
                    res_df = df[mask]
                    if not res_df.empty:
                        msg = f"Mana, {sinf_nomi} sinf ma'lumotlari:"
                        st.success(msg)
                        st.dataframe(res_df, use_container_width=True)
                        st.session_state.messages.append({"role": "assistant", "content": msg})
                        topildi = True
                        break

            # 2. Umumiy bazadan qidirish (O'qituvchi yoki O'quvchi farqlanmaydi)
            if not topildi:
                for name, df in sheets_baza.items():
                    # Har bir qatordan foydalanuvchi yozgan so'zni qidiramiz
                    mask = df.apply(lambda row: row.astype(str).str.contains(q, case=False).any(), axis=1)
                    res_df = df[mask]
                    
                    if not res_df.empty:
                        if "лист2" in name.lower() or "pedagog" in " ".join(df.columns).lower():
                            msg = f"Pedagoglar bazasidan topildi:"
                        else:
                            msg = f"Ma'lumotlar bazasidan topildi ({name}):"
                        
                        st.success(msg)
                        st.dataframe(res_df, use_container_width=True)
                        st.session_state.messages.append({"role": "assistant", "content": msg})
                        topildi = True
                        break

            # 3. AI bilan bog'lanish
            if not topildi:
                try:
                    chat_completion = client.chat.completions.create(
                        messages=[
                            {"role": "system", "content": f"Sen {MAKTAB_NOMI} yordamchisisan. O'zbek tilida javob ber."},
                            {"role": "user", "content": savol}
                        ],
                        model="llama-3.3-70b-versatile",
                    )
                    javob = chat_completion.choices[0].message.content
                    st.markdown(javob)
                    st.session_state.messages.append({"role": "assistant", "content": javob})
                except Exception as e:
                    st.error(f"AI bilan bog'lanishda xatolik: {e}")

# --- 6. JURNAL MONITORINGI (O'ZGARMADI) ---
elif menu == "📊 Jurnal Monitoringi":
    st.title("📊 Jurnal Monitoringi")
    if "m_auth" not in st.session_state:
        st.session_state.m_auth = False
    if not st.session_state.m_auth:
        m_input = st.text_input("Monitoring kodi:", type="password")
        if st.button("Kirish"):
            if m_input == MONITORING_KODI:
                st.session_state.m_auth = True
                st.rerun()
            else:
                st.error("Kod xato!")
        st.stop()
    
    j_fayl = st.file_uploader("Excel yuklang", type=['xlsx', 'xls', 'html'])
    if j_fayl:
        try:
            try:
                df_j = pd.read_excel(j_fayl)
            except:
                j_fayl.seek(0)
                df_j = pd.read_html(j_fayl, header=0)[0]
            
            df_j.columns = [str(c).replace('\n', ' ').strip() for c in df_j.columns]
            st.dataframe(df_j)
            
            col_target, col_name = "Baholar qo'yilgan jurnallar soni", "O'qituvchi"
            kamchiliklar = []
            if col_target in df_j.columns:
                for _, row in df_j.iterrows():
                    nums = re.findall(r'(\d+)', str(row[col_target]))
                    if len(nums) >= 2 and int(nums[0]) < int(nums[1]):
                        kamchiliklar.append(f"❌ {row[col_name]}: {int(nums[1]) - int(nums[0])} ta jurnal chala")
            
            xabar_tahlili = "✅ Barcha jurnallar baholangan!" if not kamchiliklar else "⚠️ **Kamchiliklar:**\n" + "\n".join(kamchiliklar)
            st.info(xabar_tahlili)
            
            if st.button("📢 Telegramga yuborish"):
                requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", 
                             json={"chat_id": GURUH_ID, "text": f"<b>📊 Monitoring</b>\n\n{xabar_tahlili}", "parse_mode": "HTML"})
                st.success("✅ Yuborildi!")
        except Exception as e:
            st.error(f"Xato: {e}")
