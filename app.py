import streamlit as st
import google.generativeai as genai
import pandas as pd
import os

# 1. SOZLAMALAR
API_KEY = "AIzaSyAp3ImXzlVyNF_UXjes2LsSVhG0Uusobdw"
TO_GRI_PAROL = "informatika2024"

genai.configure(api_key=API_KEY)

st.set_page_config(page_title="Maktab AI | Abdiyev Ma'rufjon", layout="centered")

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

# --- ISHLAYDIGAN MODELNI ANIQLASH ---
@st.cache_resource
def get_working_model():
    try:
        available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        priorities = ['models/gemini-1.5-flash', 'models/gemini-pro']
        for model_path in priorities:
            if model_path in available_models:
                return model_path
        return "models/gemini-pro"
    except:
        return "models/gemini-pro"

# --- BAZALARNI YUKLASH (5-qatorni tashlab o'tish bilan) ---
@st.cache_data
def bazani_yukla():
    # Fayl nomlarini tekshirish (GitHub yuklaganda nomlar o'zgarishi mumkin)
    fayllar = [f for f in os.listdir('.') if (f.endswith('.xlsx') or f.endswith('.csv')) and 'app.py' not in f]
    if not fayllar:
        return None
    
    dfs = []
    for f in fayllar:
        try:
            # Fayl turiga qarab o'qiymiz va tepadagi 5 ta bo'sh qatorni tashlab ketamiz
            if f.endswith('.csv'):
                temp_df = pd.read_csv(f, dtype=str, skiprows=5)
            else:
                temp_df = pd.read_excel(f, dtype=str, skiprows=5)
            
            # Bo'sh qolgan ustunlarni o'chirish
            temp_df = temp_df.loc[:, ~temp_df.columns.str.contains('^Unnamed')]
            dfs.append(temp_df)
        except Exception as e:
            continue
    
    if dfs:
        return pd.concat(dfs, ignore_index=True)
    return None

# --- ASOSIY QISM ---
st.title("🏫 Maktab AI Yordamchisi")
working_model_name = get_working_model()
df = bazani_yukla()

if df is not None:
    # Ma'lumotlar borligini tekshirish
    st.success(f"✅ Baza tayyor! {len(df)} ta qator topildi.")
    
    savol = st.chat_input("Ism, familiya yoki sinf bo'yicha so'rang...")

    if savol:
        with st.chat_message("user"):
            st.write(savol)
        
        with st.chat_message("assistant"):
            # Savolni qidirish
            mask = df.apply(lambda row: row.astype(str).str.contains(savol, case=False, na=False).any(), axis=1)
            qidirilgan_data = df[mask]
            
            if qidirilgan_data.empty:
                context_text = "Bazadan ushbu so'rov bo'yicha ma'lumot topilmadi."
            else:
                context_text = qidirilgan_data.head(30).to_string(index=False)
            
            try:
                model = genai.GenerativeModel(working_model_name)
                prompt = f"""
                Sen maktab yordamchi botisan. Quyidagi bazaga tayanib savolga javob ber.
                Ma'lumotlar:
                {context_text}
                
                Savol: {savol}
                Javobni o'zbek tilida, tushunarli qilib ber.
                """
                
                with st.spinner("Qidiryapman..."):
                    response = model.generate_content(prompt)
                    st.write(response.text)
            except Exception as e:
                st.error(f"Xatolik: {e}")
else:
    st.warning("⚠️ Fayllar o'qilmadi. GitHub-da fayllar borligini tekshiring.")
