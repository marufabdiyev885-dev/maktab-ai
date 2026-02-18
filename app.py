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
                    df.columns = [str(c).strip().lower() for c in df.columns]
                    all_sheets[f"{f} | {name}"] = df
        except: continue
    return all_sheets

sheets_baza = yuklash()

# --- 4. DIZAYN VA KIRISH ---
st.set_page_config(page_title=MAKTAB_NOMI, layout="wide")

if "authenticated" not in st.session_state:
    st.title(f"🏫 {MAKTAB_NOMI}")
    parol = st.text_input("Kirish paroli:", type="password", key="auth_pass_main")
    if st.button("Kirish", key="auth_btn_main"):
        if parol == TO_GRI_PAROL:
            st.session_state.authenticated = True
            st.rerun()
        else: st.error("Xato!")
    st.stop()

# --- 5. SIDEBAR (ASOSIY MENYU) ---
with st.sidebar:
    st.title(f"🏛 {MAKTAB_NOMI}")
    st.write(f"👤 **Direktor:** {DIREKTOR_FIO}")
    st.divider()
    # Key nomi unikal qilindi: sidebar_menu_selection
    menu = st.radio("Bo'limni tanlang:", ["🤖 AI Muloqot", "📊 Jurnal Monitoringi"], key="sidebar_menu_selection")
    st.divider()
    st.info(f"💡 {random.choice(HIKMATLAR)}")

# --- 6. AI MULOQOT ---
if menu == "🤖 AI Muloqot":
    st.title("🤖 Maktab AI yordamchisi")
    if "messages" not in st.session_state: st.session_state.messages = []
    
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]): st.markdown(msg["content"])

    if savol := st.chat_input("Ism yozing yoki savol bering...", key="ai_chat_input_unique"):
        st.session_state.messages.append({"role": "user", "content": savol})
        with st.chat_message("user"): st.markdown(savol)
        
        with st.chat_message("assistant"):
            q_upper = savol.upper().strip()
            topildi = False
            
            # Ro'yxat so'ralsa
            if any(x in q_upper for x in ["RO'YXAT", "KIMLAR BOR"]):
                if sheets_baza:
                    st.success("📋 Maktab bazasidagi pedagoglar:")
                    for key, df in sheets_baza.items():
                        col_name = next((c for c in df.columns if any(x in c for x in ["pedagog", "ismi", "f.i.sh"])), df.columns[0])
                        st.dataframe(df[[col_name]], use_container_width=True)
                    topildi = True
            
            # Bazadan qidiruv
            if not topildi and sheets_baza:
                for key, df in sheets_baza.items():
                    mask = df.apply(lambda row: row.astype(str).str.contains(savol, case=False, na=False).any(), axis=1)
                    res_df = df[mask]
                    if not res_df.empty:
                        st.success(f"🔍 Topildi:")
                        st.dataframe(res_df, use_container_width=True)
                        topildi = True; break
            
            # Groq AI suhbat
            if not topildi:
                try:
                    chat_completion = client.chat.completions.create(
                        messages=[{"role": "system", "content": f"Sen {MAKTAB_NOMI} yordamchisisan. O'zbek tilida javob ber."},
                                 {"role": "user", "content": savol}],
                        model="llama-3.3-70b-versatile",
                    )
                    javob = chat_completion.choices[0].message.content
                    st.markdown(javob)
                    st.session_state.messages.append({"role": "assistant", "content": javob})
                except: st.error("AI hozirda band.")

# --- 7. MONITORING (MUTLAQO O'ZGARISHSIZ) ---
elif menu == "📊 Jurnal Monitoringi":
    st.title("📊 Jurnal Monitoringi")
    if "m_auth" not in st.session_state: st.session_state.m_auth = False
    if not st.session_state.m_auth:
        m_in = st.text_input("Monitoring kodi:", type="password", key="monitoring_pass_key")
        if st.button("Kirish", key="monitoring_login_btn"):
            if m_in == MONITORING_KODI: st.session_state.m_auth = True; st.rerun()
            else: st.error("Kod xato!")
        st.stop()
    
    j_fayl = st.file_uploader("Excel yuklang", type=['xlsx', 'xls', 'html'], key="excel_uploader_key")
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
                
                if st.button("📢 Telegramga yuborish", key="telegram_send_unique"):
                    requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", 
                                 json={"chat_id": GURUH_ID, "text": f"📊 <b>Monitoring:</b>\n\n{xabar}", "parse_mode": "HTML"})
                    st.success("Yuborildi!")
        except Exception as e: st.error(f"Xato: {e}")
