import streamlit as st
import google.generativeai as genai
import pandas as pd
import os

# 1. API VA XAVFSIZLIK
API_KEY = "AIzaSyAp3ImXzlVyNF_UXjes2LsSVhG0Uusobdw"
TO_GRI_PAROL = "informatika2024"

# Google AI ni sozlash
genai.configure(api_key=API_KEY)

st.set_page_config(page_title="Maktab AI", layout="centered")

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

# --- BAZANI O'QISH (CSV VA EXCEL UCHUN) ---
@st.cache_data
def yuklash():
    # Papkadagi barcha CSV va Excel fayllarni topish
    files = [f for f in os.listdir('.') if f.endswith(('.xlsx', '.csv')) and 'app.py' not in f]
    all_data = []
    for f in files:
        try:
            if f.endswith('.csv'):
                # CSV fayllarni UTF-8 formatida o'qish
                df = pd.read_csv(f, dtype=str, encoding='utf-8')
            else:
                # Excelning barcha listlarini birlashtirish
                sheets = pd.read_excel(f, sheet_name=None, dtype=str)
                df = pd.concat(sheets.values(), ignore_index=True)
            all_data.append(df)
        except:
            continue
    return pd.concat(all_data, ignore_index=True) if all_data else None

# --- ASOSIY QISM ---
st.title("🏫 Maktab AI Yordamchisi")
df = yuklash()

if df is not None:
    st.success(f"✅ Baza tayyor! {len(df)} ta qator yuklandi.")
    
    savol = st.chat_input("Ism yozing (Masalan: NASIMOV yoki JALILOVA)")

    if savol:
        with st.chat_message("user"):
            st.write(savol)
        
        with st.chat_message("assistant"):
            # AQLLI QIDIRUV: Katta-kichik harfga qaramasdan bazadan topish
            mask = df.apply(lambda row: row.astype(str).str.contains(savol, case=False, na=False).any(), axis=1)
            results = df[mask].head(15)
            
            if results.empty:
                st.warning(f"'{savol}' bo'yicha ma'lumot topilmadi.")
            else:
                context = results.to_string(index=False)
                
                # MODELNI TO'G'RI CHAQIRISH (models/ prefiksi bilan)
                try:
                    # 404 xatosini oldini olish uchun prefiks qo'shildi
                    model = genai.GenerativeModel('models/gemini-1.5-flash')
                    
                    with st.spinner("AI javob bermoqda..."):
                        prompt = f"Sen maktab yordamchisisan. Faqat ushbu ma'lumotlar asosida javob ber:\n{context}\n\nSavol: {savol}"
                        response = model.generate_content(prompt)
                        st.write(response.text)
                except Exception as e:
                    # Agar models/ prefiksi ham xato bersa, prefiksiz sinab ko'radi
                    try:
                        model_alt = genai.GenerativeModel('gemini-pro')
                        response = model_alt.generate_content(f"Ma'lumot: {context}\nSavol: {savol}")
                        st.write(response.text)
                    except:
                        st.error(f"AI bilan bog'lanishda xato: {e}")
else:
    st.warning("⚠️ Fayllar topilmadi. GitHub-ga .xlsx yoki .csv fayllarni yuklang.")
