import streamlit as st
import google.generativeai as genai
import pandas as pd
import os

# 1. API VA SOZLAMALAR
API_KEY = "AIzaSyAp3ImXzlVyNF_UXjes2LsSVhG0Uusobdw"
TO_GRI_PAROL = "informatika2024"
FAYL_NOMI = "baza.xlsx" 

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
def bazani_yukla():
    # Hozirgi papkadagi hamma fayllarni ko'rish (Tekshirish uchun)
    barcha_fayllar = os.listdir('.')
    
    if os.path.exists(FAYL_NOMI):
        try:
            # Excelning barcha betlarini o'qish
            all_sheets = pd.read_excel(FAYL_NOMI, sheet_name=None, dtype=str)
            df = pd.concat(all_sheets.values(), ignore_index=True)
            return df
        except Exception as e:
            st.error(f"Faylni o'qishda xato: {e}")
            return None
    else:
        st.error(f"⚠️ '{FAYL_NOMI}' topilmadi!")
        st.write("GitHub'dagi fayllar ro'yxati:", barcha_fayllar)
        return None

st.title("🏫 Maktab AI Yordamchisi")
df = bazani_yukla()

if df is not None:
    st.success(f"✅ Baza yuklandi! {len(df)} ta qator topildi.")
    
    savol = st.chat_input("Masalan: JALILOVA DILFUZA")

    if savol:
        with st.chat_message("user"):
            st.write(savol)
        
        with st.chat_message("assistant"):
            # Bazadan qidirish (Katta-kichik harfga qaramaydi)
            mask = df.apply(lambda row: row.astype(str).str.contains(savol, case=False, na=False).any(), axis=1)
            results = df[mask].head(20)
            
            if results.empty:
                st.warning("Bazadan ushbu ism bo'yicha ma'lumot topilmadi. Ism to'g'ri yozilganini tekshiring.")
            else:
                context = results.to_string(index=False)
                try:
                    model = genai.GenerativeModel('gemini-1.5-flash')
                    response = model.generate_content(f"Ma'lumotlar: {context}\nSavol: {savol}")
                    st.write(response.text)
                except:
                    st.error("AI bilan bog'lanishda muammo.")
