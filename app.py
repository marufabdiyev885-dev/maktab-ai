import streamlit as st
import google.generativeai as genai
import pandas as pd
import os

# 1. Sozlamalar
API_KEY = "AIzaSyAp3ImXzlVyNF_UXjes2LsSVhG0Uusobdw"
TO_GRI_PAROL = "informatika2024"

genai.configure(api_key=API_KEY)

st.set_page_config(page_title="Maktab AI | Abdiyev Ma'rufjon", layout="centered")

# --- PAROL ---
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

# --- MODELLARNI TEKSHIRISH ---
@st.cache_resource
def get_working_model():
    try:
        models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        priorities = ['models/gemini-1.5-flash', 'models/gemini-pro']
        for m in priorities:
            if m in models: return m
        return models[0] if models else None
    except:
        return "models/gemini-1.5-flash"

# --- BAZALARNI O'QISH ---
def bazani_yukla():
    fayllar = [f for f in os.listdir('.') if f.endswith('.xlsx')]
    if not fayllar: return None
    
    dfs = []
    for f in fayllar:
        try:
            temp_df = pd.read_excel(f)
            # Har bir qatorni matnga aylantirib, qaysi fayldanligini belgilaymiz
            temp_df['manba_fayl'] = f
            dfs.append(temp_df)
        except: continue
    return pd.concat(dfs, ignore_index=True) if dfs else None

# --- ASOSIY ---
st.title("🏫 Maktab AI Yordamchisi")
working_model = get_working_model()
df = bazani_yukla()

if df is not None:
    st.success(f"✅ {len(os.listdir('.')) - 2} ta fayl yuklangan.")
    
    savol = st.chat_input("Ism yoki sinfni yozing...")

    if savol:
        with st.chat_message("user"):
            st.write(savol)
        
        with st.chat_message("assistant"):
            # --- FILTRLASH (Limitdan oshmaslik uchun) ---
            # Savoldagi so'zlar qaysi qatorda qatnashganini qidiramiz
            mask = df.astype(str).apply(lambda x: x.str.contains(savol, case=False, na=False)).any(axis=1)
            qidirilgan_data = df[mask]
            
            # Agar topilmasa, bazaning bir qismini ko'rsatamiz
            if qidirilgan_data.empty:
                context = "Hech qanday ma'lumot topilmadi."
            else:
                # Faqat topilgan qatorlarni (max 50 ta) AIga yuboramiz
                context = qidirilgan_data.head(50).to_string(index=False)
            
            try:
                model = genai.GenerativeModel(working_model)
                prompt = f"Maktab bazasidan olingan ma'lumotlar:\n{context}\n\nSavol: {savol}\n\nJavobni o'zbek tilida ber."
                
                with st.spinner("Qidiryapman..."):
                    response = model.generate_content(prompt)
                    st.write(response.text)
            except Exception as e:
                if "429" in str(e):
                    st.error("⏳ Google biroz charchadi (Limit). 30 soniya kutib qayta urining.")
                else:
                    st.error(f"Xato: {e}")
else:
    st.warning("⚠️ Excel fayllar topilmadi.")
