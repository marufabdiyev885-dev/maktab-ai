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
    st.success("💡 **Metodik Namuna Bo'limi**\n\nUstozlar, dars uchun tayyor ssenariylar va o'yin namunalarini so'rang!")
    st.caption("© 2024 Maktab AI Master")

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
st.title(f"🤖 AI Konsultant & Metodist")

if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "Assalomu alaykum, hurmatli foydalanuvchi! Men maktabingizning bosh metodistiman. Qanday dars ssenariysi yoki namunali metod kerak?"}]

for m in st.session_state.messages:
    with st.chat_message(m["role"]): st.markdown(m["content"])

if savol := st.chat_input("Savolingizni yoki dars mavzusini yozing..."):
    st.session_state.messages.append({"role": "user", "content": savol})
    with st.chat_message("user"): st.markdown(savol)
    
    with st.chat_message("assistant"):
        found_data = ""
        soni = 0
        skip_search = False
        
        # 🟢 FAROSAT FILTRI
        shunchaki_gap = [r"rahmat", r"ajoyib", r"yaxshi", r"zo'r", r"salom", r"assalomu alaykum"]
        if any(re.search(rf"\b{soz}\b", savol.lower()) for soz in shunchaki_gap):
            skip_search = True

        # 🔵 QIDIRUV QISMI (Jadvallar uchun)
        if df is not None and not skip_search:
            keywords = [s.lower() for s in savol.split() if len(s) > 2]
            res = df[df.apply(lambda row: any(k in str(v).lower() for k in keywords for v in row), axis=1)]
            
            if not res.empty:
                st.markdown("### 📋 Topilgan ma'lumotlar:")
                st.dataframe(res, use_container_width=True)
                soni = len(res)
                found_data = res.head(20).to_string(index=False)
                
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                    res.to_excel(writer, index=False)
                st.download_button("📥 Excelda yuklab olish", output.getvalue(), "royxat.xlsx")
                st.divider() # Jadvalni AI matnidan ajratadi

        # 🚀 3. AI KONSULTANT (NAMUNA BERUVCHI)
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
        
        system_talimoti = f"""
        Sen {MAKTAB_NOMI} maktabining BOSH METODISTI va professional pedagogik kouchisiz. 
        VAZIFANG: Faqat tavsiya berish emas, balki TAYYOR NAMUNA va SSENARIY ko'rsatish.
        
        Agar o'qituvchi metod yoki o'yin so'rasa, javobni quyidagi tuzilmada ber:
        1. 🎯 **Metod/O'yin nomi**: Qisqa va qiziqarli nom.
        2. 🛠 **Kerakli asboblar**: Darsda nima kerak bo'lishi.
        3. 📝 **Qadamba-qadam ssenariy**: O'qituvchi nima qiladi, o'quvchi nima qiladi.
        4. 💡 **Darsdan namuna**: Masalan, Informatika yoki Matematika darsida buni qanday qo'llashni aniq misol (keys) bilan tushuntir.
        
        MULOQOT: 'Hurmatli foydalanuvchi' deb boshla. O'qituvchini 'Sizdek fidoyi ustoz' deb ruhlantir. 
        Ma'lumot topilgan bo'lsa ({soni} ta), jadvalga ishora qil.
        """

        payload = {
            "model": "llama-3.3-70b-versatile",
            "messages": [
                {"role": "system", "content": system_talimoti},
                {"role": "user", "content": f"Baza: {found_data}. Savol: {savol}"}
            ],
            "temperature": 0.8
        }
        
        try:
            r = requests.post(url, json=payload, headers=headers, timeout=15)
            ai_text = r.json()['choices'][0]['message']['content']
        except:
            ai_text = "Hurmatli foydalanuvchi, ulanishda xatolik bo'ldi. Iltimos, qaytadan urinib ko'ring."

        st.info(ai_text) # AI javobi ko'k blokda, jadvaldan ajralgan holda chiqadi
        st.session_state.messages.append({"role": "assistant", "content": ai_text})
