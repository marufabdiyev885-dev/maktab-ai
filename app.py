import streamlit as st
import pandas as pd
import os

# 1. SOZLAMALAR
TO_GRI_PAROL = "informatika2024"
st.set_page_config(page_title="Maktab AI | Analitika", layout="wide")

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
            # Ustun nomlaridagi bo'shliqlarni olib tashlaymiz
            df.columns = [str(c).strip() for c in df.columns]
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
if savol := st.chat_input("Savol yozing (Masalan: nechta o'qituvchi bor?)"):
    st.session_state.messages.append({"role": "user", "content": savol})
    with st.chat_message("user"):
        st.write(savol)

    with st.chat_message("assistant"):
        javob = ""
        s = savol.lower()

        if df is not None:
            # 1. PEDAGOG USTUNINI TOPISH (Moslashuvchan qidiruv)
            pedagog_col = [c for c in df.columns if 'pedago' in c.lower()]
            
            # 2. O'QITUVCHILARNI SANASH
            if "nechta o'qituvchi" in s or "pedagog" in s:
                if pedagog_col:
                    # Pedagog ustunida ism yozilgan qatorlarni sanaymiz
                    col_name = pedagog_col[0]
                    oqt_df = df[df[col_name].notna() & (df[col_name].astype(str).str.len() > 2)]
                    javob = f"Bazada jami **{len(oqt_df)} ta** o'qituvchi (pedagog) topildi."
                else:
                    # Agar ustun topilmasa, bazadagi ustun nomlarini ko'rsatamiz (tekshirish uchun)
                    ustunlar = ", ".join(df.columns)
                    javob = f"Kechirasiz, 'pedagog' so'zi bor ustunni topolmadim. Bazadagi ustunlar: {ustunlar}"

            # 3. O'QUVCHILARNI SANASH
            elif "nechta o'quvchi" in s:
                if pedagog_col:
                    # Pedagog ustuni bo'sh bo'lgan qatorlar - bular o'quvchilar
                    col_name = pedagog_col[0]
                    oqv_df = df[df[col_name].isna() | (df[col_name].astype(str).str.len() < 2)]
                    javob = f"Bazadagi o'quvchilar soni: **{len(oqv_df)} ta**."
                else:
                    javob = f"Jami ma'lumotlar soni: **{len(df)} ta**."

            # 4. SERTIFIKATLAR
            elif "sertifikat" in s:
                ser_mask = df.apply(lambda r: r.astype(str).str.contains('sertifikat|bor|mavjud|ha|yes', case=False, na=False).any(), axis=1)
                ser_df = df[ser_mask]
                javob = f"Sertifikati borlar soni: **{len(ser_df)} ta**."
                st.dataframe(ser_df)

            # 5. QIDIRUV
            else:
                mask = df.apply(lambda row: row.astype(str).str.contains(savol, case=False, na=False).any(), axis=1)
                res = df[mask].head(10)
                if not res.empty:
                    javob = f"'{savol}' bo'yicha natijalar:"
                    st.dataframe(res)
                else:
                    javob = f"Kechirasiz, '{savol}' bo'yicha ma'lumot yo'q."
        else:
            javob = "Baza yuklanmagan!"

        st.markdown(javob)
        st.session_state.messages.append({"role": "assistant", "content": javob})
