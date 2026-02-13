import streamlit as st
import pandas as pd
import os
import requests
import re

# --- 1. ASOSIY SOZLAMALAR ---
MAKTAB_NOMI = "32-sonli umumta'lim maktabi"
DIREKTOR_FIO = "Eshmatov Toshmat"
GROQ_API_KEY = "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"
TO_GRI_PAROL = "informatika2024"

st.set_page_config(page_title=MAKTAB_NOMI, layout="wide")

# --- 2. XAVFSIZLIK ---
if "authenticated" not in st.session_state:
    st.title(f"🏫 {MAKTAB_NOMI} | Tizim")
    parol = st.text_input("Parolni kiriting:", type="password")
    if st.button("Kirish"):
        if parol == TO_GRI_PAROL:
            st.session_state.authenticated = True
            st.rerun()
        else: st.error("❌ Parol xato!")
    st.stop()

# --- 3. BAZANI YUKLASH ---
@st.cache_data
def yuklash():
    files = [f for f in os.listdir('.') if f.lower().endswith(('.xlsx', '.csv')) and 'app.py' not in f]
    all_data = []
    for f in files:
        try:
            df_s = pd.read_excel(f, dtype=str) if f.endswith('.xlsx') else pd.read_csv(f, dtype=str)
            df_s.columns = [str(c).strip().lower() for c in df_s.columns]
            for col in df_s.columns:
                df_s[col] = df_s[col].astype(str).str.strip()
            all_data.append(df_s)
        except: continue
    return pd.concat(all_data, ignore_index=True) if all_data else None

df = yuklash()

# --- 4. CHAT INTERFEYSI ---
st.title(f"🤖 {MAKTAB_NOMI} AI Yordamchisi")

if "messages" not in st.session_state:
    # Botning birinchi kutib olish so'zi (Ma'rufjon akaga xos)
    st.session_state.messages = [{"role": "assistant", "content": "Assalomu alaykum, Ma'rufjon aka! 32-maktabning raqamli yordamchisi xizmatingizga tayyor. Qanday ma'lumot kerak bo'lsa, bemalol so'rang, qo'limdan kelgancha yordam beraman!"}]

for m in st.session_state.messages:
    with st.chat_message(m["role"]): st.markdown(m["content"])

if savol := st.chat_input("Ma'rufjon aka, savolingizni yozing..."):
    st.session_state.messages.append({"role": "user", "content": savol})
    with st.chat_message("user"): st.markdown(savol)
    
    with st.chat_message("assistant"):
        found_data = "Hozircha bazadan ma'lumot topilmadi."
        
        if df is not None:
            # Aqlli qidiruv
            sinf_match = re.search(r'\d{1,2}-[a-z|A-Z]', savol)
            if sinf_match:
                kalit = sinf_match.group().lower()
                res = df[df.apply(lambda x: x.astype(str).str.lower().str.contains(kalit).any(), axis=1)]
            else:
                keywords = [s for s in savol.split() if len(s) > 2]
                res = df[df.apply(lambda x: any(k.lower() in str(v).lower() for k in keywords for v in x), axis=1)]
            
            if not res.empty:
                st.dataframe(res, use_container_width=True)
                found_data = res.head(15).to_string(index=False)

        # 🚀 BU YERDA BOTNING "TILINI" O'ZGARTIRAMIZ
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
        
        system_talimoti = f"""
        Sen {MAKTAB_NOMI} maktabining samimiy, zukko va xushmuomala xodimisiz. 
        Sening suhbatdoshing - Ma'rufjon aka. Unga doim hurmat bilan murojaat qil.
        
        Senga taqdim etilgan baza ma'lumotlari: {found_data}
        
        Vazifang:
        1. Ma'rufjon akaning savoliga bazadan kelib chiqib javob ber. 
        2. Agar ma'lumot topilgan bo'lsa, uni chiroyli, tushunarli tilda tushuntirib ber. 
        3. Agar ma'lumot topilmagan bo'lsa ham, quruq 'topilmadi' demasdan, vaziyatni yumshoq tilda tushuntir.
        4. O'zbek tilida, imlo xatolarisiz, xuddi jonli suhbatdagidek javob ber.
        """

        payload = {
            "model": "llama-3.3-70b-versatile",
            "messages": [
                {"role": "system", "content": system_talimoti},
                {"role": "user", "content": savol}
            ],
            "temperature": 0.8  # Bot "robot" bo'lib qolmasligi uchun
        }
        
        try:
            r = requests.post(url, json=payload, headers=headers, timeout=15)
            ai_text = r.json()['choices'][0]['message']['content']
        except:
            ai_text = "Ma'rufjon aka, ulanishda biroz texnik nosozlik bo'ldi, lekin ma'lumotlar jadvalda keltirilgan."

        st.markdown(ai_text)
        st.session_state.messages.append({"role": "assistant", "content": ai_text})
