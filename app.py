import streamlit as st
import google.generativeai as genai
import pandas as pd
import os

# 1. API VA XAVFSIZLIK
API_KEY = "AIzaSyAp3ImXzlVyNF_UXjes2LsSVhG0Uusobdw"
TO_GRI_PAROL = "informatika2024"
FAYL_NOMI = "baza.xlsx" 

# Google AI ni rasmiy kutubxona orqali sozlash
genai.configure(api_key=API_KEY)

st.set_page_config(page_title="Maktab AI | Ma'rufjon Abdiyev", layout="centered")

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

# --- BAZANI O'QISH (Toza fayl uchun) ---
@st.cache_data
def bazani_yukla():
    if os.path.exists(FAYL_NOMI):
        try:
            # Barcha listlarni (O'quvchilar va Pedagoglar) o'qiymiz
            all_sheets = pd.read_excel(FAYL_NOMI, sheet_name=None, dtype=str)
            df = pd.concat(all_sheets.values(), ignore_index=True)
            return df
        except Exception as e:
            st.error(f"Faylni o'qishda xato: {e}")
            return None
    return None

# --- ASOSIY QISM ---
st.title("🏫 Maktab AI Yordamchisi")
df = bazani_yukla()

if df is not None:
    st.success(f"✅ Baza yuklandi! {len(df)} ta ma'lumot tayyor.")
    
    savol = st.chat_input("Ism, familiya yoki sinf bo'yicha so'rang...")

    if savol:
        with st.chat_message("user"):
            st.write(savol)
        
        with st.chat_message("assistant"):
            # Bazadan qidirish
            mask = df.apply(lambda row: row.astype(str).str.contains(savol, case=False, na=False).any(), axis=1)
            results = df[mask].head(25)
            
            if results.empty:
                st.write("Bazadan ma'lumot topilmadi.")
            else:
                context = results.to_string(index=False)
                
                try:
                    # MODELNI CHAQIRISH (Eng barqaror usul)
                    model = genai.GenerativeModel('gemini-1.5-flash')
                    
                    with st.spinner("O'ylayapman..."):
                        response = model.generate_content(
                            f"Sen maktab yordamchisisan. Faqat quyidagi ma'lumotlarga tayanib o'zbek tilida javob ber:\n\n{context}\n\nSavol: {savol}"
                        )
                        st.write(response.text)
                except Exception as e:
                    # Agar 1.5-flash ishlamasa, gemini-pro ni sinab ko'radi
                    try:
                        model_alt = genai.GenerativeModel('gemini-pro')
                        response = model_alt.generate_content(f"Ma'lumot: {context}\nSavol: {savol}")
                        st.write(response.text)
                    except:
                        st.error("AI bilan bog'lanishda xato. API kalitingizni tekshiring.")
else:
    st.warning(f"⚠️ '{FAYL_NOMI}' fayli topilmadi.")
