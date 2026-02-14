import streamlit as st
import pandas as pd
import os
import requests
import re
import io
import docx
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

# --- 2. BAZANI YUKLASH ---
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
            elif f.endswith(('.xlsx', '.xls')):
                try:
                    excel_sheets = pd.read_excel(f, sheet_name=None, dtype=str)
                    for name, sheet_df in excel_sheets.items():
                        if not sheet_df.empty:
                            all_data.append(sheet_df)
                except:
                    df_html_list = pd.read_html(f)
                    if df_html_list:
                        all_data.append(df_html_list[0].astype(str))
            elif f.endswith('.csv'):
                df_s = pd.read_csv(f, dtype=str)
                if not df_s.empty:
                    all_data.append(df_s)
        except: continue
    
    if all_data:
        full_df = pd.concat(all_data, ignore_index=True)
        # Ustun nomlarini tozalash
        full_df.columns = [str(c).strip().lower() for c in full_df.columns]
        
        # Takrorlangan ustunlarni raqamlash
        cols = pd.Series(full_df.columns)
        for i, col in enumerate(cols):
            count = cols[:i].tolist().count(col)
            if count > 0:
                cols[i] = f"{col}.{count}"
        full_df.columns = cols
        
        full_df = full_df.applymap(lambda x: str(x).strip() if pd.notnull(x) else "")
        return full_df, word_text
    return None, word_text

df_baza, maktab_doc_content = yuklash()

# --- 3. SIDEBAR ---
with st.sidebar:
    st.markdown(f"## 🏛 {MAKTAB_NOMI}")
    st.image("https://cdn-icons-png.flaticon.com/512/2859/2859706.png", width=80)
    st.divider()
    menu = st.radio("Bo'limni tanlang:", ["🤖 AI Yordamchi", "📊 Jurnal Monitoringi"])
    st.divider()
    st.info(f"**Direktor:**\n\n{DIREKTOR_FIO}")

# --- 4. XAVFSIZLIK ---
if "authenticated" not in st.session_state:
    st.title(f"🏫 {MAKTAB_NOMI} | Tizim")
    parol = st.text_input("Parolni kiriting:", type="password")
    if st.button("Kirish"):
        if parol == TO_GRI_PAROL:
            st.session_state.authenticated = True
            st.rerun()
        else: st.error("❌ Xato!")
    st.stop()

# --- 5. AI YORDAMCHI (ANIQ FILTR BILAN) ---
if menu == "🤖 AI Yordamchi":
    st.title(f"🤖 {MAKTAB_NOMI} AI Yordamchisi")
    if "messages" not in st.session_state:
        st.session_state.messages = [{"role": "assistant", "content": "Assalomu alaykum! O'qituvchilar yoki o'quvchilar ro'yxati kerakmi?"}]
    
    for m in st.session_state.messages:
        with st.chat_message(m["role"]): st.markdown(m["content"])

    if savol := st.chat_input("Savolingizni yozing..."):
        st.session_state.messages.append({"role": "user", "content": savol})
        with st.chat_message("user"): st.markdown(savol)
        
        with st.chat_message("assistant"):
            found_data = ""
            soni = 0
            
            if df_baza is not None:
                qidiruv_sozlari = [s.lower() for s in savol.split() if len(s) > 2]
                
                # Savol mazmunini aniqlash
                is_teacher_req = any(x in savol.lower() for x in ["o'qituvchi", "pedagog", "xodim", "toifasi", "ustoz"])
                is_student_req = any(x in savol.lower() for x in ["o'quvchi", "sinf", "bola"])

                temp_df = df_baza.copy()

                # --- ANIQ FILTRLASH ---
                # Agar o'qituvchi so'ralsa, faqat "mutaxassisligi" bor qatorlarni qoldiramiz
                if is_teacher_req:
                    for col in ["mutaxassisligi", "toifasi", "pedagogning ismi familiyasi"]:
                        if col in temp_df.columns:
                            temp_df = temp_df[temp_df[col] != ""]

                if qidiruv_sozlari:
                    # Qidiruv so'zi qaysi ustunda bo'lishidan qat'i nazar topadi
                    res = temp_df[temp_df.apply(lambda row: any(k in str(v).lower() for k in qidiruv_sozlari for v in row), axis=1)]
                    
                    if not res.empty:
                        st.dataframe(res, use_container_width=True)
                        soni = len(res)
                        found_data = res.head(40).to_string(index=False)
                        
                        output = io.BytesIO()
                        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                            res.to_excel(writer, index=False)
                        st.download_button(label=f"📥 {soni} ta natijani yuklab olish", data=output.getvalue(), file_name="royxat.xlsx")
            
            # AI JAVOBI
            payload = {
                "model": "llama-3.3-70b-versatile",
                "messages": [
                    {"role": "system", "content": f"Sen {MAKTAB_NOMI} yordamchisisan. Jami ma'lumot: {len(df_baza)}. Faqat bazadagi aniq ma'lumotga tayan."},
                    {"role": "user", "content": f"Baza: {found_data}. Savol: {savol}"}
                ], "temperature": 0.2
            }
            try:
                r = requests.post("https://api.groq.com/openai/v1/chat/completions", json=payload, headers={"Authorization": f"Bearer {GROQ_API_KEY}"})
                ai_text = r.json()['choices'][0]['message']['content']
            except: ai_text = "Natijalarni yuqoridagi jadvalda ko'rishingiz mumkin."
            
            st.markdown(ai_text)
            st.session_state.messages.append({"role": "assistant", "content": ai_text})

# --- 6. MONITORING ---
elif menu == "📊 Jurnal Monitoringi":
    st.title("📊 Jurnal Monitoringi")
    # ... (monitoring kodi)
