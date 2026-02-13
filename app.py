import streamlit as st
import pandas as pd
import os
import requests
import re
import io
import docx

# --- 1. ASOSIY SOZLAMALAR ---
MAKTAB_NOMI = "1-sonli umumta'lim maktabi"
DIREKTOR_FIO = "Mahmudov Matyoqub Narzulloyevich"
GROQ_API_KEY = "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"
TO_GRI_PAROL = "informatika2024"

st.set_page_config(page_title=MAKTAB_NOMI, layout="wide")

# --- 2. RAHBARIYAT PANELI (SIDEBAR) ---
with st.sidebar:
    st.markdown(f"## 🏛 {MAKTAB_NOMI}")
    st.image("https://cdn-icons-png.flaticon.com/512/2859/2859706.png", width=80)
    st.divider()
    st.subheader("👨‍🏫 Rahbariyat")
    st.info(f"**Direktor:**\n\n{DIREKTOR_FIO}")
    st.divider()
    st.success("💡 **Action Metodist**\n\nDarsni shouga aylantiramiz!")

# --- 3. XAVFSIZLIK ---
if "authenticated" not in st.session_state:
    st.title(f"🏫 {MAKTAB_NOMI} | Tizim")
    parol = st.text_input("Parolni kiriting:", type="password")
    if st.button("Kirish"):
        if parol == TO_GRI_PAROL:
            st.session_state.authenticated = True
            st.rerun()
        else: st.error("❌ Parol xato!")
    st.stop()

# --- 4. BAZANI YUKLASH ---
@st.cache_data
def yuklash():
    files = [f for f in os.listdir('.') if f.lower().endswith(('.xlsx', '.csv', '.docx')) and 'app.py' not in f]
    all_data = []
    for f in files:
        try:
            if f.endswith('.docx'): continue
            df_s = pd.read_excel(f, dtype=str) if f.endswith('.xlsx') else pd.read_csv(f, dtype=str)
            df_s.columns = [str(c).strip().lower() for c in df_s.columns]
            all_data.append(df_s)
        except: continue
    return pd.concat(all_data, ignore_index=True) if all_data else None

df = yuklash()

# --- 5. CHAT INTERFEYSI (MANA SHU YERDA TO'XTASH LOGIKASI) ---
st.title(f"🤖 AI Konsultant & Metodist")

if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "Assalomu alaykum! Bugun darsni qanday 'Ekshn' ssenariy bilan boyitamiz?"}]

# Tarixni chiqarish
for m in st.session_state.messages:
    with st.chat_message(m["role"]): st.markdown(m["content"])

if savol := st.chat_input("Dars mavzusini yozing..."):
    st.session_state.messages.append({"role": "user", "content": savol})
    with st.chat_message("user"): st.markdown(savol)

    # 🛑 1-DARVOZA: TO'XTASH FILTRI (Agar rahmat/bo'ldi desa, kod shu yerda tugaydi)
    stop_sozlar = r"\b(rahmat|boldi|bo'ldi|tushundim|ok|yaxshi|tugadi|xayr)\b"
    if re.search(stop_sozlar, savol.lower()):
        xayr_text = "Sizga yordam berganimdan xursandman, ustoz! Keyingi darslarda omad! 😊"
        with st.chat_message("assistant"):
            st.success(xayr_text)
        st.session_state.messages.append({"role": "assistant", "content": xayr_text})
        st.stop() # <--- ENG MUHIMI! Pastdagi hech narsa ishlamaydi.

    # 🚀 2-DARVOZA: AGAR TO'XTAMASA, AI ISHLAYDI
    with st.chat_message("assistant"):
        found_data = ""
        # Baza qidiruvi
        if df is not None:
            keywords = [s.lower() for s in savol.split() if len(s) > 2]
            res = df[df.apply(lambda row: any(k in str(v).lower() for k in keywords for v in row), axis=1)]
            if not res.empty:
                st.markdown("### 📋 Baza ma'lumotlari:")
                st.dataframe(res, use_container_width=True)
                found_data = res.head(5).to_string()

        # Groq AI so'rovi
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
        
        system_talimoti = f"""
        Sen {MAKTAB_NOMI} maktabining 'Kreativ Rejissyorisan'.
        Vazifang: Faqat harakatli o'yinlar berish. 
        Taqiqlanadi: "Muhokama", "Fidoyi ustoz", "Sirli so'zlar".
        Format: 💥Nomi, 🎭Rollar, 📦Rekvizit, 🎬Action, 💻Namuna.
        """

        payload = {
            "model": "llama-3.3-70b-versatile",
            "messages": [
                {"role": "system", "content": system_talimoti},
                {"role": "user", "content": f"Baza: {found_data}. Savol: {savol}"}
            ],
            "temperature": 1.3,
            "presence_penalty": 1.5,
            "frequency_penalty": 1.0
        }

        try:
            r = requests.post(url, json=payload, headers=headers, timeout=15)
            ai_text = r.json()['choices'][0]['message']['content']
        except:
            ai_text = "Tizimda yuklama. Birozdan so'ng urinib ko'ring."

        st.info(ai_text)
        st.session_state.messages.append({"role": "assistant", "content": ai_text})
