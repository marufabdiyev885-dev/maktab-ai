import streamlit as st
import google.generativeai as genai
import pandas as pd
import os

# 1. SOZLAMALAR
API_KEY = "AIzaSyAp3ImXzlVyNF_UXjes2LsSVhG0Uusobdw"
TO_GRI_PAROL = "informatika2024"

# Google AI ni sozlash
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

# --- ISHLAYDIGAN MODELNI TOPISH (404 xatosini yechish) ---
@st.cache_resource
def get_working_model():
    # Google tanishi mumkin bo'lgan barcha nomlar ketma-ketligi
    model_names = [
        'gemini-1.5-flash',
        'gemini-1.5-pro',
        'gemini-pro'
    ]
    
    for name in model_names:
        try:
            model = genai.GenerativeModel(name)
            # Kichik sinov o'tkazamiz
            model.generate_content("test", generation_config={"max_output_tokens": 1})
            return model
        except:
            continue
    return None

# --- BAZANI O'QISH ---
@st.cache_data
def bazani_yukla():
    # Papkadagi barcha Excel va CSV fayllarni topish
    fayllar = [f for f in os.listdir('.') if f.lower().endswith(('.xlsx', '.csv')) and 'app.py' not in f]
    
    dfs = []
    for f in fayllar:
        try:
            if f.lower().endswith('.csv'):
                temp_df = pd.read_csv(f, dtype=str)
            else:
                temp_df = pd.read_excel(f, dtype=str)
            dfs.append(temp_df)
        except:
            continue
    
    return pd.concat(dfs, ignore_index=True) if dfs else None

st.title("🏫 Maktab AI Yordamchisi")
df = bazani_yukla()
model = get_working_model()

if df is not None and model is not None:
    st.success(f"✅ Baza tayyor! {len(df)} ta qator yuklandi.")
    
    savol = st.chat_input("Ism yozing (masalan: SHERZODBEK)")

    if savol:
        with st.chat_message("user"):
            st.write(savol)
        
        with st.chat_message("assistant"):
            # Bazadan qidirish
            mask = df.apply(lambda row: row.astype(str).str.contains(savol, case=False, na=False).any(), axis=1)
            results = df[mask].head(15)
            
            if results.empty:
                st.warning(f"'{savol}' bo'yicha ma'lumot topilmadi.")
            else:
                context = results.to_string(index=False)
                try:
                    with st.spinner("AI javob bermoqda..."):
                        response = model.generate_content(
                            f"Sen maktab bazasi bo'yicha yordamchisan. Faqat quyidagi jadval ma'lumotlari asosida javob ber:\n\n{context}\n\nSavol: {savol}"
                        )
                        st.write(response.text)
                except Exception as e:
                    st.error(f"Xatolik: {str(e)}")
elif model is None:
    st.error("❌ Google AI tizimiga ulanib bo'lmadi. API kalit yoki model xatosi.")
else:
    st.warning("⚠️ Bazaga oid fayllar topilmadi.")
