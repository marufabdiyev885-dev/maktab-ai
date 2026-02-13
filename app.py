import streamlit as st
import pandas as pd
import os
import requests
import re
import io
import docx
import random
from datetime import datetime

# --- 1. ASOSIY SOZLAMALAR ---
MAKTAB_NOMI = "1-sonli umumta'lim maktabi"
DIREKTOR_FIO = "Mahmudov Matyoqub Narzulloyevich"
GROQ_API_KEY = "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"
TO_GRI_PAROL = "informatika2024"

st.set_page_config(page_title=MAKTAB_NOMI, layout="wide")

# --- 2. ADMIN STATISTIKA (SESSION STATE) ---
# Bu qism raqamlarni xotirada saqlab turadi
if "stats" not in st.session_state:
    st.session_state.stats = {
        "o_quvchi": "1250",
        "o_qituvchi": "85",
        "sinflar": "42",
        "yutuq": "18"
    }

# --- 3. RAHBARIYAT VA ADMIN PANELI (SIDEBAR) ---
with st.sidebar:
    st.markdown(f"## 🏛 {MAKTAB_NOMI}")
    st.image("https://cdn-icons-png.flaticon.com/512/2859/2859706.png", width=80)
    
    st.divider()

    # 🌟 KUN HIKMATI
    hikmatlar = [
        "Ilm — saodat kalitidir.",
        "Ustoz — otangdek ulug‘, darsing — davlatingdek aziz.",
        "Informatika — kelajak tili!",
        "Muvaffaqiyatning siri — har kuni bir qadam oldinga yurishda."
    ]
    st.warning(f"🌟 **Kun hikmati:**\n\n*{random.choice(hikmatlar)}*")

    st.divider()
    
    # ⚙️ ADMIN PANEL (FAQAT SIZ UCHUN)
    with st.expander("⚙️ Admin Boshqaruvi"):
        admin_kod = st.text_input("Admin paroli:", type="password")
        if admin_kod == TO_GRI_PAROL:
            st.write("📊 Statistikani yangilang:")
            st.session_state.stats["o_quvchi"] = st.text_input("O'quvchilar:", st.session_state.stats["o_quvchi"])
            st.session_state.stats["o_qituvchi"] = st.text_input("O'qituvchilar:", st.session_state.stats["o_qituvchi"])
            st.session_state.stats["sinflar"] = st.text_input("Sinflar:", st.session_state.stats["sinflar"])
            st.session_state.stats["yutuq"] = st.text_input("Yutuqlar:", st.session_state.stats["yutuq"])
            st.success("Raqamlar yangilandi!")
        else:
            st.caption("Raqamlarni o'zgartirish uchun admin kodini yozing.")

    st.divider()
    st.info(f"**Direktor:**\n\n{DIREKTOR_FIO}")
    
    st.divider()
    st.caption("© 2026 Maktab AI Tizimi")

# --- 4. XAVFSIZLIK (KIRISH) ---
if "authenticated" not in st.session_state:
    st.title(f"🏫 {MAKTAB_NOMI} | Tizim")
    parol = st.text_input("Tizimga kirish parolini kiriting:", type="password")
    if st.button("Kirish"):
        if parol == TO_GRI_PAROL:
            st.session_state.authenticated = True
            st.rerun()
        else: st.error("❌ Parol xato!")
    st.stop()

# --- 5. ASOSIY SAHIFADA STATISTIKA ---
st.title(f"📊 {MAKTAB_NOMI} Dashboard")
bugun = datetime.now().strftime("%d-%m-%Y")
st.write(f"📅 Bugungi sana: **{bugun}**")

# Statistikani chiroyli kartochkalar ko'rinishida chiqarish
c1, c2, c3, c4 = st.columns(4)
c1.metric("👥 O'quvchilar", st.session_state.stats["o_quvchi"])
c2.metric("👩‍🏫 O'qituvchilar", st.session_state.stats["o_qituvchi"])
c3.metric("🏫 Sinflar", st.session_state.stats["sinflar"])
c4.metric("🏆 Yutuqlar", st.session_state.stats["yutuq"])

st.divider()

# --- 6. BAZANI YUKLASH ---
@st.cache_data
def yuklash():
    files = [f for f in os.listdir('.') if f.lower().endswith(('.xlsx', '.csv', '.docx')) and 'app.py' not in f]
    all_data = []
    word_text = ""
    for f in files:
        try:
            if f.endswith('.docx'):
                doc = docx.Document(f)
                word_text += "\n".join([para.text for para in doc.paragraphs])
            else:
                df_s = pd.read_excel(f, dtype=str) if f.endswith('.xlsx') else pd.read_csv(f, dtype=str)
                df_s.columns = [str(c).strip().lower() for c in df_s.columns]
                all_data.append(df_s)
        except: continue
    return (pd.concat(all_data, ignore_index=True) if all_data else None), word_text

df, maktab_doc_content = yuklash()

# --- 7. CHAT VA QIDIRUV ---
st.subheader("🤖 AI Metodist va Qidiruv")

if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "Assalomu alaykum! Maktab bazasidan ma'lumot qidiramizmi yoki yangi dars ssenariysi kerakmi?"}]

for m in st.session_state.messages:
    with st.chat_message(m["role"]): st.markdown(m["content"])

if savol := st.chat_input("Savolingizni yozing..."):
    st.session_state.messages.append({"role": "user", "content": savol})
    with st.chat_message("user"): st.markdown(savol)
    
    with st.chat_message("assistant"):
        found_data = ""
        soni = 0
        
        # 🔵 QIDIRUV
        if df is not None:
            keywords = [s.lower() for s in savol.split() if len(s) > 2]
            res = df[df.apply(lambda row: any(k in str(v).lower() for k in keywords for v in row), axis=1)]
            
            if not res.empty:
                st.dataframe(res, use_container_width=True)
                soni = len(res) 
                found_data = res.head(30).to_string(index=False)
                
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                    res.to_excel(writer, index=False)
                st.download_button(label="📥 Excelni yuklab olish", data=output.getvalue(), file_name="royxat.xlsx")

        # 🚀 AI JAVOBI
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
        payload = {
            "model": "llama-3.3-70b-versatile",
            "messages": [
                {"role": "system", "content": f"Sen {MAKTAB_NOMI} metodistisan. Shirin-zabon bo'l."},
                {"role": "user", "content": f"Baza: {found_data}. Savol: {savol}"}
            ],
            "temperature": 0.8
        }
        
        try:
            r = requests.post(url, json=payload, headers=headers)
            ai_text = r.json()['choices'][0]['message']['content']
        except:
            ai_text = "Hozircha javob bera olmayman, lekin ma'lumotlar tayyor!"

        st.info(ai_text)
        st.session_state.messages.append({"role": "assistant", "content": ai_text})
