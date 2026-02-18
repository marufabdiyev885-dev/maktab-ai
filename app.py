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
    st.error("⚠️ Secrets bo'limida ma'molik bor!")
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

# --- 4. KIRISH ---
st.set_page_config(page_title=MAKTAB_NOMI, layout="wide")

if "authenticated" not in st.session_state:
    st.title(f"🏫 {MAKTAB_NOMI}")
    p_input = st.text_input("Kirish paroli:", type="password", key="main_pass")
    if st.button("Kirish", key="main_btn"):
        if p_input == TO_GRI_PAROL:
            st.session_state.authenticated = True
            st.rerun()
        else: st.error("Xato!")
    st.stop()

# --- 5. SIDEBAR ---
with st.sidebar:
    st.title(f"🏛 {MAKTAB_NOMI}")
    st.write(f"👤 **Direktor:** {DIREKTOR_FIO}")
    menu = st.radio("Bo'lim:", ["🤖 AI Muloqot", "📊 Jurnal Monitoringi"], key="menu_radio")
    st.info(f"💡 {random.choice(HIKMATLAR)}")

# --- 6. AI MULOQOT ---
if menu == "🤖 AI Muloqot":
    st.title("🤖 Maktab AI yordamchisi")
    if "messages" not in st.session_state: st.session_state.messages = []
    
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]): st.markdown(msg["content"])

    if savol := st.chat_input("Ism yozing...", key="ai_input"):
        st.session_state.messages.append({"role": "user", "content": savol})
        with st.chat_message("user"): st.markdown(savol)
        
        with st.chat_message("assistant"):
            q_low = savol.lower().strip()
            topildi = False
            
            # Bazadan qidirish (Faqat ism yozilsa)
            if len(q_low) >= 3 and not any(x in q_low for x in ["salom", "qalay", "yaxshi"]):
                target = sheets_baza
                if "o'qituvchi" in q_low:
                    target = {k:v for k,v in sheets_baza.items() if "o'qituvchi" in k.lower()}
                    q_low = q_low.replace("o'qituvchi", "").strip()
                
                for key, df in target.items():
                    mask = df.apply(lambda r: r.astype(str).str.contains(q_low, case=False).any(), axis=1)
                    if not df[mask].empty:
                        st.dataframe(df[mask], use_container_width=True)
                        topildi = True
            
            if not topildi:
                res = client.chat.completions.create(
                    messages=[{"role":"system","content":"Sen maktab yordamchisisan."},{"role":"user","content":savol}],
                    model="llama-3.3-70b-versatile"
                )
                st.markdown(res.choices[0].message.content)

# --- 7. MONITORING (Sizning kodingiz tuzatildi) ---
elif menu == "📊 Jurnal Monitoringi":
    st.title("📊 Jurnal Monitoringi")
    if "m_auth" not in st.session_state: st.session_state.m_auth = False
    
    if not st.session_state.m_auth:
        m_in = st.text_input("Kod:", type="password", key="m_pass")
        if st.button("Kirish", key="m_btn"):
            if m_in == MONITORING_KODI: st.session_state.m_auth = True; st.rerun()
            else: st.error("Xato!")
        st.stop()
    
    j_fayl = st.file_uploader("Excel yuklang", type=['xlsx', 'xls', 'html'], key="m_file")
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
                
                st.dataframe(df_j, use_container_width=True)
                xabar = "✅ To'liq!" if not kamchiliklar else "⚠️ **Kamchiliklar:**\n\n" + "\n".join(kamchiliklar)
                
                # SIZNING MANTIQINGIZ
                st.warning(xabar) if kamchiliklar else st.success(xabar)
                
                if st.button("📢 Telegram", key="tg_btn"):
                    requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", 
                                 json={"chat_id": GURUH_ID, "text": f"📊 Monitoring:\n{xabar}"})
                    st.success("Yuborildi!")
        except Exception as e: st.error(f"Xato: {e}")
