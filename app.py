import streamlit as st
import pandas as pd
import os
import requests
import re
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
    st.error("⚠️ Secrets bo'limida ma'lumotlar xato yoki yetishmayapti!")
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
                    key = f"{f.lower()} | {name.lower()}"
                    all_sheets[key] = df
        except:
            continue
    return all_sheets

sheets_baza = yuklash()

# --- 3. DIZAYN ---
st.set_page_config(page_title=MAKTAB_NOMI, layout="wide")

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

# --- 4. SIDEBAR ---
with st.sidebar:
    st.title(f"🏛 {MAKTAB_NOMI}")
    menu = st.radio("Bo'limni tanlang:", ["🤖 AI Muloqot", "📊 Jurnal Monitoringi"])

# --- 5. AI MULOQOT ---
if menu == "🤖 AI Muloqot":
    st.title("🤖 Maktab AI yordamchisi")
    if "messages" not in st.session_state: st.session_state.messages = []
    for message in st.session_state.messages:
        with st.chat_message(message["role"]): st.markdown(message["content"])

    if savol := st.chat_input("Xabaringizni yozing..."):
        st.session_state.messages.append({"role": "user", "content": savol})
        with st.chat_message("user"): st.markdown(savol)
        
        with st.chat_message("assistant"):
            q = savol.lower().strip()
            topildi = False
            for key, df in sheets_baza.items():
                mask = df.apply(lambda row: row.astype(str).str.contains(q, case=False).any(), axis=1)
                res_df = df[mask]
                if not res_df.empty:
                    st.success(f"🔍 Topildi:")
                    st.dataframe(res_df, use_container_width=True)
                    topildi = True; break
            if not topildi:
                chat_completion = client.chat.completions.create(
                    messages=[{"role": "system", "content": f"Sen {MAKTAB_NOMI} AI yordamchisisan."},
                             {"role": "user", "content": savol}],
                    model="llama-3.3-70b-versatile",
                )
                javob = chat_completion.choices[0].message.content
                st.markdown(javob)
                st.session_state.messages.append({"role": "assistant", "content": javob})

# --- 6. JURNAL MONITORINGI (SIZNING JADVALINGIZGA MOSLANDI) ---
elif menu == "📊 Jurnal Monitoringi":
    st.title("📊 Jurnal Monitoringi")
    
    if "m_auth" not in st.session_state: st.session_state.m_auth = False
    if not st.session_state.m_auth:
        m_input = st.text_input("Monitoring kodi:", type="password")
        if st.button("Kirish"):
            if m_input == MONITORING_KODI:
                st.session_state.m_auth = True; st.rerun()
            else: st.error("Kod xato!")
        st.stop()
    
    j_fayl = st.file_uploader("Monitoring Excel faylini yuklang", type=['xlsx', 'xls', 'html'])
    
    if j_fayl:
        try:
            try:
                df_j = pd.read_excel(j_fayl)
            except:
                j_fayl.seek(0)
                df_j = pd.read_html(j_fayl, header=0)[0]
            
            df_j.columns = [str(c).replace('\n', ' ').strip() for c in df_j.columns]
            
            # Ustunlarni aniqlash
            col_target = next((c for c in df_j.columns if "baholar qo'yilgan jurnallar" in c.lower()), None)
            col_name = next((c for c in df_j.columns if any(x in c.lower() for x in ["o'qituvchi", "f.i.sh"])), None)
            
            if col_target and col_name:
                kamchiliklar = []
                for _, row in df_j.iterrows():
                    val = str(row[col_target])
                    # "6 Undan 6" formatidan sonlarni ajratish
                    nums = re.findall(r'(\d+)', val)
                    if len(nums) >= 2:
                        baho_bor = int(nums[0])
                        jami = int(nums[1])
                        if baho_bor < jami:
                            farq = jami - baho_bor
                            kamchiliklar.append(f"❌ **{row[col_name]}**: {farq} ta jurnalda baho qo'yilmagan (Holat: {val})")
                
                # NATIJANI KO'RSATISH
                st.subheader("📋 Tekshiruv Natijasi:")
                st.dataframe(df_j, use_container_width=True)
                
                if not kamchiliklar:
                    xabar_text = "✅ Barcha jurnallar to'liq yozilgan!"
                    st.success(xabar_text)
                else:
                    xabar_text = "⚠️ **Quyidagi o'qituvchilarda kamchilik aniqlandi:**\n\n" + "\n".join(kamchiliklar)
                    st.warning(xabar_text)
                
                st.divider()
                if st.button("📢 Natijalarni Telegramga yuborish"):
                    requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", 
                                 json={"chat_id": GURUH_ID, "text": f"<b>📊 Monitoring</b>\n\n{xabar_text}", "parse_mode": "HTML"})
                    st.success("✅ Telegramga yuborildi!")
            else:
                st.error("❌ Kerakli ustunlar topilmadi. Ustun nomlarini tekshiring.")
        except Exception as e:
            st.error(f"Xato: {e}")
