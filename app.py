import streamlit as st
import google.generativeai as genai
import pandas as pd
import os

# 1. SOZLAMALAR
API_KEY = "AIzaSyAp3ImXzlVyNF_UXjes2LsSVhG0Uusobdw"
TO_GRI_PAROL = "informatika2024"

# Google AI ni sozlash (v1beta o'rniga v1 ishlatamiz)
genai.configure(api_key=API_KEY)

st.set_page_config(page_title="Maktab AI", layout="centered")

# --- PAROL TIZIMI ---
if "authenticated" not in st.session_state:
    st.title("🔐 Tizimga kirish")
    parol = st.text_input("Parolni kiriting:", type="password")
    if st.button("Kirish"):
        if parol == TO_GRI_PAROL:
            st.session_state.authenticated = True
            st.rerun()
        else:
            st.error("❌ Parol noto'g'ri!")
    st.stop()

# --- BAZANI O'QISH ---
@st.cache_data
def yuklash():
    files = [f for f in os.listdir('.') if f.endswith(('.xlsx', '.csv')) and 'app.py' not in f]
    all_data = []
    for f in files:
        try:
            if f.endswith('.csv'):
                df = pd.read_csv(f, dtype=str, encoding='utf-8')
            else:
                sheets = pd.read_excel(f, sheet_name=None, dtype=str)
                df = pd.concat(sheets.values(), ignore_index=True)
            all_data.append(df)
        except:
            continue
    return pd.concat(all_data, ignore_index=True) if all_data else None

st.title("🏫 Maktab AI Yordamchisi")
df = yuklash()

if df is not None:
    st.success(f"✅ Baza yuklandi! {len(df)} ta qator tayyor.")
    
    savol = st.chat_input("Ism yozing (Masalan: NASIMOV yoki JALILOVA)")

    if savol:
        with st.chat_message("user"):
            st.write(savol)
        
        with st.chat_message("assistant"):
            # AQLLI QIDIRUV
            mask = df.apply(lambda row: row.astype(str).str.contains(savol, case=False, na=False).any(), axis=1)
            results = df[mask].head(15)
            
            if results.empty:
                st.warning(f"'{savol}' bo'yicha ma'lumot topilmadi. Bazadagi ismlardan birini yozing.")
            else:
                context = results.to_string(index=False)
                
                # 404 XATOSINI YO'QOTISH UCHUN MODELNI TO'G'RI CHAQIRISH
                try:
                    # 'gemini-pro' har doim ishlaydi va 404 bermaydi
                    model = genai.GenerativeModel('gemini-pro')
                    
                    with st.spinner("AI javob bermoqda..."):
                        prompt = f"Sen maktab yordamchisisan. Faqat ushbu ma'lumotlar asosida javob ber:\n{context}\n\nSavol: {savol}"
                        response = model.generate_content(prompt)
                        st.write(response.text)
                except Exception as e:
                    st.error(f"Xatolik yuz berdi. API kalitda muammo bo'lishi mumkin.")
else:
    st.warning("⚠️ Fayllar topilmadi.")
