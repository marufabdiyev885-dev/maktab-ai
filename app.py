import streamlit as st
import google.generativeai as genai
import pandas as pd
import os

# 1. SOZLAMALAR
API_KEY = "AIzaSyAp3ImXzlVyNF_UXjes2LsSVhG0Uusobdw"
TO_GRI_PAROL = "informatika2024"

# Google AI ni sozlash (Aniq model nomi bilan)
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
    # Papkadagi barcha Excel va CSV fayllarni topish
    fayllar = [f for f in os.listdir('.') if f.endswith(('.xlsx', '.csv')) and 'app.py' not in f]
    
    dfs = []
    for f in fayllar:
        try:
            # Fayllaringiz tozalangan bo'lsa, skiprows shart emas
            if f.endswith('.csv'):
                temp_df = pd.read_csv(f, dtype=str)
            else:
                temp_df = pd.read_excel(f, dtype=str)
            dfs.append(temp_df)
        except:
            continue
    
    return pd.concat(dfs, ignore_index=True) if dfs else None

st.title("🏫 Maktab AI Yordamchisi")
df = bazani_yukla()

if df is not None:
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
                
                # MODELNI TO'G'RI CHAQIRISH (Modul ichida xatoni ko'rsatadi)
                try:
                    # 'models/' prefiksi bilan yozish xatolarni oldini oladi
                    model = genai.GenerativeModel('models/gemini-1.5-flash')
                    
                    with st.spinner("AI javob tayyorlayapti..."):
                        response = model.generate_content(
                            f"Faqat ushbu ma'lumotlar asosida javob ber:\n{context}\n\nSavol: {savol}"
                        )
                        st.write(response.text)
                except Exception as e:
                    # Haqiqiy xatoni ekranga chiqarish (sababini bilish uchun)
                    st.error(f"AI xatosi yuz berdi: {str(e)}")
else:
    st.warning("⚠️ Fayllar topilmadi. GitHub-ga fayllarni yuklang.")
