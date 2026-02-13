import streamlit as st
import requests
import pandas as pd
import os

# 1. SOZLAMALAR
API_KEY = "AIzaSyAp3ImXzlVyNF_UXjes2LsSVhG0Uusobdw"
TO_GRI_PAROL = "informatika2024"
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
            # Excelning barcha listlarini birlashtirib o'qiymiz
            all_sheets = pd.read_excel(FAYL_NOMI, sheet_name=None, dtype=str)
            combined_df = pd.concat(all_sheets.values(), ignore_index=True)
            return combined_df
        except Exception as e:
            st.error(f"Faylni o'qishda xato: {e}")
            return None
    return None

# --- ASOSIY QISM ---
st.title("🏫 Maktab AI Yordamchisi")
df = bazani_yukla()

if df is not None:
    st.success(f"✅ Baza tayyor! {len(df)} ta qator yuklandi.")
    
    savol = st.chat_input("Ism yoki familiyani yozing...")

    if savol:
        with st.chat_message("user"):
            st.write(savol)
        
        with st.chat_message("assistant"):
            # Bazadan qidirish
            mask = df.apply(lambda row: row.astype(str).str.contains(savol, case=False, na=False).any(), axis=1)
            context_data = df[mask].head(25).to_string(index=False)
            
            if not context_data.strip() or "Empty DataFrame" in context_data:
                context_data = "Ma'lumot topilmadi."

            # 404 XATOSINI OLDIRINI OLUVCHI TO'G'RI URL:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={API_KEY}"
            
            with st.spinner("Qidiryapman..."):
                payload = {
                    "contents": [{
                        "parts": [{
                            "text": f"Sen maktab yordamchisisan. Quyidagi ma'lumotlarga tayanib o'zbek tilida javob ber:\n{context_data}\n\nSavol: {savol}"
                        }]
                    }]
                }
                
                try:
                    r = requests.post(url, json=payload)
                    if r.status_code == 200:
                        res_json = r.json()
                        st.write(res_json['candidates'][0]['content']['parts'][0]['text'])
                    else:
                        # Agar yana 404 bersa, muqobil modelni sinab ko'radi
                        st.error(f"API xatosi: {r.status_code}. Iltimos, API kalitini yoki model nomini tekshiring.")
                except Exception as e:
                    st.error(f"Bog'lanishda xato: {e}")
else:
    st.warning(f"⚠️ '{FAYL_NOMI}' fayli topilmadi. GitHub'ga yuklaganingizga ishonch hosil qiling.")
