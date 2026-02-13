import streamlit as st
import google.generativeai as genai
import pandas as pd
import os

# 1. API va Parol sozlamalari
API_KEY = "AIzaSyAp3ImXzlVyNF_UXjes2LsSVhG0Uusobdw"
TO_GRI_PAROL = "informatika2024"

# Google AI-ni sozlash
genai.configure(api_key=API_KEY)

st.set_page_config(page_title="Maktab AI | Abdiyev Ma'rufjon", layout="centered")

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

# --- ISHLAYDIGAN MODELNI ANIQLASH ---
@st.cache_resource
def get_working_model():
    # 404 xatosini oldini olish uchun mavjud modellarni tekshiramiz
    available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
    
    # Eng yaxshi modellarni navbati bilan tanlaymiz
    priorities = ['models/gemini-1.5-flash', 'models/gemini-1.5-flash-8b', 'models/gemini-pro']
    
    for model_path in priorities:
        if model_path in available_models:
            return model_path
    
    # Agar ro'yxatdagilar topilmasa, birinchi kelganini olamiz
    return available_models[0] if available_models else None

# --- BAZALARNI BIRLASHTIRISH ---
def bazani_yukla():
    fayllar = [f for f in os.listdir('.') if f.endswith('.xlsx')]
    if not fayllar:
        return None
    
    list_of_dfs = []
    for f in fayllar:
        try:
            temp_df = pd.read_excel(f)
            list_of_dfs.append(temp_df)
        except:
            continue
    
    return pd.concat(list_of_dfs, ignore_index=True) if list_of_dfs else None

# --- ASOSIY QISM ---
st.title("🏫 Maktab AI Yordamchisi")

working_model_name = get_working_model()
df = bazani_yukla()

if df is not None and working_model_name:
    st.success(f"✅ Baza tayyor. Model: {working_model_name}")
    
    savol = st.chat_input("O'quvchi yoki ma'lumotlar haqida so'rang...")

    if savol:
        with st.chat_message("user"):
            st.write(savol)
        
        with st.chat_message("assistant"):
            model = genai.GenerativeModel(working_model_name)
            # Ma'lumotlar juda ko'p bo'lsa, AI-ga faqat matnli qismini beramiz
            context = df.to_string(index=False)
            
            prompt = f"""
            Sen maktab yordamchisi - botisan. 
            Quyidagi jadval ma'lumotlari asosida foydalanuvchining savoliga o'zbek tilida aniq javob ber.
            
            Ma'lumotlar:
            {context}
            
            Savol: {savol}
            """
            
            with st.spinner("Qidiryapman..."):
                try:
                    response = model.generate_content(prompt)
                    st.write(response.text)
                except Exception as e:
                    st.error(f"AI javob berishda xato qildi: {e}")
elif not working_model_name:
    st.error("❌ API kalitda hech qanday model topilmadi. API kalitni tekshiring.")
else:
    st.warning("⚠️ Excel fayllar topilmadi. GitHub'ga .xlsx fayllarni yuklang.")

with st.sidebar:
    st.write(f"**Admin:** Ma'rufjon Abdiyev")
    if st.button("Chiqish"):
        del st.session_state.authenticated
        st.rerun()
