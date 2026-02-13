import streamlit as st
import google.generativeai as genai
import pandas as pd
import os

# 1. Sozlamalar
API_KEY = "AIzaSyAp3ImXzlVyNF_UXjes2LsSVhG0Uusobdw"
TO_GRI_PAROL = "informatika2024"

# Google AI ni sozlash
genai.configure(api_key=API_KEY)

st.set_page_config(page_title="Maktab AI | Abdiyev Ma'rufjon", layout="centered")

# --- PAROL TEKSHIRISH ---
if "authenticated" not in st.session_state:
    st.title("🔐 Kirish")
    parol = st.text_input("Parolni kiriting:", type="password")
    if st.button("Kirish"):
        if parol == TO_GRI_PAROL:
            st.session_state.authenticated = True
            st.rerun()
        else:
            st.error("❌ Parol noto'g'ri!")
    st.stop()

# --- BAZALARNI BIRLASHTIRISH ---
def bazani_yukla():
    # Papkadagi barcha Excel fayllarni qidiradi
    fayllar = [f for f in os.listdir('.') if f.endswith('.xlsx')]
    umumiy_df = pd.DataFrame()
    
    if not fayllar:
        return None

    for f in fayllar:
        try:
            temp_df = pd.read_excel(f)
            umumiy_df = pd.concat([umumiy_df, temp_df], ignore_index=True)
        except:
            continue
    return umumiy_df

# --- ASOSIY DASTUR ---
st.title("🏫 Maktab AI Yordamchisi")

df = bazani_yukla()

if df is not None:
    st.success(f"✅ {len(os.listdir('.')) - 2} ta ma'lumotlar bazasi birlashtirildi.")
    
    savol = st.chat_input("O'quvchilar yoki o'qituvchilar haqida so'rang...")

    if savol:
        with st.chat_message("user"):
            st.write(savol)
        
        with st.chat_message("assistant"):
            model = genai.GenerativeModel('gemini-1.5-flash')
            # Jadvalni matnga aylantirish (limitdan oshmaslik uchun oxirgi qismini olamiz)
            context = df.to_string(index=False)
            
            with st.spinner("Barcha fayllardan javob qidiryapman..."):
                prompt = f"Sen maktab yordamchisisan. Quyidagi jadval ma'lumotlari asosida savolga o'zbek tilida javob ber:\n\n{context}\n\nSavol: {savol}"
                try:
                    response = model.generate_content(prompt)
                    st.write(response.text)
                except Exception as e:
                    st.error(f"Xatolik: {e}")
else:
    st.warning("⚠️ Excel fayllar topilmadi! Iltimos, GitHub'ga .xlsx fayllarni yuklang.")
