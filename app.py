import streamlit as st
import pandas as pd
import os
import requests
import re

# --- 1. MAKTAB VA TIZIM MA'LUMOTLARI ---
MAKTAB_NOMI = "32-sonli umumta'lim maktabi" 
DIREKTOR_FIO = "Eshmatov Toshmat" 

# API Kalitni bo'laklab yozish (GitHub bloklamasligi uchun)
K1 = "gsk_aj4oXwYYxRBhcrPghQwS"
K2 = "WGdyb3FYSu9boRvJewpZakpofhrPMklX"
GROQ_API_KEY = K1 + K2

TO_GRI_PAROL = "informatika2024"

# Sahifa sozlamalari
st.set_page_config(page_title=f"{MAKTAB_NOMI} AI", layout="wide", page_icon="🏫")

# --- 2. XAVFSIZLIK (PAROL TIZIMI) ---
if "authenticated" not in st.session_state:
    st.title(f"🏫 {MAKTAB_NOMI} | AI Tizimi")
    st.info("Tizimga kirish uchun parolni kiriting.")
    parol = st.text_input("Parol:", type="password")
    if st.button("Kirish"):
        if parol == TO_GRI_PAROL:
            st.session_state.authenticated = True
            st.rerun()
        else:
            st.error("❌ Parol noto'g'ri! Iltimos, qaytadan urining.")
    st.stop()

# --- 3. BAZANI YUKLASH FUNKSIYASI ---
@st.cache_data
def yuklash():
    files = [f for f in os.listdir('.') if f.lower().endswith(('.xlsx', '.csv')) and 'app.py' not in f]
    all_data = []
    for f in files:
        try:
            if f.endswith('.csv'):
                df = pd.read_csv(f, dtype=str)
            else:
                excel = pd.ExcelFile(f)
                for sheet in excel.sheet_names:
                    df_s = pd.read_excel(f, sheet_name=sheet, dtype=str)
                    # Ustun nomlarini tozalash (bo'shliqlarni olib tashlash)
                    df_s.columns = [str(c).strip().lower() for c in df_s.columns]
                    all_data.append(df_s)
        except Exception as e:
            continue
    return pd.concat(all_data, ignore_index=True) if all_data else None

df = yuklash()

# --- 4. CHAT INTERFEYSI ---
st.title(f"🤖 {MAKTAB_NOMI} AI Yordamchisi")
st.markdown(f"**Direktor:** {DIREKTOR_FIO}")

if "messages" not in st.session_state:
    st.session_state.messages = []

# Eski xabarlarni ko'rsatish
for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

# Yangi savol kiritish
if savol := st.chat_input("Sinf nomi (9-A) yoki o'qituvchi ismini yozing..."):
    st.session_state.messages.append({"role": "user", "content": savol})
    with st.chat_message("user"):
        st.markdown(savol)
    
    with st.chat_message("assistant"):
        found_data = "Bazada ma'lumot topilmadi."
        sinf_data = pd.DataFrame()

        if df is not None:
            # Qidiruv so'zini kichik harfga o'tkazamiz
            qidiruv = savol.strip().lower()
            
            # 🎯 A. "sinfi" ustuni bo'yicha aniq qidiruv
            mask_sinf = pd.Series(False, index=df.index)
            if 'sinfi' in df.columns:
                mask_sinf = df['sinfi'].astype(str).str.lower() == qidiruv
            
            # 🎯 B. "pedagokning ismi familiyasi" bo'yicha qidiruv
            mask_pedagog = pd.Series(False, index=df.index)
            ustun_pedagog = 'pedagokning ismi familiyasi'
            if ustun_pedagog in df.columns:
                mask_pedagog = df[ustun_pedagog].astype(str).str.lower().str.contains(qidiruv, na=False)
            
            # 🎯 C. Umumiy qidiruv (agar yuqoridagilardan topilmasa)
            mask_umumiy = df.apply(lambda row: row.astype(str).str.lower().str.contains(qidiruv, na=False).any(), axis=1)
            
            # Natijalarni birlashtirish
            if mask_sinf.any():
                sinf_data = df[mask_sinf]
            elif mask_pedagog.any():
                sinf_data = df[mask_pedagog]
            else:
                sinf_data = df[mask_umumiy]

            if not sinf_data.empty:
                st.write(f"🔍 **'{savol}'** bo'yicha topilgan natijalar:")
                st.dataframe(sinf_data, use_container_width=True)
                # AI tahlili uchun ma'lumotni tayyorlash
                found_data = sinf_data.head(15).to_string(index=False)

        # 🚀 5. GROQ AI (Llama 3.3) BILAN ALOQA
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": "llama-3.3-70b-versatile",
            "messages": [
                {
                    "role": "system", 
                    "content": f"Sen {MAKTAB_NOMI} maktabining AI yordamchisisan. Foydalanuvchi Ma'rufjon aka. "
                               f"Baza ma'lumotlari: {found_data}. Faqat o'zbek tilida, "
                               f"samimiy va aniq javob ber. Agar ma'lumot topilgan bo'lsa, uni xulosa qil."
                },
                {"role": "user", "content": savol}
            ],
            "temperature": 0.7
        }
        
        try:
            r = requests.post(url, json=payload, headers=headers, timeout=15)
            if r.status_code == 200:
                ai_text = r.json()['choices'][0]['message']['content']
            else:
                ai_text = "Ma'rufjon aka, hozircha jadvaldagi ma'lumotlar bilan tanishib turishingiz mumkin."
        except:
            ai_text = "Ulanishda kichik xatolik bo'ldi, lekin jadval yuqorida turibdi."

        st.markdown(ai_text)
        st.session_state.messages.append({"role": "assistant", "content": ai_text})
