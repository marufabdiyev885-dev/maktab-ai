import streamlit as st
import pandas as pd
import os

# 1. SOZLAMALAR
TO_GRI_PAROL = "informatika2024"
st.set_page_config(page_title="Maktab AI | Analitika", layout="centered")

# --- PAROL TIZIMI ---
if "authenticated" not in st.session_state:
    st.title("🔐 Tizimga kirish")
    parol = st.text_input("Parol:", type="password")
    if st.button("Kirish"):
        if parol == TO_GRI_PAROL:
            st.session_state.authenticated = True
            st.rerun()
        else:
            st.error("❌ Parol noto'g'ri!")
    st.stop()

# --- BAZANI YUKLASH ---
@st.cache_data
def yuklash():
    files = [f for f in os.listdir('.') if f.lower().endswith(('.xlsx', '.csv')) and 'app.py' not in f]
    all_data = []
    for f in files:
        try:
            if f.endswith('.csv'):
                df = pd.read_csv(f, dtype=str)
            else:
                df = pd.read_excel(f, dtype=str)
            all_data.append(df)
        except:
            continue
    return pd.concat(all_data, ignore_index=True) if all_data else None

st.title("🏫 Maktab Aqlli Yordamchisi")
df = yuklash()

if "messages" not in st.session_state:
    st.session_state.messages = []

for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.write(m["content"])

# --- ASOSIY MANTIQ ---
if savol := st.chat_input("Savol yozing..."):
    st.session_state.messages.append({"role": "user", "content": savol})
    with st.chat_message("user"):
        st.write(savol)

    with st.chat_message("assistant"):
        javob = ""
        s = savol.lower()

        if df is not None:
            # 1. O'QITUVCHILARNI ANIQLASH (Siz aytgan ustun nomi orqali)
            # Ustun nomlari ichida 'pedagok' yoki 'o'qituvchi' so'zi borligini tekshiramiz
            pedagog_col = [c for c in df.columns if 'pedagok' in c.lower() or 'o\'qituvchi' in c.lower()]
            
            if "nechta o'qituvchi" in s or "pedagog" in s:
                if pedagog_col:
                    # Pedagog ustunida ma'lumot bor qatorlarni sanaymiz
                    oqt_soni = df[df[pedagog_col[0]].notna() & (df[pedagog_col[0]] != '')].shape[0]
                    javob = f"Bazada jami **{oqt_soni} ta o'qituvchi** (pedagog) ro'yxatga olingan."
                else:
                    javob = "Bazadan 'pedagokning ismi familiyasi' degan ustunni topa olmadim."

            # 2. O'QUVCHILARNI SANASH
            elif "nechta o'quvchi" in s:
                # O'qituvchi bo'lmagan qatorlarni o'quvchi deb hisoblaymiz (yoki sinfi borlarni)
                if pedagog_col:
                    oqv_df = df[df[pedagog_col[0]].isna() | (df[pedagog_col[0]] == '')]
                    soni = len(oqv_df)
                    javob = f"Bazadagi o'quvchilar soni: **{soni} ta**."
                else:
                    javob = f"Umumiy ma'lumotlar soni: **{len(df)} ta**."

            # 3. SERTIFIKATLARNI TEKSHIRISH
            elif "sertifikat" in s:
                ser_mask = df.apply(lambda r: r.astype(str).str.contains('sertifikat|bor|mavjud|ha|yes', case=False, na=False).any(), axis=1)
                ser_df = df[ser_mask]
                if not ser_df.empty:
                    javob = f"Sertifikati borlar soni: **{len(ser_df)} ta**.\n\n"
                    st.dataframe(ser_df)
                else:
                    javob = "Sertifikat haqida ma'lumot topilmadi."

            # 4. QIDIRUV (Ism yozilganda)
            else:
                mask = df.apply(lambda row: row.astype(str).str.contains(savol, case=False, na=False).any(), axis=1)
                res = df[mask].head(10)
                if not res.empty:
                    javob = f"'{savol}' bo'yicha natijalar:\n"
                    st.dataframe(res)
                else:
                    javob = f"Kechirasiz, '{savol}' bo'yicha ma'lumot yo'q."
        else:
            javob = "Baza yuklanmagan!"

        st.markdown(javob)
        st.session_state.messages.append({"role": "assistant", "content": javob})
