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

# --- ISHLAYDIGAN MODELNI ANIQLASH (404 xatosini oldini olish) ---
@st.cache_resource
def get_working_model():
    try:
        # Mavjud modellarni tekshirish
        available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        
        # Ustuvor modellar ro'yxati
        priorities = ['models/gemini-1.5-flash', 'models/gemini-1.5-flash-8b', 'models/gemini-pro']
        
        for model_path in priorities:
            if model_path in available_models:
                return model_path
        return available_models[0] if available_models else "models/gemini-pro"
    except:
        return "models/gemini-pro"

# --- BAZALARNI YUKLASH VA BIRLASHTIRISH ---
@st.cache_data
def bazani_yukla():
    fayllar = [f for f in os.listdir('.') if f.endswith('.xlsx')]
    if not fayllar:
        return None
    
    dfs = []
    for f in fayllar:
        try:
            # Ma'lumotlarni matn sifatida o'qish (qidiruv oson bo'lishi uchun)
            temp_df = pd.read_excel(f, dtype=str)
            dfs.append(temp_df)
        except:
            continue
    
    if dfs:
        return pd.concat(dfs, ignore_index=True)
    return None

# --- ASOSIY QISM ---
st.title("🏫 Maktab AI Yordamchisi")
working_model_name = get_working_model()
df = bazani_yukla()

if df is not None:
    st.success(f"✅ Baza tayyor! ({len(df)} ta qator ma'lumot yuklandi)")
    
    savol = st.chat_input("Ism, familiya yoki sinf bo'yicha so'rang...")

    if savol:
        with st.chat_message("user"):
            st.write(savol)
        
        with st.chat_message("assistant"):
            # --- AQLLI FILTR (Limit 429 xatosini oldini olish uchun) ---
            qidiruv_sozlari = savol.split()
            # Kamida bitta so'z qatnashgan qatorlarni qidirish
            mask = df.apply(lambda row: row.astype(str).str.contains(qidiruv_sozlari[0], case=False).any(), axis=1)
            for soz in qidiruv_sozlari[1:]:
                mask &= df.apply(lambda row: row.astype(str).str.contains(soz, case=False).any(), axis=1)
            
            qidirilgan_data = df[mask]
            
            if qidirilgan_data.empty:
                context_text = "Bazadan ushbu so'rov bo'yicha hech qanday ma'lumot topilmadi."
            else:
                # Faqat topilgan qismini AIga yuboramiz (max 40 qator)
                context_text = qidirilgan_data.head(40).to_string(index=False)
            
            # --- AI JAVOBI ---
            try:
                model = genai.GenerativeModel(working_model_name)
                prompt = f"""
                Sen maktab yordamchi botisan. Faqat quyidagi ma'lumotlar bazasiga tayanib javob ber.
                Ma'lumot topilmasa, o'zingdan to'qima, bazada yo'qligini ayt.
                
                Bazadagi ma'lumotlar:
                {context_text}
                
                Foydalanuvchi savoli: {savol}
                Javobni o'zbek tilida, chiroyli va tushunarli qilib ber.
                """
                
                with st.spinner("Qidiryapman..."):
                    response = model.generate_content(prompt)
                    st.write(response.text)
            except Exception as e:
                if "429" in str(e):
                    st.error("⏳ Google limitiga yetdi. 30 soniyadan so'ng qayta urinib ko'ring.")
                else:
                    st.error(f"⚠️ Xatolik: {e}")
else:
    st.warning("⚠️ Excel (.xlsx) fayllar topilmadi. GitHub'ga fayllarni yuklang!")

with st.sidebar:
    st.info(f"Admin: Abdiyev Ma'rufjon")
    st.write(f"Model: {working_model_name}")
    if st.button("Chiqish"):
        del st.session_state.authenticated
        st.rerun()
