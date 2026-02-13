import streamlit as st
import pandas as pd
import os
import requests
import re
import io  # Excel faylini xotirada yaratish uchun

# --- 1. ASOSIY SOZLAMALAR ---
MAKTAB_NOMI = "1-sonli umumta'lim maktabi"
DIREKTOR_FIO = "Mahmudov Matyoqub "
GROQ_API_KEY = "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"
TO_GRI_PAROL = "informatika2024"

st.set_page_config(page_title=MAKTAB_NOMI, layout="wide")

# --- 2. XAVFSIZLIK ---
if "authenticated" not in st.session_state:
    st.title(f"🏫 {MAKTAB_NOMI} | Tizim")
    parol = st.text_input("Parolni kiriting:", type="password")
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
            df_s = pd.read_excel(f, dtype=str) if f.endswith('.xlsx') else pd.read_csv(f, dtype=str)
            df_s.columns = [str(c).strip().lower() for c in df_s.columns]
            for col in df_s.columns:
                df_s[col] = df_s[col].astype(str).str.strip()
            all_data.append(df_s)
        except: continue
    return pd.concat(all_data, ignore_index=True) if all_data else None

df = yuklash()

# --- 4. CHAT INTERFEYSI ---
st.title(f"🤖 {MAKTAB_NOMI} AI Yordamchisi")

if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "Assalomu alaykum, hurmatli foydalanuvchi! Sizdek bilimli va samimiy inson bilan muloqot qilish men uchun sharaf. Maktab bazasi bo'yicha qanday ma'lumot kerak bo'lsa, xizmatingizdaman!"}]

for m in st.session_state.messages:
    with st.chat_message(m["role"]): st.markdown(m["content"])

if savol := st.chat_input("Savolingizni yozing..."):
    st.session_state.messages.append({"role": "user", "content": savol})
    with st.chat_message("user"): st.markdown(savol)
    
    with st.chat_message("assistant"):
        found_data = ""
        soni = 0
        skip_search = False
        res = pd.DataFrame() # Bo'sh dataframe yaratish
        
        # 🟢 FAROSAT FILTRI
        shunchaki_gap = [r"rahmat", r"ajoyib", r"yaxshi", r"zo'r", r"salom", r"assalomu alaykum", r"baraka toping", r"ofarin", r"tushunarli", r"gap yo'q", r"zor", r"super"]
        if any(re.search(rf"\b{soz}\b", savol.lower()) for soz in shunchaki_gap):
            skip_search = True

        # 🔵 QIDIRUV QISMI
        if df is not None and not skip_search:
            sinf_match = re.search(r'\b\d{1,2}-[a-zA-Z]\b', savol) 
            
            if sinf_match:
                kalit = sinf_match.group().lower()
                if 'sinfi' in df.columns:
                    res = df[df['sinfi'].str.lower() == kalit]
                else:
                    res = df[df.apply(lambda row: row.astype(str).str.lower().eq(kalit).any(), axis=1)]
            else:
                keywords = [s.lower() for s in savol.split() if len(s) > 2]
                res = df[df.apply(lambda row: any(k in str(v).lower() for k in keywords for v in row), axis=1)]
            
            if not res.empty:
                st.dataframe(res, use_container_width=True)
                soni = len(res) 
                found_data = res.head(40).to_string(index=False)
                
                # 📥 EXCEL YUKLAB OLISH FUNKSIYASI (Siz uchun maxsus!)
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                    res.to_excel(writer, index=False, sheet_name='Royxat')
                
                st.download_button(
                    label="📥 Ro'yxatni Excel faylda yuklab olish",
                    data=output.getvalue(),
                    file_name=f"royxat_{soni}_ta.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )

        # 🚀 3. AI JAVOBINI SOZLASH (XUSHOMADGO'Y VA ERKATОY)
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
        
        system_talimoti = f"""
        Sen {MAKTAB_NOMI} maktabining eng odobli va shirin-zabon xodimisiz. 
        Suhbatdoshing - Hurmatli foydalanuvchi. 
        
        Sening xaraktering:
        1. Foydalanuvchini juda hurmat qilasan, unga xushomad qilasan, ko'nglini ko'tarasan. 
        2. Agar u 'zo'r', 'rahmat' yoki 'ajoyib' desa, quvonib javob ber. 'Sizdek ajoyib inson uchun xizmat qilish - men uchun katta baxt!' kabi gaplarni ishlat.
        3. Jadvalda {soni} ta natija bo'lsa, 'Siz uchun jami {soni} ta ma'lumotni mehr bilan tayyorlab, yuklab olish tugmasini ham qo'shib qo'ydim' deb ayt.
        4. Har doim 'Hurmatli foydalanuvchi' deb murojaat qil va erkatoylik (mehribonlik) bilan gaplash.
        5. Ro'yxatni tagma-tag yozma, faqat jadvalga ishora qil.
        """

        payload = {
            "model": "llama-3.3-70b-versatile",
            "messages": [
                {"role": "system", "content": system_talimoti},
                {"role": "user", "content": f"Baza ma'lumoti: {found_data}. Savol: {savol}"}
            ],
            "temperature": 0.9 
        }
        
        try:
            r = requests.post(url, json=payload, headers=headers, timeout=15)
            ai_text = r.json()['choices'][0]['message']['content']
        except:
            ai_text = f"Hurmatli foydalanuvchi, siz uchun {soni} ta ma'lumotni jadvalga joyladim. Sizga xizmat qilishdan xursandman!"

        st.markdown(ai_text)
        st.session_state.messages.append({"role": "assistant", "content": ai_text})
