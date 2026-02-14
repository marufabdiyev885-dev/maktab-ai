import streamlit as st
import pandas as pd
import os
import requests
import io
import random
import re

# --- 1. ASOSIY SOZLAMALAR ---
MAKTAB_NOMI = "1-sonli umumta'lim maktabi"
DIREKTOR_FIO = "Mahmudov Matyoqub Narzulloyevich"
GROQ_API_KEY = "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"
TO_GRI_PAROL = "informatika2024"
MONITORING_KODI = "admin777" 
BOT_TOKEN = "8524007504:AAFiMXSbXhe2M-84WlNM16wNpzhNolfQIf8"
GURUH_ID = "-5045481739" 

HIKMATLAR_RO_YXATI = [
    "Ilm — saodat kalitidir.",
    "Hunari yo'q kishi — mevasi yo'q daraxt.",
    "Ilm izla, igna bilan quduq qazigandek bo'lsa ham.",
    "Bilim — tuganmas xazina.",
    "Kitob — bilim manbai.",
    "Aql — yoshda emas, boshda.",
    "Ilm — qalb chirog'i.",
    "Vaqt — g'animat, o'tayotgan har oningni ilmga bag'ishla.",
    "Odob — har bir kishining ziynatidir."
]

st.set_page_config(page_title=MAKTAB_NOMI, layout="wide")

# --- 2. BAZANI YUKLASH ---
@st.cache_data
def yuklash():
    files = [f for f in os.listdir('.') if f.lower().endswith(('.xlsx', '.xls', '.csv')) and 'app.py' not in f]
    all_sheets = {}
    for f in files:
        try:
            sheets = pd.read_excel(f, sheet_name=None, dtype=str)
            for name, df in sheets.items():
                if not df.empty:
                    df.columns = [str(c).strip().lower() for c in df.columns]
                    all_sheets[name] = df
        except: continue
    return all_sheets

sheets_baza = yuklash()

# --- 3. SIDEBAR ---
with st.sidebar:
    st.title(f"🏛 {MAKTAB_NOMI}")
    st.write(f"👤 **Maktab direktori:** \n{DIREKTOR_FIO}")
    st.divider()
    menu = st.radio("Bo'limni tanlang:", ["🤖 AI Muloqot", "📊 Jurnal Monitoringi"])
    st.divider()
    st.info(f"✨ **Kun hikmati:**\n*{random.choice(HIKMATLAR_RO_YXATI)}*")

# --- 4. XAVFSIZLIK ---
if "authenticated" not in st.session_state:
    st.title(f"🏫 {MAKTAB_NOMI}")
    parol = st.text_input("Kirish paroli:", type="password")
    if st.button("Kirish"):
        if parol == TO_GRI_PAROL:
            st.session_state.authenticated = True
            st.rerun()
        else: st.error("Parol xato-ku, aka!")
    st.stop()

# --- 5. MAKTAB SUN'IY INTELLEKTI BILAN MULOQOT ---
if menu == "🤖 AI Muloqot":
    st.title("🤖 Aqlli muloqot tizimi")
    
    if "greeted" not in st.session_state:
        st.session_state.greeted = False
    if not st.session_state.greeted:
        with st.chat_message("assistant"):
            st.markdown(f"**Assalomu alaykum, Ma'rufjon aka!** Nima yordam kerak?")
        st.session_state.greeted = True

    if savol := st.chat_input("Savolingizni yoki ismni yozing..."):
        with st.chat_message("user"): st.markdown(savol)
        
        with st.chat_message("assistant"):
            q = savol.lower().strip()
            
            # 1. Insoniy muloqot
            if q in ["rahmat", "katta rahmat", "tashakkur", "rahmat AI"]:
                st.markdown("Arziydi, aka! Sizga xizmat qilish — men uchun sharaf. 😊")
            elif q in ["salom", "assalom", "assalomu alaykum"]:
                st.markdown("Vaalaykum assalom, aka! Yaxshimisiz? Qanday ma'lumot qidiramiz?")
            
            # 2. Bazadan qidirish
            elif sheets_baza:
                combined_df = pd.concat(sheets_baza.values(), ignore_index=True, sort=False).fillna("")
                
                # Aniq qidiruv (1-A va 11-A muammosini hal qiluvchi regex)
                pattern = rf"\b{re.escape(q)}\b"
                mask = combined_df.apply(lambda row: any(re.search(pattern, str(v), re.IGNORECASE) for v in row), axis=1)
                res_df = combined_df[mask]

                if not res_df.empty:
                    st.success(f"Ma'rufjon aka, bazadan {len(res_df)} ta ma'lumot topdim:")
                    st.dataframe(res_df, use_container_width=True)
                else:
                    st.warning("Aka, bazadan topolmadim. Balki ismni boshqacharoq yozib ko'rarsiz?")
                    st.info(f"💡 [Google orqali qidirish](https://www.google.com/search?q={savol})")

# --- 6. JURNAL MONITORINGI ---
elif menu == "📊 Jurnal Monitoringi":
    st.title("📊 Jurnal Monitoringi")
    
    if "m_auth" not in st.session_state: st.session_state.m_auth = False
    if not st.session_state.m_auth:
        m_pass = st.text_input("Monitoring kodi:", type="password")
        if st.button("Kirish"):
            if m_pass == MONITORING_KODI:
                st.session_state.m_auth = True
                st.rerun()
            else: st.error("Kod xato!")
        st.stop()

    j_fayl = st.file_uploader("eMaktab Excel faylini yuklang", type=['xlsx', 'xls', 'html'])
    if j_fayl:
        try:
            try: df_j = pd.read_excel(j_fayl)
            except:
                j_fayl.seek(0)
                df_j = pd.read_html(j_fayl, header=0)[0]
            
            df_j.columns = [str(c).replace('\n', ' ').strip() for c in df_j.columns]
            st.dataframe(df_j)

            col_target, col_name = "Baholar qo'yilgan jurnallar soni", "O'qituvchi"
            kamchiliklar = []
            if col_target in df_j.columns:
                for _, row in df_j.iterrows():
                    nums = re.findall(r'(\d+)', str(row[col_target]))
                    if len(nums) >= 2 and int(nums[0]) < int(nums[1]):
                        kamchiliklar.append(f"❌ {row[col_name]}: {int(nums[1]) - int(nums[0])} ta jurnal chala")
            
            xabar_tahlili = "✅ Barcha jurnallar to'liq baholangan!" if not kamchiliklar else "⚠️ **Kamchiliklar:**\n" + "\n".join(kamchiliklar)
            st.info(xabar_tahlili)

            if st.button("📢 Telegramga yuborish"):
                requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", 
                             json={"chat_id": GURUH_ID, "text": f"<b>📊 Monitoring</b>\n\n{xabar_tahlili}", "parse_mode": "HTML"})
                st.success("✅ Telegramga yuborildi!")
                    
        except Exception as e:
            st.error(f"Xato: {e}")
