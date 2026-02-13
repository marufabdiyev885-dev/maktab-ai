import streamlit as st
import google.generativeai as genai
import pandas as pd
import os

# 1. SOZLAMALAR
API_KEY = "AIzaSyAp3ImXzlVyNF_UXjes2LsSVhG0Uusobdw"
TO_GRI_PAROL = "informatika2024"

# Google AI ni sozlash
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

# --- MODELLARNI TEKSHIRISH (404 xatosini oldini olish) ---
@st.cache_resource
def get_working_model():
    # Google API v1 yoki v1beta versiyalarida models/ prefiksi shart
    try:
        model = genai.GenerativeModel('models/gemini-1.5-flash')
        return model
    except:
        return genai.GenerativeModel('models/gemini-pro')

# --- BAZALARNI YUKLASH (5 qatorni tashlab o'tish) ---
@st.cache_data
def bazani_yukla():
    # Papkadagi barcha Excel va CSV larni qidirish
    fayllar = [f for f in os.listdir('.') if (f.endswith('.xlsx') or f.endswith('.csv')) and 'app.py' not in f]
    if not fayllar:
        return None
    
    dfs = []
    for f in fayllar:
        try:
            # Fayllaringizda 5 ta bo'sh qator bor, shuning uchun skiprows=5
            if f.endswith('.csv'):
                temp_df = pd.read_csv(f, dtype=str, skiprows=5)
            else:
                temp_df = pd.read_excel(f, dtype=str, skiprows=5)
            
            # Keraksiz bo'sh ustunlarni tozalash
            temp_df = temp_df.loc[:, ~temp_df.columns.str.contains('^Unnamed')]
            dfs.append(temp_df)
        except:
            continue
    
    return pd.concat(dfs, ignore_index=True) if dfs else None

# --- ASOSIY QISM ---
st.title("🏫 Maktab AI Yordamchisi")
model = get_working_model()
df = bazani_yukla()

if df is not None:
    st.success(f"✅ Baza tayyor! {len(df)} ta qator yuklandi.")
    
    savol = st.chat_input("Masalan: 'Sherzodbek haqida ma'lumot' yoki '8-A sinf ro'yxati'")

    if savol:
        with st.chat_message("user"):
            st.write(savol)
        
        with st.chat_message("assistant"):
            # Bazadan qidirish (Katta-kichik harfga qaramaydi)
            mask = df.apply(lambda row: row.astype(str).str.contains(savol, case=False, na=False).any(), axis=1)
            qidirilgan_data = df[mask]
            
            if qidirilgan_data.empty:
                context_text = "Bazadan hech qanday ma'lumot topilmadi."
            else:
                # Limitdan oshmaslik uchun faqat kerakli qismni AIga beramiz
                context_text = qidirilgan_data.head(25).to_string(index=False)
            
            try:
                prompt = f"""
                Sen maktab ma'lumotlar bazasi bo'yicha yordamchisan. 
                Faqat quyidagi jadval ma'lumotlariga tayanib javob ber:
                {context_text}
                
                Savol: {savol}
                Javobni o'zbek tilida chiroyli jadval yoki ro'yxat shaklida ber.
                """
                
                with st.spinner("Qidiryapman..."):
                    response = model.generate_content(prompt)
                    st.write(response.text)
            except Exception as e:
                st.error(f"Xatolik yuz berdi: {e}")
else:
    st.warning("⚠️ Fayllar topilmadi yoki o'qishda xato. GitHub-da fayllar borligini tekshiring.")
