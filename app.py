import streamlit as st
import pandas as pd
import os
import requests
import re
import io
import docx  # Word fayllari uchun
import random

# --- 1. ASOSIY SOZLAMALAR ---
MAKTAB_NOMI = "1-sonli umumta'lim maktabi"
DIREKTOR_FIO = "Mahmudov Matyoqub Narzulloyevich"
GROQ_API_KEY = "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"
TO_GRI_PAROL = "informatika2024"
MONITORING_KODI = "admin777" 
BOT_TOKEN = "8524007504:AAFiMXSbXhe2M-84WlNM16wNpzhNolfQIf8"
GURUH_ID = "-5045481739" 

st.set_page_config(page_title=MAKTAB_NOMI, layout="wide")

# --- 2. RAHBARIYAT VA SIDEBAR ---
with st.sidebar:
    st.markdown(f"## 🏛 {MAKTAB_NOMI}")
    st.image("https://cdn-icons-png.flaticon.com/512/2859/2859706.png", width=80)
    st.divider()
    menu = st.radio("Bo'limni tanlang:", ["🤖 AI Yordamchi", "📊 Jurnal Monitoringi"])
    st.divider()
    st.info(f"**Direktor:**\n{DIREKTOR_FIO}")

# --- 3. XAVFSIZLIK ---
if "authenticated" not in st.session_state:
    st.title(f"🏫 {MAKTAB_NOMI} | Tizim")
    parol = st.text_input("Parolni kiriting:", type="password")
    if st.button("Kirish"):
        if parol == TO_GRI_PAROL:
            st.session_state.authenticated = True
            st.rerun()
        else: st.error("❌ Parol xato!")
    st.stop()

# --- 4. BAZANI YUKLASH (AI uchun) ---
@st.cache_data
def yuklash():
    files = [f for f in os.listdir('.') if f.lower().endswith(('.xlsx', '.xls', '.csv', '.docx')) and 'app.py' not in f]
    all_data = []
    word_text = ""
    for f in files:
        try:
            if f.endswith('.docx'):
                doc = docx.Document(f)
                word_text += "\n".join([para.text for para in doc.paragraphs])
            elif f.endswith('.xls'):
                df_s = pd.read_excel(f, engine='xlrd', dtype=str)
                df_s.columns = [str(c).strip().lower() for c in df_s.columns]
                all_data.append(df_s)
            else:
                df_s = pd.read_excel(f, engine='openpyxl', dtype=str) if f.endswith('.xlsx') else pd.read_csv(f, dtype=str)
                df_s.columns = [str(c).strip().lower() for c in df_s.columns]
                all_data.append(df_s)
        except: continue
    return (pd.concat(all_data, ignore_index=True) if all_data else None), word_text

df_baza, maktab_doc_content = yuklash()

# --- 5. SAHIFALAR ---

# A) AI YORDAMCHI
if menu == "🤖 AI Yordamchi":
    st.title(f"🤖 {MAKTAB_NOMI} AI Yordamchisi")
    if "messages" not in st.session_state:
        st.session_state.messages = [{"role": "assistant", "content": "Assalomu alaykum! Hurmatli foydalanuvchi, maktab bazasi bo'yicha qanday yordam bera olaman?"}]

    for m in st.session_state.messages:
        with st.chat_message(m["role"]): st.markdown(m["content"])

    if savol := st.chat_input("Savolingizni yozing..."):
        st.session_state.messages.append({"role": "user", "content": savol})
        with st.chat_message("user"): st.markdown(savol)
        
        with st.chat_message("assistant"):
            found_data = ""
            if df_baza is not None:
                keywords = [s.lower() for s in savol.split() if len(s) > 2]
                if keywords:
                    res = df_baza[df_baza.apply(lambda row: any(k in str(v).lower() for k in keywords for v in row), axis=1)]
                    if not res.empty:
                        st.dataframe(res, use_container_width=True)
                        found_data = res.head(40).to_string(index=False)

            system_prompt = f"Sen {MAKTAB_NOMI} maktabining rasmiy yordamchisisan. Suhbatdoshingga 'Hurmatli foydalanuvchi' deb murojaat qil."
            payload = {
                "model": "llama-3.3-70b-versatile",
                "messages": [{"role": "system", "content": system_prompt}, {"role": "user", "content": f"Baza: {found_data}. Savol: {savol}"}]
            }
            try:
                r = requests.post("https://api.groq.com/openai/v1/chat/completions", json=payload, headers={"Authorization": f"Bearer {GROQ_API_KEY}"})
                ai_text = r.json()['choices'][0]['message']['content']
            except: ai_text = "Sizga yordam berishdan xursandman, hurmatli foydalanuvchi!"
            st.markdown(ai_text)
            st.session_state.messages.append({"role": "assistant", "content": ai_text})

# B) JURNAL MONITORINGI ( XLS VA XLSX UCHUN TO'LIQ )
elif menu == "📊 Jurnal Monitoringi":
    st.title("📊 Jurnal Monitoringi")
    
    if "m_auth" not in st.session_state: st.session_state.m_auth = False
    if not st.session_state.m_auth:
        m_pass = st.text_input("Monitoring kodi:", type="password")
        if st.button("Tasdiqlash"):
            if m_pass == MONITORING_KODI:
                st.session_state.m_auth = True
                st.rerun()
            else: st.error("❌ Kod noto'g'ri!")
        st.stop()

    j_fayl = st.file_uploader("Excelni yuklang (.xlsx yoki .xls)", type=['xlsx', 'xls'])
    if j_fayl:
        try:
            # Fayl kengaytmasini aniqlash va mos engine bilan o'qish
            file_extension = j_fayl.name.split('.')[-1].lower()
            if file_extension == 'xls':
                df_j = pd.read_excel(j_fayl, engine='xlrd')
            else:
                df_j = pd.read_excel(j_fayl, engine='openpyxl')
                
            st.write("📊 Yuklangan ma'lumotlar:")
            st.dataframe(df_j.head())
            
            c_oqit = st.selectbox("O'qituvchi ustuni:", df_j.columns)
            c_baho = st.selectbox("Baho ustuni (Masalan: 4 Undan 3):", df_j.columns)
            
            if st.button("📢 Telegramga yuborish"):
                def tekshir(qiymat):
                    s = str(qiymat).lower()
                    if "undan" in s:
                        try:
                            q = s.split("undan")
                            # Raqamlarni ajratib olish
                            jami = int(re.search(r'\d+', q[0]).group())
                            bor = int(re.search(r'\d+', q[1]).group())
                            return bor < jami
                        except: return False
                    return False

                xatolar = df_j[df_j[c_baho].apply(tekshir)]
                
                if not xatolar.empty:
                    text = f"<b>⚠️ JURNAL MONITORINGI</b>\n<i>{MAKTAB_NOMI}</i>\n\nKamchiliklar:\n"
                    for _, row in xatolar.iterrows():
                        text += f"❌ {row[c_oqit]} -> {row[c_baho]}\n"
                else:
                    text = f"<b>✅ JURNAL MONITORINGI</b>\n<i>{MAKTAB_NOMI}</i>\n\n✨ <b>Jurnallar 100 foiz baholangan.</b> Hamma darslarga baholar to'liq qo'yilgan!"

                requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", 
                              json={"chat_id": GURUH_ID, "text": text, "parse_mode": "HTML"})
                st.success("Hisobot guruhga yuborildi!")

        except Exception as e:
            st.error(f"Faylni o'qishda xatolik: {e}")
            st.info("Iltimos, requirements.txt faylida 'xlrd' borligini tekshiring.")
