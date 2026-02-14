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

# --- 2. BAZANI YUKLASH (1200 TA O'QUVCHI UCHUN TO'LIQ VARIANT) ---
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
                        all_data.append(sheet_df)
                except:
                    df_html = pd.read_html(f, header=0)[0]
                    all_data.append(df_html.astype(str))
            elif f.endswith('.csv'):
                df_s = pd.read_csv(f, dtype=str)
                all_data.append(df_s)
        except: continue
    
    if all_data:
        full_df = pd.concat(all_data, ignore_index=True)
        full_df.columns = [str(c).strip().lower() for c in full_df.columns]
        for col in full_df.columns:
            full_df[col] = full_df[col].astype(str).str.strip()
        return full_df, word_text
    return None, word_text

df, maktab_doc_content = yuklash()

# --- 3. SIDEBAR VA IBRATLI SO'ZLAR ---
with st.sidebar:
    st.markdown(f"## 🏛 {MAKTAB_NOMI}")
    st.image("https://cdn-icons-png.flaticon.com/512/2859/2859706.png", width=80)
    st.divider()
    menu = st.radio("Bo'limni tanlang:", ["🤖 AI Yordamchi", "📊 Jurnal Monitoringi"])
    st.divider()
    hikmatlar = ["Ilm — saodat kalitidir.", "Informatika — kelajak tili!", "Ustoz — otangdek ulug‘!"]
    st.warning(f"🌟 **Kun hikmati:**\n\n*{random.choice(hikmatlar)}*")
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

# --- 5. SAHIFALAR ---
if menu == "🤖 AI Yordamchi":
    st.title(f"🤖 {MAKTAB_NOMI} AI Yordamchisi")
    if "messages" not in st.session_state:
        st.session_state.messages = [{"role": "assistant", "content": "Assalomu alaykum! Maktab bazasi bo'yicha qanday yordam bera olaman?"}]
    for m in st.session_state.messages:
        with st.chat_message(m["role"]): st.markdown(m["content"])

    if savol := st.chat_input("Savolingizni yozing..."):
        st.session_state.messages.append({"role": "user", "content": savol})
        with st.chat_message("user"): st.markdown(savol)
        
        with st.chat_message("assistant"):
            found_data = ""
            soni = 0
            shunchaki_gap = [r"rahmat", r"ajoyib", r"yaxshi", r"zo'r", r"salom", r"assalomu alaykum", r"baraka toping"]
            is_greeting = any(re.search(rf"\b{soz}\b", savol.lower()) for soz in shunchaki_gap)

            if df is not None and not is_greeting:
                keywords = [s.lower() for s in savol.split() if len(s) > 2]
                if keywords:
                    res = df[df.apply(lambda row: any(k in str(v).lower() for k in keywords for v in row), axis=1)]
                    if not res.empty:
                        st.dataframe(res, use_container_width=True)
                        soni = len(res)
                        found_data = res.head(50).to_string(index=False)
                        output = io.BytesIO()
                        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                            res.to_excel(writer, index=False)
                        st.download_button(label=f"📥 {soni} ta natijani yuklab olish", data=output.getvalue(), file_name="natija.xlsx")

            payload = {
                "model": "llama-3.3-70b-versatile",
                "messages": [
                    {"role": "system", "content": f"Sen {MAKTAB_NOMI} AI yordamchisisan. Jami ma'lumot: {len(df) if df is not None else 0}. O'zbekona lutf bilan javob ber."},
                    {"role": "user", "content": f"Baza: {found_data}. Savol: {savol}"}
                ], "temperature": 0.5
            }
            try:
                r = requests.post("https://api.groq.com/openai/v1/chat/completions", json=payload, headers={"Authorization": f"Bearer {GROQ_API_KEY}"})
                ai_text = r.json()['choices'][0]['message']['content']
            except: ai_text = "Yordam berishdan hamisha xursandman!"
            st.markdown(ai_text)
            st.session_state.messages.append({"role": "assistant", "content": ai_text})

# --- 6. JURNAL MONITORINGI (TELEGRAM BILAN) ---
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
            
            if st.button("📢 Telegramga hisobot yuborish"):
                def tahlil(val):
                    s = str(val).lower()
                    if "undan" in s:
                        nums = re.findall(r'\d+', s)
                        if len(nums) >= 2: return int(nums[1]) < int(nums[0])
                    return False

                df_filtir = df_j[df_j[c_oqit].notna() & ~df_j[c_oqit].str.contains('maktab|tuman', case=False, na=False)]
                xatolar = df_filtir[df_filtir[c_baho].apply(tahlil)]
                
                if not xatolar.empty:
                    text = f"<b>⚠️ JURNAL MONITORINGI</b>\n<i>{MAKTAB_NOMI}</i>\n\n"
                    for _, r in xatolar.iterrows():
                        text += f"❌ <b>{r[c_oqit]}</b> -> {r[c_baho]}\n"
                else:
                    text = f"<b>✅ JURNAL MONITORINGI</b>\n<i>{MAKTAB_NOMI}</i>\n\n✨ Hamma jurnallar baholangan!"

                # TELEGRAMGA YUBORISH
                requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", 
                              json={"chat_id": GURUH_ID, "text": text, "parse_mode": "HTML"})
                st.success("Hisobot Telegramga yuborildi!")
        except Exception as e: st.error(f"Xato: {e}")
