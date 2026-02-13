import streamlit as st
import pandas as pd
import os
import requests
import re

# --- 1. MAKTAB MA'LUMOTLARI ---
MAKTAB_NOMI = "32-sonli umumta'lim maktabi" 
DIREKTOR_FIO = "Eshmatov Toshmat" 
K1 = "gsk_aj4oXwYYxRBhcrPghQwS"
K2 = "WGdyb3FYSu9boRvJewpZakpofhrPMklX"
GROQ_API_KEY = K1 + K2
TO_GRI_PAROL = "informatika2024"

st.set_page_config(page_title=f"{MAKTAB_NOMI} AI", layout="wide")

# --- PAROL ---
if "authenticated" not in st.session_state:
    st.title(f"🔐 {MAKTAB_NOMI} | Tizim")
    parol = st.text_input("Parol:", type="password")
    if st.button("Kirish"):
        if parol == TO_GRI_PAROL:
            st.session_state.authenticated = True
            st.rerun()
        else: st.error("❌ Xato!")
    st.stop()

# --- BAZA YUKLASH ---
@st.cache_data
def yuklash():
    files = [f for f in os.listdir('.') if f.lower().endswith(('.xlsx', '.csv')) and 'app.py' not in f]
    all_data = []
    for f in files:
        try:
            if f.endswith('.csv'): df = pd.read_csv(f, dtype=str)
            else:
                excel = pd.ExcelFile(f)
                for sheet in excel.sheet_names:
                    df_s = pd.read_excel(f, sheet_name=sheet, dtype=str)
                    df_s.columns = [str(c).strip().lower() for c in df_s.columns] 
                    for col in df_s.columns:
                        df_s[col] = df_s[col].astype(str).str.strip()
                    all_data.append(df_s)
        except: continue
    return pd.concat(all_data, ignore_index=True) if all_data else None

df = yuklash()

# --- CHAT ---
if "messages" not in st.session_state:
    st.session_state.messages = []

for m in st.session_state.messages:
    with st.chat_message(m["role"]): st.markdown(m["content"])

if savol := st.chat_input("Savolingizni yozing (masalan: 9-A ro'yxati)..."):
    st.session_state.messages.append({"role": "user", "content": savol})
    with st.chat_message("user"): st.markdown(savol)
    
    with st.chat_message("assistant"):
        found_data = "Bazada hech narsa topilmadi."
        sinf_data = pd.DataFrame()

        if df is not None:
            # 🔍 AQLLI QIDIRUV
            qidiruv_sozi = savol.lower()
            sinf_match = re.search(r'\d{1,2}-[a-z|A-Z]', savol)
            
            if sinf_match:
                kalit = sinf_match.group().lower()
                if 'sinfi' in df.columns:
                    sinf_data = df[df['sinfi'].str.lower() == kalit]
            
            if sinf_data.empty:
                # BU YERDA XATO TUZATILDI: Tirnoqlar to'g'rilandi
                keywords = [s for s in savol.split() if len(s) > 2 and s.lower() not in ["sinf", "ro'yxati", "kerak", "ber"]]
                if keywords:
                    mask = df.apply(lambda row: any(k.lower() in str(v).lower() for k in keywords for v in row), axis=1)
                    sinf_data = df[mask]

            if not sinf_data.empty:
                st.success("Ma'rufjon aka, topildi!")
                st.dataframe(sinf_data, use_container_width=True)
                found_data = sinf_data.head(20).to_string(index=False)

        # 🚀 GROQ AI
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
        
        payload = {
            "model": "llama-3.3-70b-versatile",
            "messages": [
                {"role": "system", "content": f"Sen {MAKTAB_NOMI} xodimisiz. Ma'rufjon akaga samimiy javob ber. Baza: {found_data}"},
                {"role": "user", "content": savol}
            ]
        }
        
        try:
            r = requests.post(url, json=payload, headers=headers, timeout=15)
            ai_text = r.json()['choices'][0]['message']['content']
        except:
            ai_text = "Ma'lumotlar jadvalda."

        st.markdown(ai_text)
        st.session_state.messages.append({"role": "assistant", "content": ai_text})
