import streamlit as st
import google.generativeai as genai
import pandas as pd
import os

# 1. SOZLAMALAR
API_KEY = "AIzaSyAp3ImXzlVyNF_UXjes2LsSVhG0Uusobdw"
TO_GRI_PAROL = "informatika2024"

# Google AI sozlash (v1beta orqali 404 ni chetlab o'tamiz)
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

# --- BAZANI O'QISH (CSV VA EXCEL UCHUN) ---
@st.cache_data
def yuklash():
    # Papkadagi barcha CSV va Excel fayllarni topish
    files = [f for f in os.listdir('.') if f.endswith(('.xlsx', '.csv')) and 'app.py' not in f]
    all_data = []
    for f in files:
        try:
            if f.endswith('.csv'):
                # CSV fayllarni o'qish
                df = pd.read_csv(f, dtype=str, encoding='utf-8')
            else:
                # Excel fayllarni o'qish
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
    st.success(f"✅ Baza yuklandi! {len(df)} ta qator ma'lumot tayyor.")
    
    # Qidiruv maydoni
    savol = st.chat_input("Ism yoki sinfni yozing (Masalan: NASIMOV yoki 1-A)")

    if savol:
        with st.chat_message("user"):
            st.write(savol)
        
        with st.chat_message("assistant"):
            # AQLLI QIDIRUV: Katta-kichik harfga qaramaydi
            mask = df.apply(lambda row: row.astype(str).str.contains(savol, case=False, na=False).any(), axis=1)
            results = df[mask].head(15)
            
            if results.empty:
                st.warning(f"'{savol}' bo'yicha ma'lumot topilmadi. Ismni to'liq yoki boshqacharoq yozib ko'ring.")
            else:
                context = results.to_string(index=False)
                
                # MODELNI CHAQIRISH
                try:
                    # 'gemini-1.5-flash' eng barqaror model
                    model = genai.GenerativeModel('gemini-1.5-flash')
                    
                    with st.spinner("AI qidirmoqda..."):
                        prompt = f"Sen maktab bazasi yordamchisisan. Jadvaldagi ma'lumotlar: \n{context}\n\nSavol: {savol}. Javobni chiroyli o'zbek tilida ber."
                        response = model.generate_content(prompt)
                        st.write(response.text)
                except Exception as e:
                    st.error(f"AI ulanishda xato: {e}")
else:
    st.warning("⚠️ GitHub-ga fayllarni yuklang (baza.xlsx yoki baza.csv)!")
