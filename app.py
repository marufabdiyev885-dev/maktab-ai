import streamlit as st
import requests
import pandas as pd
import os

# 1. SOZLAMALAR
API_KEY = "AIzaSyAp3ImXzlVyNF_UXjes2LsSVhG0Uusobdw"
TO_GRI_PAROL = "informatika2024"

# --- BU YERGA FAYLINGIZ NOMINI TO'G'RI YOZING ---
FAYL_NOMI = "baza.xlsx" 

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

# --- BAZANI O'QISH ---
@st.cache_data
def bazani_yukla():
    if os.path.exists(FAYL_NOMI):
        try:
            # Excelning barcha listlarini (Sheet) o'qiymiz
            # Sizda 2 ta list bor (O'quvchilar va Pedagoglar), shuning uchun sheet_name=None
            all_sheets = pd.read_excel(FAYL_NOMI, sheet_name=None, dtype=str)
            
            # Barcha listlarni bitta jadvalga birlashtiramiz
            combined_df = pd.concat(all_sheets.values(), ignore_index=True)
            
            # Bo'sh qolgan qatorlarni tozalash
            combined_df = combined_df.dropna(how='all')
            return combined_df
        except Exception as e:
            st.error(f"Faylni o'qishda xato: {e}")
            return None
    else:
        st.error(f"⚠️ '{FAYL_NOMI}' topilmadi! Fayl nomi GitHub-da aynan shundayligini tekshiring.")
        return None

# --- ASOSIY QISM ---
st.title("🏫 Maktab AI Yordamchisi")
df = bazani_yukla()

if df is not None:
    st.success(f"✅ Baza tayyor! {len(df)} ta ma'lumot yuklandi.")
    
    savol = st.chat_input("Ism yoki ma'lumotni yozing...")

    if savol:
        with st.chat_message("user"):
            st.write(savol)
        
        with st.chat_message("assistant"):
            # Savolga mos qismini qidirib topish
            mask = df.apply(lambda row: row.astype(str).str.contains(savol, case=False, na=False).any(), axis=1)
            qidiruv_natijasi = df[mask].head(25) 
            
            if qidiruv_natijasi.empty:
                context = "Bazadan hech qanday ma'lumot topilmadi."
            else:
                context = qidiruv_natijasi.to_string(index=False)
            
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={API_KEY}"
            
            with st.spinner("Qidiryapman..."):
                payload = {
                    "contents": [{
                        "parts": [{
                            "text": f"Faqat ushbu ma'lumotlarga tayanib savolga o'zbek tilida javob ber:\n\n{context}\n\nSavol: {savol}"
                        }]
                    }]
                }
                r = requests.post(url, json=payload)
                if r.status_code == 200:
                    res_json = r.json()
                    st.write(res_json['candidates'][0]['content']['parts'][0]['text'])
                else:
                    st.error(f"AI Xatosi: {r.status_code}")
