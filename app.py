import streamlit as st
import pandas as pd
import os
import requests
import re
import io
import docx
import random # Tasodifiylik qo'shish uchun

# --- 1. ASOSIY SOZLAMALAR ---
MAKTAB_NOMI = "1-sonli umumta'lim maktabi"
DIREKTOR_FIO = "Mahmudov Matyoqub Narzulloyevich"
GROQ_API_KEY = "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"
TO_GRI_PAROL = "informatika2024"

st.set_page_config(page_title=MAKTAB_NOMI, layout="wide")

# --- 2. RAHBARIYAT VA SIDEBAR ---
with st.sidebar:
    st.markdown(f"## 🏛 {MAKTAB_NOMI}")
    st.image("https://cdn-icons-png.flaticon.com/512/2859/2859706.png", width=80)
    st.divider()
    st.success("💡 **Kreativ Produser**\n\nBu bot darsingizni zerikarli ma'ruzadan 'Ekshn' filmga aylantiradi!")

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
            if f.endswith('.docx'): continue # Matnli qidiruvni soddalashtirdik
            df_s = pd.read_excel(f, dtype=str) if f.endswith('.xlsx') else pd.read_csv(f, dtype=str)
            df_s.columns = [str(c).strip().lower() for c in df_s.columns]
            all_data.append(df_s)
        except: continue
    return pd.concat(all_data, ignore_index=True) if all_data else None

df = yuklash()

# --- 5. CHAT INTERFEYSI ---
st.title(f"🤖 Action-Dars Metodisti")

if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "Salom! Bugun darsda qanday 'to'polon' (shov-shuv) ko'taramiz?"}]

for m in st.session_state.messages:
    with st.chat_message(m["role"]): st.markdown(m["content"])

if savol := st.chat_input("Mavzuni yozing (masalan: Algoritm)..."):
    st.session_state.messages.append({"role": "user", "content": savol})
    with st.chat_message("user"): st.markdown(savol)
    
    # 🛑 FILTR: Rahmat desa javobni to'xtatish
    if any(word in savol.lower() for word in ["rahmat", "bo'ldi", "tushundim", "ok"]):
        with st.chat_message("assistant"): st.info("Sizga yordam berganimdan xursandman!")
        st.stop()

    with st.chat_message("assistant"):
        found_data = ""
        if df is not None:
            keywords = [s.lower() for s in savol.split() if len(s) > 2]
            res = df[df.apply(lambda row: any(k in str(v).lower() for k in keywords for v in row), axis=1)]
            if not res.empty:
                found_data = res.head(5).to_string()

        # 🚀 AI KONSULTANT (TEMIR INTIZOM BILAN)
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
        
        # Tasodifiy uslub tanlash (AIni har xil javob berishga majburlash)
        uslublar = ["Kvest (Ayg'oqchilik)", "Auktsion (Savdo)", "Mina maydoni (Xavf)", "Hakerlar jangi", "Detektiv qidiruv"]
        tanlangan_uslub = random.choice(uslublar)

        system_talimoti = f"""
        Sen {MAKTAB_NOMI} maktabining 'Kreativ Rejissyorisan'. 
        VAZIFANG: Faqat va faqat JONLI HARAKATga asoslangan ssenariy berish. 

        ❌ QAT'IYAN TAQIQLANGAN: "Muhokama", "Tushuntirish", "Varaqqa yozish", "Sirli so'zlar" (bu o'yin eskirgan).
        ✅ BUGUNGI MAJBURIY USLUB: {tanlangan_uslub}.

        Javobni juda qisqa, 'shov-shuvli' va 'Action' elementlari bilan yoz:
        💥 **Ssenariy nomi**
        🎭 **O'quvchilar roli** (Masalan: Agentlar, Mijozlar, Robotlar)
        🎬 **DAQIQA BAYAN REJA:** (10-daqiqa: kutilmagan voqea bo'ladi...)
        💻 **KEYS:** (Mavzuga bog'liq texnik harakat)
        """

        payload = {
            "model": "llama-3.3-70b-versatile",
            "messages": [
                {"role": "system", "content": system_talimoti},
                {"role": "user", "content": f"Baza: {found_data}. Savol: {savol}"}
            ],
            "temperature": 1.4, # Maksimal darajada tasodifiy g'oyalar
            "presence_penalty": 1.5, # Oldin aytgan gapini aytishni taqiqlash
            "frequency_penalty": 1.5
        }
        
        try:
            r = requests.post(url, json=payload, headers=headers, timeout=15)
            ai_text = r.json()['choices'][0]['message']['content']
        except:
            ai_text = "Tizim biroz o'ylab qoldi, qaytadan yozing."

        st.info(ai_text)
        st.session_state.messages.append({"role": "assistant", "content": ai_text})
