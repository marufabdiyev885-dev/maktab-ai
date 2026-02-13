import streamlit as st
import google.generativeai as genai
import pandas as pd
import os

# 1. Sozlamalar
API_KEY = "AIzaSyAp3ImXzlVyNF_UXjes2LsSVhG0Uusobdw"
TO_GRI_PAROL = "informatika2024"

# Google AI ni sozlash
genai.configure(api_key=API_KEY)

st.set_page_config(page_title="Maktab AI | Ko'p faylli baza", layout="centered")

# --- PAROL TEKSHIRISH ---
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

# --- BAZALARNI BIRLASHTIRISH ---
@st.cache_data # Fayllarni har safar qayta o'qib vaqt sarflamaslik uchun
def bazani_yukla():
    fayllar = [f for f in os.listdir('.') if f.endswith('.xlsx') or f.endswith('.csv')]
    umumiy_df = pd.DataFrame()
    
    if not fayllar:
        return None

    for f in fayllar:
        try:
            temp_df = pd.read_excel(f) if f.endswith('.xlsx') else pd.read_csv(f)
            umumiy_df = pd.concat([umumiy_df, temp_df], ignore_index=True)
        except Exception as e:
            st.error(f"Xatolik: {f} faylini o'qib bo'lmadi.")
    
    return umumiy_df

df = bazani_yukla()

# --- ASOSIY DASTUR ---
st.title("🏫 Maktab AI Yordamchisi")

if df is not None:
    st.success(f"✅ {len(os.listdir('.'))} ta fayl topildi va baza birlashtirildi.")
    
    savol = st.chat_input("O'quvchi, sinf yoki o'qituvchi haqida so'rang...")

    if savol:
        with st.chat_message("user"):
            st.write(savol)
        
        with st.chat_message("assistant"):
            # Modelni tanlash (eng barqaror variant)
            model = genai.GenerativeModel('gemini-1.5-flash')
            
            # Ma'lumot juda ko'p bo'lib ketmasligi uchun oxirgi 500 qatorni olamiz 
            # (AI matn limiti borligi uchun)
            context = df.to_string(index=False)
            
            with st.spinner("Barcha fayllardan qidiryapman..."):
                prompt = f"Sen maktab yordamchisisan. Quyidagi ma'lumotlar bazasi asosida savolga o'zbek tilida javob ber:\n\n{context}\n\nSavol: {savol}"
                try:
                    response = model.generate_content(prompt)
                    st.write(response.text)
                except Exception as e:
                    st.error(f"AI javob berishda xato qildi: {e}")
else:
    st.warning("⚠️ Papkada hech qanday Excel yoki CSV fayl topilmadi!")

with st.sidebar:
    st.info(f"Foydalanuvchi: Abdiyev Ma'rufjon")
    if st.button("Chiqish"):
        del st.session_state.authenticated
        st.rerun()
