import streamlit as st
import google.generativeai as genai
import pandas as pd
import os

# 1. SOZLAMALAR
API_KEY = "AIzaSyAp3ImXzlVyNF_UXjes2LsSVhG0Uusobdw"
TO_GRI_PAROL = "informatika2024"

# Google AI ni sozlash
genai.configure(api_key=API_KEY)

st.set_page_config(page_title="Maktab AI | Abdiyev Ma'rufjon", layout="centered")

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

# --- ISHLAYDIGAN MODELNI ANIQLASH (404 xatosini yengish) ---
@st.cache_resource
def get_working_model():
    # Eng barqaror va yangi model nomlari
    try:
        # Avval 1.5-flash modelini sinab ko'ramiz
        model = genai.GenerativeModel('gemini-1.5-flash')
        return 'gemini-1.5-flash'
    except:
        return 'gemini-pro'

# --- BAZALARNI YUKLASH (5-qatorni tashlab o'tish) ---
@st.cache_data
def bazani_yukla():
    # Papkadagi barcha Excel va CSV fayllarni qidirish
    fayllar = [f for f in os.listdir('.') if (f.endswith('.xlsx') or f.endswith('.csv')) and f != 'requirements.txt']
    if not fayllar:
        return None
    
    dfs = []
    for f in fayllar:
        try:
            # Fayl turiga qarab o'qiymiz va tepadagi 5 ta bo'sh qatorni tashlab ketamiz
            if f.endswith('.csv'):
                temp_df = pd.read_csv(f, dtype=str, skiprows=5)
            else:
                temp_df = pd.read_excel(f, dtype=str, skiprows=5)
            
            # Bo'sh qolgan yoki "Unnamed" deb nomlangan ustunlarni tozalash
            temp_df = temp_df.loc[:, ~temp_df.columns.str.contains('^Unnamed')]
            dfs.append(temp_df)
        except Exception as e:
            continue
    
    if dfs:
        return pd.concat(dfs, ignore_index=True)
    return None

# --- ASOSIY QISM ---
st.title("🏫 Maktab AI Yordamchisi")
working_model_name = get_working_model()
df = bazani_yukla()

if df is not None:
    st.success(f"✅ Baza tayyor! {len(df)} ta qator ma'lumot topildi.")
    
    savol = st.chat_input("Ism, familiya yoki sinf bo'yicha so'rang...")

    if savol:
        with st.chat_message("user"):
            st.write(savol)
        
        with st.chat_message("assistant"):
            # Savolni qidirish (Katta-kichik harfni farqlamaydi)
            mask = df.apply(lambda row: row.astype(str).str.contains(savol, case=False, na=False).any(), axis=1)
            qidirilgan_data = df[mask]
            
            if qidirilgan_data.empty:
                context_text = "Bazadan ushbu so'rov bo'yicha ma'lumot topilmadi."
            else:
                # Faqat topilgan qismini AIga yuboramiz (limit uchun max 30 qator)
                context_text = qidirilgan_data.head(30).to_string(index=False)
            
            try:
                # Modelni chaqirish
                model = genai.GenerativeModel(working_model_name)
                prompt = f"""
                Sen maktab yordamchi botisan. Quyidagi ma'lumotlar bazasiga tayanib foydalanuvchi savoliga javob ber.
                Ma'lumot topilmasa, bazada yo'qligini ayt. 
                
                Ma'lumotlar:
                {context_text}
                
                Savol: {savol}
                Javobni o'zbek tilida, tushunarli qilib ber.
                """
                
                with st.spinner("Qidiryapman..."):
                    response = model.generate_content(prompt)
                    st.write(response.text)
            except Exception as e:
                st.error(f"⚠️ AI bilan bog'lanishda xato: {e}")
else:
    st.warning("⚠️ Fayllar o'qilmadi. GitHub'ga Excel yoki CSV fayllarni yuklang.")
