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

# --- 2. BAZANI YUKLASH (XATOLIKLARSIZ) ---
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
        # Ustun nomlaridagi duplikatlarni yo'qotish
        cols = pd.Series(full_df.columns).astype(str).str.strip().str.lower()
        for i, col in enumerate(cols):
            count = cols[:i].tolist().count(col)
            if count > 0:
                cols[i] = f"{col}.{count}"
        full_df.columns = cols
        # Ma'lumotlarni tozalash
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

# --- 4. XAVFSIZLIK (TO'G'IRLANGAN) ---
if "authenticated" not in st.session_state:
    st.title(f"🏫 {MAKTAB_NOMI} | Tizim")
    parol = st.text_input("Parolni kiriting:", type="password")
    if st.button("Kirish"):
        if parol == TO_GRI_PAROL:  # Bu yerda harf xatosi tuzatildi
            st.session_state.authenticated = True
            st.rerun()
        else: st.error("❌ Xato!")
    st.stop()

# --- 5. AI YORDAMCHI (ANIK QIDIRUV) ---
if menu == "🤖 AI Yordamchi":
    st.title(f"🤖 {MAKTAB_NOMI} AI Yordamchisi")
    if "messages" not in st.session_state:
        st.session_state.messages = [{"role": "assistant", "content": "Assalomu alaykum! Kimni qidiramiz (masalan: o'qituvchi Sobir)?"}]
    
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
                
                # O'qituvchi/O'quvchi ajratish mantiqi
                is_teacher_req = any(x in savol.lower() for x in ["o'qituvchi", "ustoz", "muallim", "xodim"])
                is_student_req = any(x in savol.lower() for x in ["o'quvchi", "bola", "shogird"])

                temp_df = df_baza.copy()

                # Agar o'qituvchi so'ralsa, "sinfi" ustunida ma'lumot yo'qlarini qidiramiz
                if is_teacher_req and "sinfi" in temp_df.columns:
                    temp_df = temp_df[temp_df["sinfi"] == ""]
                
                # Agar o'quvchi so'ralsa, "sinfi" ustunida ma'lumot borlarini qidiramiz
                if is_student_req and "sinfi" in temp_df.columns:
                    temp_df = temp_df[temp_df["sinfi"] != ""]

                if qidiruv_sozlari:
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
                    {"role": "system", "content": f"Sen {MAKTAB_NOMI} yordamchisisan. Jami baza: {len(df_baza) if df_baza is not None else 0}. Topilgan natijalar: {soni} ta."},
                    {"role": "user", "content": f"Baza: {found_data}. Savol: {savol}"}
                ], "temperature": 0.3
            }
            try:
                r = requests.post("https://api.groq.com/openai/v1/chat/completions", json=payload, headers={"Authorization": f"Bearer {GROQ_API_KEY}"})
                ai_text = r.json()['choices'][0]['message']['content']
            except: ai_text = "Natijalar jadvalda ko'rsatildi."
            
            st.markdown(ai_text)
            st.session_state.messages.append({"role": "assistant", "content": ai_text})

# --- 6. MONITORING (TELEGRAM BILAN) ---
elif menu == "📊 Jurnal Monitoringi":
    st.title("📊 Jurnal Monitoringi")
    if "m_auth" not in st.session_state: st.session_state.m_auth = False
    if not st.session_state.m_auth:
        m_pass = st.text_input("Monitoring kodi:", type="password")
        if st.button("Kirish"):
            if m_pass == MONITORING_KODI:
                st.session_state.m_auth = True
                st.rerun()
            else: st.error("❌ Xato!")
        st.stop()

    j_fayl = st.file_uploader("eMaktab faylini yuklang", type=['xlsx', 'xls'])
    if j_fayl:
        try:
            try: df_j = pd.read_excel(j_fayl, header=[0, 1]) 
            except:
                j_fayl.seek(0)
                df_j = pd.read_html(j_fayl, header=0)[0]

            df_j.columns = [' '.join([str(i) for i in col]).strip() if isinstance(col, tuple) else str(col) for col in df_j.columns]
            df_j.columns = [re.sub(r'Unnamed: \d+_level_\d+', '', c).strip() for c in df_j.columns]
            
            st.write("📊 Jadval namunasi:")
            st.dataframe(df_j.head())
            
            c_oqit = st.selectbox("O'qituvchi ustunini tanlang:", df_j.columns)
            c_baho = st.selectbox("Baho ustunini tanlang:", df_j.columns)
            
            if st.button("📢 Telegramga yuborish"):
                def tahlil(val):
                    s = str(val).lower()
                    if "undan" in s:
                        nums = re.findall(r'\d+', s)
                        if len(nums) >= 2: return int(nums[1]) < int(nums[0])
                    return False

                df_filtir = df_j[df_j[c_oqit].notna()]
                xatolar = df_filtir[df_filtir[c_baho].apply(tahlil)]
                
                text = f"<b>📊 {MAKTAB_NOMI}</b>\n\n"
                if not xatolar.empty:
                    for _, r in xatolar.iterrows():
                        text += f"❌ <b>{r[c_oqit]}</b> -> {r[c_baho]}\n"
                else: text += "✅ Hamma jurnallar to'liq!"

                requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", 
                             json={"chat_id": GURUH_ID, "text": text, "parse_mode": "HTML"})
                st.success("Telegramga yuborildi!")
        except Exception as e: st.error(f"Xato: {e}")
