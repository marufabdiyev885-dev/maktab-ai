import streamlit as st
import google.generativeai as genai
import pandas as pd
import os

# 1. Sozlamalar
API_KEY = "AIzaSyAp3ImXzlVyNF_UXjes2LsSVhG0Uusobdw"
TO_GRI_PAROL = "informatika2024"

genai.configure(api_key=API_KEY)

st.set_page_config(page_title="Maktab AI | Abdiyev Ma'rufjon", layout="centered")

# --- PAROL ---
if "authenticated" not in st.session_state:
    st.title("🔐 Kirish")
    parol = st.text_input("Parolni kiriting:", type="password")
    if st.button("Kirish"):
        if parol == TO_GRI_PAROL:
            st.session_state.authenticated = True
            st.rerun()
        else:
            st.error("❌ Parol noto'g'ri!")
    st.stop()

# --- BAZALARNI O'QISH ---
@st.cache_data
def bazani_yukla():
    fayllar = [f for f in os.listdir('.') if f.endswith('.xlsx')]
    if not fayllar:
        return None
    
    dfs = []
    for f in fayllar:
        try:
            # Excelni o'qishda hamma ustunlarni matn ko'rinishida olamiz
            temp_df = pd.read_excel(f, dtype=str)
            dfs.append(temp_df)
        except:
            continue
    return pd.concat(dfs, ignore_index=True) if dfs else None

# --- ASOSIY ---
st.title("🏫 Maktab AI Yordamchisi")
df = bazani_yukla()

if df is not None:
    st.success(f"✅ Baza yuklandi ({len(df)} ta qator mavjud).")
    
    savol = st.chat_input("Ism, familiya yoki sinfni yozing...")

    if savol:
        with st.chat_message("user"):
            st.write(savol)
        
        with st.chat_message("assistant"):
            # Savolni bo'laklarga bo'lib qidiramiz (masalan: "Ali 9-sinf")
            qidiruv_sozlari = savol.split()
            
            # Bazadan savolga aloqador qatorlarni topish
            mask = df.apply(lambda row: row.astype(str).str.contains(qidiruv_sozlari[0], case=False).any(), axis=1)
            for soz in qidiruv_sozlari[1:]:
                mask &= df.apply(lambda row: row.astype(str).str.contains(soz, case=False).any(), axis=1)
            
            qidirilgan_data = df[mask]
            
            # Agar juda ko'p ma'lumot chiqsa, limit uchun kamaytiramiz
            context_data = qidirilgan_data.head(30).to_string(index=False)
            
            if qidirilgan_data.empty:
                # Agar aniq topilmasa, AIga umumiyroq qidirishni buyuramiz
                context_data = "Bazadan aniq ma'lumot topilmadi. O'zingdagi umumiy bilimlardan foydalanma, faqat bazada yo'qligini ayt."

            try:
                model = genai.GenerativeModel('models/gemini-1.5-flash')
                prompt = f"""
                Sen maktab xodimlari va o'quvchilari haqidagi bazadan javob beruvchi yordamchisan.
                
                Quyida bazadan topilgan ma'lumotlar berilgan:
                {context_data}
                
                Foydalanuvchi savoli: {savol}
                
                Vazifang: 
                1. Agar ma'lumot topilgan bo'lsa, jadval shaklida yoki chiroyli qilib tushuntirib ber.
                2. Agar ma'lumot topilmagan bo'lsa, "Kechirasiz, bazada bunday ma'lumot topilmadi" deb javob ber.
                Javobni o'zbek tilida ber.
                """
                
                with st.spinner("O'ylayapman..."):
                    response = model.generate_content(prompt)
                    st.write(response.text)
            except Exception as e:
                st.error(f"Xato yuz berdi: {e}")
else:
    st.warning("⚠️ Excel fayllar hali ham topilmadi. Nomlarini tekshiring!")
