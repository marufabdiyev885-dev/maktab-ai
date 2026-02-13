import streamlit as st
import pandas as pd
import os
import requests
import re

# 1. MAKTAB MA'LUMOTLARI
MAKTAB_NOMI = "32-sonli umumta'lim maktabi"
DIREKTOR_FIO = "Eshmatov Toshmat" 
GROQ_API_KEY = "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"
TO_GRI_PAROL = "informatika2024"

st.set_page_config(page_title=MAKTAB_NOMI, layout="wide")

# 2. XAVFSIZLIK (PAROL)
if "authenticated" not in st.session_state:
    st.title(f"🔐 {MAKTAB_NOMI} | Tizim")
    parol = st.text_input("Kirish paroli:", type="password")
    if st.button("Kirish"):
        if parol == TO_GRI_PAROL:
            st.session_state.authenticated = True
            st.rerun()
        else: st.error("❌ Parol noto'g'ri!")
    st.stop()

# 3. BAZANI YUKLASH
@st.cache_data
def yuklash():
    files = [f for f in os.listdir('.') if f.lower().endswith(('.xlsx', '.csv')) and 'app.py' not in f]
    if not files: return None
    all_dfs = []
    for f in files:
        try:
            temp_df = pd.read_excel(f, dtype=str) if f.endswith('.xlsx') else pd.read_csv(f, dtype=str)
            # Ustun nomlarini va ma'lumotlarni tozalash
            temp_df.columns = [str(c).strip().lower() for c in temp_df.columns]
            for col in temp_df.columns:
                temp_df[col] = temp_df[col].astype(str).str.strip()
            all_dfs.append(temp_df)
        except: continue
    return pd.concat(all_dfs, ignore_index=True) if all_dfs else None

df = yuklash()

# 4. CHAT
st.title(f"🤖 {MAKTAB_NOMI} AI Yordamchisi")

if "messages" not in st.session_state:
    st.session_state.messages = []

for m in st.session_state.messages:
    with st.chat_message(m["role"]): st.markdown(m["content"])

if savol := st.chat_input("Savol yozing (masalan: 9-A sinf yoki Ism)..."):
    st.session_state.messages.append({"role": "user", "content": savol})
    with st.chat_message("user"): st.markdown(savol)
    
    with st.chat_message("assistant"):
        found_data = "Bazada hech narsa topilmadi."
        
        if df is not None:
            # 🔍 AQLLI QIDIRUV (Gap ichidan kalit so'zni qidirish)
            # 1. Sinfni aniqlash (masalan 9-A)
            sinf_match = re.search(r'\d{1,2}-[A-Z|a-z]', savol)
            
            if sinf_match:
                qidiruv_sozi = sinf_match.group().lower()
            else:
                # 2. Agar sinf topilmasa, gapdagi eng uzun so'zni (ism bo'lishi mumkin) qidiradi
                sozlar = [s for s in savol.split() if len(s) > 2 and s.lower() not in ['sinf', 'ro\'yxati', 'kerak']]
                qidiruv_sozi = sozlar[0].lower() if sozlar else savol.lower()

            # Barcha ustunlardan qidirish
            mask = df.apply(lambda row: row.astype(str).str.lower().str.contains(qidiruv_sozi, na=False).any(), axis=1)
            res = df[mask]
            
            if not res.empty:
                st.success(f"Ma'rufjon aka, '{qidiruv_sozi}' bo'yicha ma'lumotlar topildi:")
                st.dataframe(res, use_container_width=True)
                found_data = res.head(15).to_string(index=False)
            else:
                st.warning(f"Bazada '{qidiruv_sozi}' so'ziga mos ma'lumot yo'q.")

        # 🚀 GROQ AI
        try:
            r = requests.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={"Authorization": f"Bearer {GROQ_API_KEY}"},
                json={
                    "model": "llama-3.3-70b-versatile",
                    "messages": [
                        {"role": "system", "content": f"Sen {MAKTAB_NOMI} xodimisiz. Ma'rufjon akaga samimiy, o'zbek tilida javob ber. Topilgan ma'lumotlar: {found_data}"},
                        {"role": "user", "content": savol}
                    ]
                }
            )
            ai_text = r.json()['choices'][0]['message']['content']
            st.markdown(ai_text)
            st.session_state.messages.append({"role": "assistant", "content": ai_text})
        except:
            st.write("AI javob berishda kechikmoqda, lekin jadval yuqorida chiqdi.")
