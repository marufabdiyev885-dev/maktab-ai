import streamlit as st
import google.generativeai as genai
import pandas as pd
import os

# 1. API VA SOZLAMALAR
API_KEY = "AIzaSyAp3ImXzlVyNF_UXjes2LsSVhG0Uusobdw"
TO_GRI_PAROL = "informatika2024"

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

# --- BAZANI O'QISH (KUCHAYTIRILGAN) ---
@st.cache_data
def bazani_yukla():
    # Papkadagi barcha Excel va CSV fayllarni topish
    fayllar = [f for f in os.listdir('.') if f.endswith(('.xlsx', '.csv')) and 'app.py' not in f]
    
    if not fayllar:
        st.error("⚠️ GitHub'da hech qanday Excel yoki CSV fayl topilmadi!")
        return None
    
    dfs = []
    for f in fayllar:
        try:
            if f.endswith('.csv'):
                # CSV bo'lsa (UTF-8 formatida o'qiymiz)
                temp_df = pd.read_csv(f, dtype=str, encoding='utf-8')
            else:
                # Excel bo'lsa
                temp_df = pd.read_excel(f, dtype=str)
            dfs.append(temp_df)
        except Exception as e:
            st.warning(f"{f} faylini o'qishda muammo: {e}")
            continue
            
    if dfs:
        return pd.concat(dfs, ignore_index=True)
    return None

st.title("🏫 Maktab AI Yordamchisi")
df = bazani_yukla()

if df is not None:
    st.success(f"✅ Baza tayyor! {len(df)} ta qator yuklandi.")
    
    savol = st.chat_input("Ism yozing (masalan: SHERZODBEK yoki DILFUZA)")

    if savol:
        with st.chat_message("user"):
            st.write(savol)
        
        with st.chat_message("assistant"):
            # Bazadan qidirish (Katta-kichik harfga qaramaydi)
            # o‘, g‘ harflari muammosini hal qilish uchun qisman qidirish
            mask = df.apply(lambda row: row.astype(str).str.contains(savol, case=False, na=False).any(), axis=1)
            results = df[mask].head(15) # AIga 15 ta qator yetarli
            
            if results.empty:
                st.warning(f"'{savol}' bo'yicha ma'lumot topilmadi. Ismni boshqacharoq yozib ko'ring.")
            else:
                context = results.to_string(index=False)
                try:
                    # Modelni chaqirish
                    model = genai.GenerativeModel('gemini-1.5-flash')
                    prompt = f"Sen maktab yordamchisisan. Quyidagi jadval ma'lumotlari asosida savolga o'zbek tilida javob ber:\n\n{context}\n\nSavol: {savol}"
                    
                    with st.spinner("O'ylayapman..."):
                        response = model.generate_content(prompt)
                        st.write(response.text)
                except Exception as e:
                    st.error("AI xizmati hozir band. Birozdan so'ng urinib ko'ring.")
else:
    st.warning("⚠️ Fayllar topilmadi. GitHub-ga fayllarni yuklang.")
