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
                    df_s.columns = [str(c).strip() for c in df_s.columns] # Ustun nomlaridagi bo'shliqlarni o'chirish
                    all_data.append(df_s)
        except: continue
    return pd.concat(all_data, ignore_index=True) if all_data else None

df = yuklash()

# --- CHAT ---
if "messages" not in st.session_state:
    st.session_state.messages = []

for m in st.session_state.messages:
    with st.chat_message(m["role"]): st.markdown(m["content"])

if savol := st.chat_input("Savolingizni yozing (masalan: 9-A)..."):
    st.session_state.messages.append({"role": "user", "content": savol})
    with st.chat_message("user"): st.markdown(savol)
    
    with st.chat_message("assistant"):
        found_data = "Bazada hech narsa topilmadi."
        sinf_data = pd.DataFrame()

        if df is not None:
            # 🎯 AQLLI FILTR: "sinfi" ustunidan aynan qidirish
            if 'sinfi' in df.columns:
                # To'liq mos kelishini tekshirish (masalan: "9-A" bo'lsa faqat "9-A" ni oladi)
                mask = df['sinfi'].astype(str).str.contains(rf'^{savol}$', case=False, na=False, regex=True)
                sinf_data = df[mask]
            
            # Agar aniq sinf topilmasa, umumiy qidiruvga o'tish (ism yoki boshqa ma'lumot uchun)
            if sinf_data.empty:
                mask = df.apply(lambda row: row.astype(str).str.contains(savol, case=False, na=False).any(), axis=1)
                sinf_data = df[mask]

            if not sinf_data.empty:
                st.write(f"🔍 '{savol}' bo'yicha ma'lumotlar:")
                st.dataframe(sinf_data, use_container_width=True)
                found_data = f"Topilgan ma'lumotlar jadvali: {sinf_data.head(10).to_dict(orient='records')}"

        # 🚀 GROQ AI (Llama 3.3)
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
        
        payload = {
            "model": "llama-3.3-70b-versatile",
            "messages": [
                {"role": "system", "content": f"Sen {MAKTAB_NOMI} xodimisiz. Direktor: {DIREKTOR_FIO}. Ma'rufjon akaga samimiy va aniq javob ber."},
                {"role": "user", "content": f"Baza: {found_data}. Savol: {savol}"}
            ]
        }
        
        try:
            r = requests.post(url, json=payload, headers=headers, timeout=15)
            ai_text = r.json()['choices'][0]['message']['content']
        except:
            ai_text = "Ma'rufjon aka, ma'lumotlarni jadvaldan ko'rishingiz mumkin."

        st.markdown(ai_text)
        st.session_state.messages.append({"role": "assistant", "content": ai_text})
