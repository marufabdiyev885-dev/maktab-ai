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

# --- 2. PAROL TIZIMI ---
if "authenticated" not in st.session_state:
    st.title(f"🔐 {MAKTAB_NOMI} | Kirish")
    parol = st.text_input("Parolni kiriting:", type="password")
    if st.button("Kirish"):
        if parol == TO_GRI_PAROL:
            st.session_state.authenticated = True
            st.rerun()
        else: st.error("❌ Parol noto'g'ri!")
    st.stop()

# --- 3. BAZANI YUKLASH (ENG KUCHLI VARIANT) ---
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
                    # Ustun nomlarini va kataklarni tozalaymiz
                    df_s.columns = [str(c).strip().lower() for c in df_s.columns]
                    for col in df_s.columns:
                        df_s[col] = df_s[col].astype(str).str.strip()
                    all_data.append(df_s)
        except: continue
    return pd.concat(all_data, ignore_index=True) if all_data else None

df = yuklash()

# --- 4. CHAT ---
st.title(f"🤖 {MAKTAB_NOMI} AI Yordamchisi")

if "messages" not in st.session_state:
    st.session_state.messages = []

for m in st.session_state.messages:
    with st.chat_message(m["role"]): st.markdown(m["content"])

if savol := st.chat_input("Sinf (9-A) yoki o'qituvchi ismini yozing..."):
    st.session_state.messages.append({"role": "user", "content": savol})
    with st.chat_message("user"): st.markdown(savol)
    
    with st.chat_message("assistant"):
        found_data = "Bazada bunday ma'lumot topilmadi."
        qidiruv = savol.lower().strip()
        
        if df is not None:
            # 🔍 QIDIRUV MANTIG'I (Xatolarga chidamli)
            # Har qanday ustunda qidiruv so'zi qatnashganini tekshirish
            mask = df.apply(lambda row: row.astype(str).str.lower().str.contains(qidiruv, na=False).any(), axis=1)
            
            res_df = df[mask]
            if not res_df.empty:
                st.write(f"🔍 **Topilgan natijalar:**")
                st.dataframe(res_df, use_container_width=True)
                found_data = res_df.head(20).to_string(index=False)

        # 🚀 GROQ AI
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
        
        sys_prompt = f"""Sen {MAKTAB_NOMI} maktabi xodimisiz. Foydalanuvchi: Ma'rufjon aka.
        Baza ma'lumotlari: {found_data}
        Agar ma'lumot topilgan bo'lsa, uni jadvalga qarab xulosa qil. 
        Agar topilmagan bo'lsa, Ma'rufjon akaga ma'lumot yo'qligini samimiy tushuntir. Faqat o'zbekcha javob ber."""

        payload = {
            "model": "llama-3.3-70b-versatile",
            "messages": [{"role": "system", "content": sys_prompt}, {"role": "user", "content": savol}]
        }
        
        try:
            r = requests.post(url, json=payload, headers=headers, timeout=15)
            ai_text = r.json()['choices'][0]['message']['content']
        except:
            ai_text = "Ma'lumotlar yuqoridagi jadvalda."

        st.markdown(ai_text)
        st.session_state.messages.append({"role": "assistant", "content": ai_text})
