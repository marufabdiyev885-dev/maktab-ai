import streamlit as st
import pandas as pd
import os
import requests
import re

# --- 1. ASOSIY SOZLAMALAR ---
MAKTAB_NOMI = "1-sonli umumta'lim maktabi"
DIREKTOR_FIO = "Mahmudov Matyoqub "
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
    st.session_state.messages = [{"role": "assistant", "content": "Assalomu alaykum, Ma'rufjon aka! Xizmatingizga tayyorman. Qanday ma'lumot kerak bo'lsa, bemalol so'rang!"}]

for m in st.session_state.messages:
    with st.chat_message(m["role"]): st.markdown(m["content"])

if savol := st.chat_input("Ma'rufjon aka, savolingizni yozing..."):
    st.session_state.messages.append({"role": "user", "content": savol})
    with st.chat_message("user"): st.markdown(savol)
    
    with st.chat_message("assistant"):
        found_data = ""
        soni = 0
        
        if df is not None:
            # 🔍 QIDIRUVNI TUZATILGAN QISMI
            sinf_match = re.search(r'\b\d{1,2}-[a-z|A-Z]\b', savol) # RegEx chegarasi qo'shildi
            
            if sinf_match:
                kalit = sinf_match.group().lower()
                # 🎯 ANIQ MOSLIK (1-A so'ralsa, faqat 1-A chiqadi, 11-A emas)
                if 'sinfi' in df.columns:
                    res = df[df['sinfi'].str.lower() == kalit]
                else:
                    res = df[df.apply(lambda row: row.astype(str).str.lower().eq(kalit).any(), axis=1)]
            else:
                keywords = [s.lower() for s in savol.split() if len(s) > 2]
                res = df[df.apply(lambda row: any(k in str(v).lower() for k in keywords for v in row), axis=1)]
            
            if not res.empty:
                st.dataframe(res, use_container_width=True)
                soni = len(res)  # 🎯 JAMI SONINI HISOBLASH
                found_data = res.head(40).to_string(index=False)

        # 🚀 AI JAVOBINI SOZLASH
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
        
        system_talimoti = f"""
        Sen {MAKTAB_NOMI} maktabining samimiy xodimisiz. Suhbatdoshing - Ma'rufjon aka. 
        
        Vazifang:
        1. Agar ma'lumot topilsa, jadvalda jami {soni} ta ma'lumot borligini Ma'rufjon akaga samimiy aytsang kifoya.
        2. Ro'yxatni jadval ostidan qaytadan tagma-tag yozib chiqma (Taqiqlanadi).
        3. Doim Ma'rufjon aka deb hurmat bilan murojaat qil.
        4. Javobing qisqa va mazmunli bo'lsin.
        """

        payload = {
            "model": "llama-3.3-70b-versatile",
            "messages": [
                {"role": "system", "content": system_talimoti},
                {"role": "user", "content": f"Baza ma'lumoti: {found_data}. Savol: {savol}"}
            ],
            "temperature": 0.4 # AI o'zidan ro'yxat to'qimasligi uchun
        }
        
        try:
            r = requests.post(url, json=payload, headers=headers, timeout=15)
            ai_text = r.json()['choices'][0]['message']['content']
        except:
            ai_text = f"Ma'rufjon aka, jami {soni} ta ma'lumot topildi. Marhamat, jadvaldan ko'rishingiz mumkin."

        st.markdown(ai_text)
        st.session_state.messages.append({"role": "assistant", "content": ai_text})
