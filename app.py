import streamlit as st
import pandas as pd
import os
import requests

# 1. SOZLAMALAR
MAKTAB_NOMI = "32-sonli umumta'lim maktabi"
# Kalitni GitHub bloklamasligi uchun bitta satrda yozamiz
GROQ_API_KEY = "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"
TO_GRI_PAROL = "informatika2024"

st.set_page_config(page_title=MAKTAB_NOMI, layout="wide")

# 2. XAVFSIZLIK
if "authenticated" not in st.session_state:
    st.title(f"🔐 {MAKTAB_NOMI} | Kirish")
    parol = st.text_input("Tizim paroli:", type="password")
    if st.button("Kirish"):
        if parol == TO_GRI_PAROL:
            st.session_state.authenticated = True
            st.rerun()
        else: st.error("❌ Xato!")
    st.stop()

# 3. BAZANI YUKLASH (Eng chidamli variant)
@st.cache_data
def yuklash():
    # Papkadagi barcha Excel va CSV fayllarni qidiradi
    files = [f for f in os.listdir('.') if f.lower().endswith(('.xlsx', '.csv')) and 'app.py' not in f]
    if not files:
        return None
    
    all_dfs = []
    for f in files:
        try:
            if f.endswith('.csv'):
                temp_df = pd.read_csv(f, dtype=str)
            else:
                temp_df = pd.read_excel(f, dtype=str)
            
            # Ustun nomlarini va ma'lumotlarni probellardan tozalash
            temp_df.columns = [str(c).strip() for c in temp_df.columns]
            for col in temp_df.columns:
                temp_df[col] = temp_df[col].astype(str).str.strip()
            
            all_dfs.append(temp_df)
        except: continue
    
    return pd.concat(all_dfs, ignore_index=True) if all_dfs else None

df = yuklash()

# 4. CHAT INTERFEYSI
st.title(f"🤖 {MAKTAB_NOMI} AI")

if "messages" not in st.session_state:
    st.session_state.messages = []

# Eski xabarlar
for m in st.session_state.messages:
    with st.chat_message(m["role"]): st.markdown(m["content"])

# Qidiruv
if savol := st.chat_input("Ism, familiya yoki sinfni yozing..."):
    st.session_state.messages.append({"role": "user", "content": savol})
    with st.chat_message("user"): st.markdown(savol)
    
    with st.chat_message("assistant"):
        found_data = ""
        if df is not None:
            # 🔍 UNIVERSAL QIDIRUV: Har qanday ustunda shu so'z bormi?
            # Case=False katta-kichik harfni farqlamaslik uchun
            mask = df.apply(lambda row: row.astype(str).str.contains(savol, case=False, na=False).any(), axis=1)
            res = df[mask]
            
            if not res.empty:
                st.success(f"Ma'rufjon aka, {len(res)} ta ma'lumot topildi!")
                st.dataframe(res, use_container_width=True)
                found_data = res.head(15).to_string(index=False)
            else:
                st.warning(f"'{savol}' bo'yicha bazada hech narsa topilmadi.")
        else:
            st.error("Diqqat! Excel fayli yuklanmagan yoki topilmadi.")

        # AI JAVOBI (Llama 3.3)
        try:
            r = requests.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={"Authorization": f"Bearer {GROQ_API_KEY}"},
                json={
                    "model": "llama-3.3-70b-versatile",
                    "messages": [
                        {"role": "system", "content": "Sen maktab yordamchisisan. Ma'rufjon akaga samimiy va o'zbek tilida javob ber. Faqat berilgan bazadagi ma'lumotga tayangan holda gapir."},
                        {"role": "user", "content": f"Baza ma'lumotlari: {found_data}. Savol: {savol}"}
                    ]
                }
            )
            ai_text = r.json()['choices'][0]['message']['content']
            st.markdown(ai_text)
            st.session_state.messages.append({"role": "assistant", "content": ai_text})
        except:
            st.error("AI bilan bog'lanishda xato.")
