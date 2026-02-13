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

# --- ISHLAYDIGAN MODELNI AVTOMATIK ANIQLASH ---
@st.cache_resource
def get_model():
    # Tizimda ruxsat berilgan barcha modellarni ko'rib chiqadi
    try:
        # Avval eng yaxshisini sinab ko'radi
        m = genai.GenerativeModel('gemini-1.5-flash')
        m.generate_content("hi", generation_config={"max_output_tokens": 1})
        return m
    except:
        try:
            # Agar flash-1.5 bo'lmasa, pro versiyani ko'radi
            m = genai.GenerativeModel('gemini-pro')
            return m
        except:
            return None

# --- BAZANI O'QISH (CSV VA EXCEL UCHUN) ---
@st.cache_data
def yuklash():
    # Papkadagi barcha fayllarni tekshirish
    files = [f for f in os.listdir('.') if f.endswith(('.xlsx', '.csv'))]
    all_data = []
    for f in files:
        try:
            if f.endswith('.csv'):
                df = pd.read_csv(f, dtype=str)
            else:
                # Excelning barcha listlarini birlashtirish
                sheets = pd.read_excel(f, sheet_name=None, dtype=str)
                df = pd.concat(sheets.values(), ignore_index=True)
            all_data.append(df)
        except:
            continue
    return pd.concat(all_data, ignore_index=True) if all_data else None

# --- ASOSIY ---
st.title("🏫 Maktab AI Yordamchisi")
model = get_model()
df = yuklash()

if df is not None and model is not None:
    st.success(f"✅ Tizim tayyor! {len(df)} ta qator yuklandi.")
    
    savol = st.chat_input("Ism yoki sinfni yozing...")
    if savol:
        with st.chat_message("user"):
            st.write(savol)
        
        with st.chat_message("assistant"):
            # Filtrlash (Ismni bazadan qidirish)
            mask = df.apply(lambda row: row.astype(str).str.contains(savol, case=False, na=False).any(), axis=1)
            results = df[mask].head(10)
            
            if results.empty:
                st.warning("Ma'lumot topilmadi.")
            else:
                context = results.to_string(index=False)
                with st.spinner("AI o'ylamoqda..."):
                    try:
                        response = model.generate_content(f"Ma'lumot: {context}\nSavol: {savol}\nJavobni o'zbekcha ber.")
                        st.write(response.text)
                    except Exception as e:
                        st.error(f"Xatolik: {e}")
elif model is None:
    st.error("❌ Google AI modeliga ulanib bo'lmadi. Kalitni tekshiring.")
else:
    st.warning("⚠️ Fayllar topilmadi.")
