import streamlit as st
import pandas as pd
import os
import requests
import docx

# --- 1. ASOSIY SOZLAMALAR ---
MAKTAB_NOMI = "1-sonli umumiy o'rta ta'lim maktabi"
DIREKTOR_FIO = "Mahmudov Matyoqub Narzulloyevich"
GROQ_API_KEY = "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"
TO_GRI_PAROL = "informatika2024"
MONITORING_KODI = "admin777"
BOT_TOKEN = "8524007504:AAFiMXSbXhe2M-84WlNM16wNpzhNolfQIf8"
GURUH_ID = "-1003047388159"

st.set_page_config(page_title=MAKTAB_NOMI)

# --- 2. BAZANI YUKLASH FUNKSIYASI ---
@st.cache_data
def yuklash():
    # Papkadagi Excel va Word fayllarni qidirish
    files = [f for f in os.listdir('.') if f.lower().endswith(('.xlsx', '.xls', '.docx')) and f != 'app.py']
    all_data = []
    word_text = ""
    
    for f in files:
        try:
            if f.endswith('.docx'):
                doc = docx.Document(f)
                word_text += "\n".join([para.text for para in doc.paragraphs])
            else:
                try:
                    df_s = pd.read_excel(f, dtype=str)
                except:
                    df_s = pd.read_html(f)[0]
                all_data.append(df_s)
        except Exception as e:
            print(f"Faylni o'qishda xato ({f}): {e}")
            
    combined_df = pd.concat(all_data, ignore_index=True) if all_data else None
    return combined_df, word_text

# --- 3. LOGIN TIZIMI ---
if "authenticated" not in st.session_state:
    st.title(MAKTAB_NOMI)
    st.subheader("Tizimga kirish")
    parol = st.text_input("Parolni kiriting:", type="password")
    
    if st.button("Kirish"):
        if parol == TO_GRI_PAROL:
            st.session_state.authenticated = True
            st.rerun()
        else:
            st.error("Xato parol kiritildi!")
    st.stop()

# --- 4. ASOSIY PANEL ---
df_baza, word_baza = yuklash()

with st.sidebar:
    st.title(MAKTAB_NOMI)
    st.write(f"Direktor: {DIREKTOR_FIO}")
    st.divider()
    menu = st.radio("Bo'limni tanlang:", ["🤖 AI Yordamchi", "📊 Jurnal Monitoringi"])
    
    if st.button("Chiqish"):
        del st.session_state.authenticated
        st.rerun()

# --- 5. SAHIFALAR ---

# 1-Sahifa: AI Yordamchi
if menu == "🤖 AI Yordamchi":
    st.header("🤖 AI Yordamchi")
    
    if "messages" not in st.session_state:
        st.session_state.messages = [{"role": "assistant", "content": "Assalomu alaykum! Maktab bazasi bo'yicha savol bera olasiz."}]
    
    for m in st.session_state.messages:
        with st.chat_message(m["role"]):
            st.markdown(m["content"])
    
    if savol := st.chat_input("Savolingizni yozing..."):
        st.session_state.messages.append({"role": "user", "content": savol})
        with st.chat_message("user"):
            st.markdown(savol)
        
        with st.chat_message("assistant"):
            # Bazadan ma'lumot tayyorlash
            found_data = df_baza.head(20).to_string() if df_baza is not None else "Baza bo'sh"
            
            payload = {
                "model": "llama-3.3-70b-versatile",
                "messages": [
                    {"role": "system", "content": f"Sen {MAKTAB_NOMI} maktabining AI yordamchisisan. Quyidagi baza ma'lumotlaridan foydalanib javob ber: {found_data} {word_baza[:1000]}"},
                    {"role": "user", "content": savol}
                ]
            }
            
            headers = {"Authorization": f"Bearer {GROQ_API_KEY}"}
            
            try:
                r = requests.post("https://api.groq.com/openai/v1/chat/completions", json=payload, headers=headers)
                ai_response = r.json()['choices'][0]['message']['content']
            except:
                ai_response = "Xatolik: API ga ulanib bo'lmadi yoki kalit xato."
                
            st.markdown(ai_response)
            st.session_state.messages.append({"role": "assistant", "content": ai_response})

# 2-Sahifa: Monitoring
elif menu == "📊 Jurnal Monitoringi":
    st.header("📊 Jurnal Monitoringi")
    
    if "m_auth" not in st.session_state:
        st.session_state.m_auth = False
    
    if not st.session_state.m_auth:
        m_pass = st.text_input("Monitoring kodini kiriting:", type="password")
        if st.button("Tasdiqlash"):
            if m_pass == MONITORING_KODI:
                st.session_state.m_auth = True
                st.rerun()
            else:
                st.error("Maxsus kod xato!")
        st.stop()
        
    st.info("eMaktabdan yuklangan Excel faylni tahlil qilish bo'limi.")
    fayl = st.file_uploader("Faylni tanlang", type=['xlsx', 'xls'])
    if fayl:
        st.success("Fayl yuklandi!")
        df_j = pd.read_excel(fayl)
        st.dataframe(df_j.head())
