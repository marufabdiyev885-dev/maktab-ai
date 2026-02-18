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

# --- 5. AI MULOQOT (TOZALANGAN VARIANT) ---
if menu == "🤖 AI Muloqot":
    st.title("🤖 Maktab AI yordamchisi")
    if "messages" not in st.session_state: st.session_state.messages = []
    
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]): st.markdown(msg["content"])

    if savol := st.chat_input("Ism yozing...", key="chat_input_unique"):
        st.session_state.messages.append({"role": "user", "content": savol})
        with st.chat_message("user"): st.markdown(savol)
        
        with st.chat_message("assistant"):
            q_low = savol.lower().strip()
            topildi = False
            
            # Faqat ism qidirilganda bazadan izlaydi
            if len(q_low) >= 3 and not any(x in q_low for x in ["salom", "qalay", "yaxshi", "rahmat"]):
                for key, df in sheets_baza.items():
                    mask = df.apply(lambda r: r.astype(str).str.contains(savol, case=False).any(), axis=1)
                    if not df[mask].empty:
                        st.success(f"🔍 Bazadan topildi:")
                        st.dataframe(df[mask], use_container_width=True)
                        topildi = True
                        break
            
            if not topildi:
                res = client.chat.completions.create(
                    messages=[{"role":"system","content":"Sen maktab yordamchisisan."},{"role":"user","content":savol}],
                    model="llama-3.3-70b-versatile"
                )
                msg_text = res.choices[0].message.content
                st.markdown(msg_text)
                st.session_state.messages.append({"role": "assistant", "content": msg_text})

# --- 6. MONITORING (SENING MANTIQING - XATOSIZ) ---
elif menu == "📊 Jurnal Monitoringi":
    st.title("📊 Jurnal Monitoringi")
    if "m_auth" not in st.session_state: st.session_state.m_auth = False
    
    if not st.session_state.m_auth:
        m_pass = st.text_input("Monitoring kodi:", type="password", key="mon_login_key")
        if st.button("Kirish", key="mon_login_btn"):
            if m_pass == MONITORING_KODI: 
                st.session_state.m_auth = True
                st.rerun()
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
                
                # MONITORING NATIJASI FAQAT SHU YERDA CHIQADI
                st.warning(xabar) if kamchiliklar else st.success(xabar)
                
                if st.button("📢 Telegramga yuborish", key="mon_tg_btn"):
                    requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", 
                                 json={"chat_id": GURUH_ID, "text": f"📊 <b>Monitoring:</b>\n\n{xabar}", "parse_mode": "HTML"})
                    st.success("Yuborildi!")
        except Exception as e: st.error(f"Xato: {e}")
