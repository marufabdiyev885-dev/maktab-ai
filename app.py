import streamlit as st
import pandas as pd
import os
import requests

# --- 1. MAKTAB MA'LUMOTLARI ---
MAKTAB_NOMI = "32-sonli umumta'lim maktabi" 
DIREKTOR_FIO = "Eshmatov Toshmat" 

K1 = "gsk_aj4oXwYYxRBhcrPghQwS"
K2 = "WGdyb3FYSu9boRvJewpZakpofhrPMklX"
GROQ_API_KEY = K1 + K2
TO_GRI_PAROL = "informatika2024"

st.set_page_config(page_title=f"{MAKTAB_NOMI} AI", layout="wide")

# --- 2. XAVFSIZLIK ---
if "authenticated" not in st.session_state:
    st.title(f"🔐 {MAKTAB_NOMI} | Kirish")
    parol = st.text_input("Tizim paroli:", type="password")
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
            if f.endswith('.csv'): df = pd.read_csv(f, dtype=str)
            else:
                excel = pd.ExcelFile(f)
                for sheet in excel.sheet_names:
                    df_s = pd.read_excel(f, sheet_name=sheet, dtype=str)
                    df_s.columns = [str(c).strip().lower() for c in df_s.columns]
                    all_data.append(df_s)
        except: continue
    return pd.concat(all_data, ignore_index=True) if all_data else None

df = yuklash()

# --- 4. CHAT ---
st.title(f"🤖 {MAKTAB_NOMI} AI")

if "messages" not in st.session_state:
    st.session_state.messages = []

for m in st.session_state.messages:
    with st.chat_message(m["role"]): st.markdown(m["content"])

if savol := st.chat_input("Savol yozing (masalan: o'qituvchilar yoki 9-A)..."):
    st.session_state.messages.append({"role": "user", "content": savol})
    with st.chat_message("user"): st.markdown(savol)
    
    with st.chat_message("assistant"):
        found_data = "Bazada ma'lumot topilmadi."
        qidiruv = savol.lower().strip()
        
        if df is not None:
            # 🎯 Maxsus qidiruv logic:
            mask = pd.Series(False, index=df.index)
            
            # Agar foydalanuvchi "o'qituvchi" yoki "pedagog" deb so'rasa
            if "o'qituvchi" in qidiruv or "pedagog" in qidiruv:
                if 'sinfi' in df.columns:
                    mask = df['sinfi'].astype(str).str.lower().str.contains("o'qituvchi|pedagog", na=False)
            
            # Agar sinf yoki ism so'ralsa
            if not mask.any():
                if 'sinfi' in df.columns:
                    mask |= (df['sinfi'].astype(str).str.lower() == qidiruv)
                if 'pedagokning ismi familiyasi' in df.columns:
                    mask |= (df['pedagokning ismi familiyasi'].astype(str).str.lower().str.contains(qidiruv, na=False))
            
            # Agar hali ham bo'sh bo'lsa umumiy qidiruv
            if not mask.any():
                mask = df.apply(lambda row: row.astype(str).str.lower().str.contains(qidiruv, na=False).any(), axis=1)
            
            res_df = df[mask]
            if not res_df.empty:
                st.write(f"🔍 **Topilgan ma'lumotlar:**")
                st.dataframe(res_df, use_container_width=True)
                found_data = res_df.head(20).to_string(index=False)

        # 🚀 GROQ AI
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
        
        # System promptni tozaladik, AI endi o'zidan to'qimaydi, faqat bazadagini aytadi
        sys_prompt = f"""Sen {MAKTAB_NOMI} boti san. Direktor: {DIREKTOR_FIO}.
        Faqat taqdim etilgan baza asosida javob ber. 
        Baza ma'lumotlari: {found_data}
        Ma'rufjon akaga samimiy o'zbek tilida javob ber."""

        payload = {
            "model": "llama-3.3-70b-versatile",
            "messages": [
                {"role": "system", "content": sys_prompt},
                {"role": "user", "content": savol}
            ]
        }
        
        try:
            r = requests.post(url, json=payload, headers=headers, timeout=15)
            ai_text = r.json()['choices'][0]['message']['content']
        except:
            ai_text = "Ma'lumotlar jadvalda ko'rsatildi."

        st.markdown(ai_text)
        st.session_state.messages.append({"role": "assistant", "content": ai_text})
