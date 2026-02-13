import streamlit as st
import pandas as pd
import os

# 1. SOZLAMALAR
TO_GRI_PAROL = "informatika2024"
st.set_page_config(page_title="Maktab AI Analitika", layout="centered")

# --- PAROL ---
if "authenticated" not in st.session_state:
    st.title("🔐 Kirish")
    parol = st.text_input("Parol:", type="password")
    if st.button("Kirish"):
        if parol == TO_GRI_PAROL:
            st.session_state.authenticated = True
            st.rerun()
        else:
            st.error("❌ Xato!")
    st.stop()

# --- BAZANI O'QISH ---
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

st.title("🏫 Maktab AI (Aqlli Hisobot)")
df = yuklash()

if "messages" not in st.session_state:
    st.session_state.messages = []

for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.write(m["content"])

# --- TAHLIL QISMI ---
if savol := st.chat_input("Savol yozing (Masalan: nechta o'quvchi bor?)"):
    st.session_state.messages.append({"role": "user", "content": savol})
    with st.chat_message("user"):
        st.write(savol)

    with st.chat_message("assistant"):
        javob = ""
        s = savol.lower()

        if df is not None:
            # 1. O'QUVCHILARNI SANASH (Sinf yoki O'quvchi so'zi bor qatorlar)
            if "nechta o'quvchi" in s:
                # 'Sinf' ustuni bor yoki 'O'quvchi' deb yozilgan qatorlarni topamiz
                mask_oqv = df.apply(lambda r: r.astype(str).str.contains(r'^\d+-', case=False, na=False).any() or r.astype(str).str.contains('o\'quvchi', case=False, na=False).any(), axis=1)
                soni = len(df[mask_oqv])
                javob = f"Bazadagi ma'lumotlarga ko'ra, jami **{soni} ta o'quvchi** bor."

            # 2. O'QITUVCHILARNI SANASH
            elif "nechta o'qituvchi" in s or "pedagog" in s:
                mask_oqt = df.apply(lambda r: r.astype(str).str.contains('o\'qituvchi|pedagog|o’qituvchi|direktor', case=False, na=False).any(), axis=1)
                soni = len(df[mask_oqt])
                javob = f"Bazada jami **{soni} ta o'qituvchi** (pedagog xodim) mavjud."

            # 3. UMUMIY SONI
            elif "nechta" in s and "jami" in s:
                javob = f"Bazada jami (o'qituvchi va o'quvchi birga) **{len(df)} ta** qator mavjud."

            # 4. SERTIFIKATLAR (faqat o'quvchilarda borlarini chiqaradi)
            elif "sertifikat" in s:
                ser_mask = df.apply(lambda r: r.astype(str).str.contains('sertifikat|bor|mavjud|ha', case=False, na=False).any(), axis=1)
                ser_df = df[ser_mask]
                javob = f"Sertifikatga ega bo'lganlar soni: **{len(ser_df)} ta**.\n\nRo'yxat:\n"
                for idx, row in ser_df.iterrows():
                    # Ism va familiyani topish (taxminan 1 va 2-ustunlar)
                    javob += f"✅ {row.iloc[0]} {row.iloc[1]}\n"

            # 5. ODDIY QIDIRUV (Ism yozilganda)
            else:
                mask = df.apply(lambda row: row.astype(str).str.contains(savol, case=False, na=False).any(), axis=1)
                res = df[mask].head(10)
                if not res.empty:
                    javob = "Topilgan ma'lumotlar:\n\n"
                    for _, r in res.iterrows():
                        row_text = " | ".join([f"**{c}**: {v}" for c, v in r.items() if str(v) != 'nan'])
                        javob += f"📌 {row_text}\n\n---\n"
                else:
                    javob = f"'{savol}' bo'yicha hech narsa topilmadi."
        else:
            javob = "Baza yuklanmagan!"

        st.markdown(javob)
        st.session_state.messages.append({"role": "assistant", "content": javob})
