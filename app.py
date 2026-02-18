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

# --- 6. AI MULOQOT (QIDIRUV VA SUHBAT) ---
if menu == "🤖 AI Muloqot":
    st.title("🤖 Maktab AI yordamchisi")
    if "messages" not in st.session_state: st.session_state.messages = []
    
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]): st.markdown(msg["content"])

    # Unikal key: chat_input_box
    if savol := st.chat_input("Ism yozing (masalan: JALILOVA yoki Dilfuza)...", key="chat_input_box"):
        st.session_state.messages.append({"role": "user", "content": savol})
        with st.chat_message("user"): st.markdown(savol)
        
        with st.chat_message("assistant"):
            q_clean = savol.strip()
            topildi = False
            
            # 1. Ro'yxat yoki kimlar borligi so'ralsa
            if any(x in q_clean.lower() for x in ["ro'yxat", "kimlar bor", "hamma"]):
                if sheets_baza:
                    for key, df in sheets_baza.items():
                        st.write(f"📋 **{key}** bo'yicha ro'yxat:")
                        st.dataframe(df, use_container_width=True)
                    topildi = True
            
            # 2. Bazadan aniq qidiruv
            if not topildi and sheets_baza:
                for key, df in sheets_baza.items():
                    # Harflar registri va bo'shliqlarga qaramasdan qidirish
                    mask = df.apply(lambda row: row.astype(str).str.contains(q_clean, case=False, na=False).any(), axis=1)
                    res_df = df[mask]
                    if not res_df.empty:
                        st.success(f"🔍 Topildi:")
                        st.dataframe(res_df, use_container_width=True)
                        topildi = True
                        # To'xtatmaslik kerak, chunki ham o'qituvchi, ham o'quvchi chiqishi mumkin
            
            # 3. Agar bazada bo'lmasa yoki qo'shimcha savol bo'lsa Groq AI javob beradi
            if not topildi or len(savol.split()) > 3:
                try:
                    chat_completion = client.chat.completions.create(
                        messages=[{"role": "system", "content": f"Sen {MAKTAB_NOMI} yordamchisisan. O'qituvchilarga ochiq darslarda yordam berasan."},
                                 {"role": "user", "content": savol}],
                        model="llama-3.3-70b-versatile",
                    )
                    javob = chat_completion.choices[0].message.content
                    st.markdown(javob)
                    st.session_state.messages.append({"role": "assistant", "content": javob})
                except:
                    if not topildi: st.error("AI hozirda band, bazadan ham topilmadi.")

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
