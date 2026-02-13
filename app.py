import streamlit as st
import pandas as pd
import os
import requests
import re
import io
import docx  # Word fayllari uchun

# --- 1. ASOSIY SOZLAMALAR ---
MAKTAB_NOMI = "1-sonli umumta'lim maktabi"
DIREKTOR_FIO = "Mahmudov Matyoqub Narzulloyevich"
GROQ_API_KEY = "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"
TO_GRI_PAROL = "informatika2024"

st.set_page_config(page_title=MAKTAB_NOMI, layout="wide")

# --- 2. RAHBARIYAT VA KONSULTANT PANELI (SIDEBAR) ---
with st.sidebar:
    st.markdown(f"## 🏛 {MAKTAB_NOMI}")
    st.image("https://cdn-icons-png.flaticon.com/512/2859/2859706.png", width=80)
    
    st.divider()
    st.subheader("👨‍🏫 Rahbariyat")
    st.info(f"**Direktor:**\n\n{DIREKTOR_FIO}")
    
    with st.expander("O'rinbosarlar ro'yxati"):
        orinbosarlar = [
            "Aslonova Ruxsora Xikmatovna",
            "Omonova Shaxnoza Panjiyevna",
            "Ro'zieva Mastura G'ulomovna",
            "Tosheva Lobar Sayfullayevna",
            "Sharopova Firuza Djalolovna"
        ]
        for ism in orinbosarlar:
            st.write(f"🔹 {ism}")
    
    st.divider()
    st.success("💡 **AI Konsultant Bo'limi**\n\nUstozlar, darsni qiziqarli o'tish, yangi metodlar va o'yinlar haqida so'rang!")
    st.caption("© 2024 Maktab AI Konsultant")

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

# --- 4. BAZANI YUKLASH (EXCEL + WORD) ---
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
                for col in df_s.columns:
                    df_s[col] = df_s[col].astype(str).str.strip()
                all_data.append(df_s)
        except: continue
    return (pd.concat(all_data, ignore_index=True) if all_data else None), word_text

df, maktab_doc_content = yuklash()

# --- 5. CHAT INTERFEYSI ---
st.title(f"🤖 AI Konsultant & Yordamchi")

if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "Assalomu alaykum, hurmatli foydalanuvchi! Sizdek fidoyi inson bilan suhbatlashish men uchun sharaf. Maktab bazasi yoki dars metodikasi bo'yicha qanday yordam kerak?"}]

for m in st.session_state.messages:
    with st.chat_message(m["role"]): st.markdown(m["content"])

if savol := st.chat_input("Savolingizni yoki metodik ehtiyojingizni yozing..."):
    st.session_state.messages.append({"role": "user", "content": savol})
    with st.chat_message("user"): st.markdown(savol)
    
    with st.chat_message("assistant"):
        found_data = ""
        soni = 0
        skip_search = False
        res = pd.DataFrame()
        
        # 🟢 FAROSAT FILTRI
        shunchaki_gap = [r"rahmat", r"ajoyib", r"yaxshi", r"zo'r", r"salom", r"assalomu alaykum", r"baraka toping", r"ofarin"]
        if any(re.search(rf"\b{soz}\b", savol.lower()) for soz in shunchaki_gap):
            skip_search = True

        # 🔵 QIDIRUV QISMI
        if df is not None and not skip_search:
            sinf_match = re.search(r'\b\d{1,2}-[a-zA-Z]\b', savol) 
            if sinf_match:
                kalit = sinf_match.group().lower()
                res = df[df['sinfi'].str.lower() == kalit] if 'sinfi' in df.columns else df[df.apply(lambda r: r.astype(str).str.lower().eq(kalit).any(), axis=1)]
            else:
                keywords = [s.lower() for s in savol.split() if len(s) > 2]
                res = df[df.apply(lambda row: any(k in str(v).lower() for k in keywords for v in row), axis=1)]
            
            if not res.empty:
                st.dataframe(res, use_container_width=True)
                soni = len(res) 
                found_data = res.head(30).to_string(index=False)
                
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                    res.to_excel(writer, index=False, sheet_name='Royxat')
                
                st.download_button(
                    label="📥 Ro'yxatni Excelda yuklab olish",
                    data=output.getvalue(),
                    file_name=f"royxat_{soni}_ta.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )

        # 🚀 3. AI KONSULTANT JAVOBINI SOZLASH
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
        
        system_talimoti = f"""
        Sen {MAKTAB_NOMI} maktabining BOSH KONSULTANTI va METODISTISIZ. 
        Suhbatdoshing - Hurmatli foydalanuvchi (asosan o'qituvchilar). 
        
        SENING YANGI VAZIFALARING:
        1. O'qituvchilarga darslarni qiziqarli o'tish, yangi metodikalar va interaktiv o'yinlar bo'yicha professional maslahat ber.
        2. Agar o'qituvchi "darsni qanday qiziqarli o'tsam bo'ladi?" deb so'rasa, unga 3 ta aniq metod tavsiya qil.
        3. Maktab hujjatlari (Word'dan olingan): {maktab_doc_content[:1000]}
        4. O'qituvchilarni doim rag'batlantir, ularga "Sizdek fidoyi ustoz" deb murojaat qil.
        5. Har doim 'Hurmatli foydalanuvchi' deb gap boshla.
        """

        payload = {
            "model": "llama-3.3-70b-versatile",
            "messages": [
                {"role": "system", "content": system_talimoti},
                {"role": "user", "content": f"Baza ma'lumoti: {found_data}. Savol: {savol}"}
            ],
            "temperature": 0.8 
        }
        
        try:
            r = requests.post(url, json=payload, headers=headers, timeout=15)
            ai_text = r.json()['choices'][0]['message']['content']
        except:
            ai_text = f"Hurmatli foydalanuvchi, siz uchun ma'lumotlarni tayyorladim. Sizga xizmat qilishdan mamnunman!"

        st.markdown(ai_text)
        st.session_state.messages.append({"role": "assistant", "content": ai_text})
