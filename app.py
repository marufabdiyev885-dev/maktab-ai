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

# --- BAZALARNI YUKLASH (Tepadagi 5 ta bo'sh qatorni tashlab o'tish) ---
@st.cache_data
def bazani_yukla():
    # Papkadagi barcha Excel va CSV fayllarni qidirish
    fayllar = [f for f in os.listdir('.') if (f.endswith('.xlsx') or f.endswith('.csv')) and 'app.py' not in f]
    if not fayllar:
        return None
    
    dfs = []
    for f in fayllar:
        try:
            # Fayllaringizda tepadagi 5 qator bo'sh, shuning uchun skiprows=5
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
df = bazani_yukla()

if df is not None:
    st.success(f"✅ Baza tayyor! {len(df)} ta qator yuklandi.")
    
    savol = st.chat_input("Ism yoki sinfni yozing...")

    if savol:
        with st.chat_message("user"):
            st.write(savol)
        
        with st.chat_message("assistant"):
            # Bazadan qidirish (Katta-kichik harfga qaramasdan)
            mask = df.apply(lambda row: row.astype(str).str.contains(savol, case=False, na=False).any(), axis=1)
            qidirilgan_data = df[mask]
            
            if qidirilgan_data.empty:
                context_text = "Bazadan hech qanday ma'lumot topilmadi."
            else:
                context_text = qidirilgan_data.head(20).to_string(index=False)
            
            try:
                # 404 xatosini oldini olish uchun eng aniq model nomi
                model = genai.GenerativeModel('gemini-1.5-flash')
                
                prompt = f"""
                Sen maktab yordamchi botisan. Faqat quyidagi ma'lumotlarga tayanib javob ber.
                Ma'lumotlar:
                {context_text}
                
                Savol: {savol}
                Javobni o'zbek tilida ber.
                """
                
                with st.spinner("Qidiryapman..."):
                    response = model.generate_content(prompt)
                    st.write(response.text)
            except Exception as e:
                # Agar gemini-1.5-flash yana 404 bersa, gemini-pro ni sinaymiz
                try:
                    model_alt = genai.GenerativeModel('gemini-pro')
                    response = model_alt.generate_content(prompt)
                    st.write(response.text)
                except Exception as e2:
                    st.error(f"Xatolik: {e2}")
else:
    st.warning("⚠️ Fayllar topilmadi. GitHub'da Excel yoki CSV borligini tekshiring.")
