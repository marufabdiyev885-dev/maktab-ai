import streamlit as st
import pandas as pd
import os
import requests
import io
import random

# --- 1. ASOSIY SOZLAMALAR ---
MAKTAB_NOMI = "1-sonli umumta'lim maktabi"
DIREKTOR_FIO = "Mahmudov Matyoqub Narzulloyevich"
GROQ_API_KEY = "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"
TO_GRI_PAROL = "informatika2024"
MONITORING_KODI = "admin777" 
BOT_TOKEN = "8524007504:AAFiMXSbXhe2M-84WlNM16wNpzhNolfQIf8"
GURUH_ID = "-5045481739" 

# O'zgarib turuvchi hikmatlar ro'yxati
HIKMATLAR_RO_YXATI = [
    "Ilm — saodat kalitidir.",
    "Hunari yo'q kishi — mevasi yo'q daraxt.",
    "Ilm izla, igna bilan quduq qazigandek bo'lsa ham.",
    "O'qigan o'zini taniydi, o'qimagan — ko'zini.",
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

# --- 3. SIDEBAR (DIREKTOR VA O'ZGARUVCHAN HIKMAT) ---
with st.sidebar:
    st.title(f"🏛 {MAKTAB_NOMI}")
    st.write(f"👤 **Maktab direktori:** \n{DIREKTOR_FIO}")
    st.divider()
    menu = st.radio("Bo'limni tanlang:", ["🤖 AI bilan muloqot", "📊 Jurnal Monitoringi"])
    st.divider()
    # Har safar sahifa yangilanganda o'zgaradigan hikmat
    st.info(f"✨ **Kun hikmati:**\n*{random.choice(HIKMATLAR_RO_YXATI)}*")

# --- 4. XAVFSIZLIK ---
if "authenticated" not in st.session_state:
    st.title(f"🏫 {MAKTAB_NOMI}")
    parol = st.text_input("Kirish paroli:", type="password")
    if st.button("Kirish"):
        if parol == TO_GRI_PAROL:
            st.session_state.authenticated = True
            st.rerun()
        else: st.error("Parol noto'g'ri!")
    st.stop()

# --- 5. MAKTAB SUN'IY INTELLEKTI BILAN MULOQOT ---
if menu == "🤖 AI bilan muloqot":
    st.title("🤖 Maktab sun'iy intellekti bilan muloqot")
    
    if "greeted" not in st.session_state:
        st.session_state.greeted = False

    if not st.session_state.greeted:
        with st.chat_message("assistant"):
            st.markdown(f"**Assalomu alaykum, hurmatli foydalanuvchi!**\n\nSizga qanday ma'lumot qidirib berishim mumkin?")
        st.session_state.greeted = True

    if savol := st.chat_input("Savolingizni kiriting..."):
        with st.chat_message("user"): st.markdown(savol)
        
        with st.chat_message("assistant"):
            res_df = pd.DataFrame()
            salomlar = ["salom", "assalom", "qalay", "yaxshimi"]
            is_greeting = any(s in savol.lower() for s in salomlar)

            if is_greeting:
                st.markdown("Vaalaykum assalom! **Hurmatli foydalanuvchi**, sizga xizmat qilishdan mamnunman.")
            elif sheets_baza:
                is_teacher_req = any(x in savol.lower() for x in ["o'qituvchi", "pedagog", "ro'yxat", "xodim"])
                
                if is_teacher_req and "Лист2" in sheets_baza:
                    res_df = sheets_baza["Лист2"]
                else:
                    all_df = pd.concat(sheets_baza.values(), ignore_index=True, sort=False).fillna("")
                    q = savol.lower()
                    mask = all_df.apply(lambda row: any(q in str(v).lower() for v in row), axis=1)
                    res_df = all_df[mask]

                if not res_df.empty:
                    st.success(f"Natija topildi ({len(res_df)} ta qator).")
                    st.dataframe(res_df, use_container_width=True)
                    
                    # Excel yuklash tugmasi
                    output = io.BytesIO()
                    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                        res_df.to_excel(writer, index=False)
                    st.download_button("📥 Natijani Excelda yuklab olish", output.getvalue(), "natija.xlsx")
                else:
                    st.warning("Hurmatli foydalanuvchi, bazada bunday ma'lumot topilmadi.")
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
            else: st.error("Xato!")
        st.stop()

    j_fayl = st.file_uploader("Faylni yuklang", type=['xlsx', 'xls', 'html'])
    if j_fayl:
        try:
            try:
                df_j = pd.read_excel(j_fayl)
            except:
                j_fayl.seek(0)
                df_j = pd.read_html(j_fayl, header=0)[0]
            
            df_j.columns = [str(c).replace('\n', ' ').strip() for c in df_j.columns]
            st.dataframe(df_j)

            col_target = "Baholar qo'yilgan jurnallar soni"
            col_name = "O'qituvchi"
            
            kamchiliklar = []
            if col_target in df_j.columns:
                for _, row in df_j.iterrows():
                    val = str(row[col_target])
                    nums = re.findall(r'(\d+)', val)
                    if len(nums) >= 2:
                        if int(nums[0]) < int(nums[1]):
                            kamchiliklar.append(f"❌ {row[col_name]}: {int(nums[1]) - int(nums[0])} ta jurnal yozilmagan")
            
            xabar_tahlili = "✅ Barcha jurnallar to'liq baholangan!" if not kamchiliklar else "⚠️ **Kamchiliklar aniqlandi:**\n" + "\n".join(kamchiliklar)
            st.info(xabar_tahlili)

            if st.button("📢 Telegramga hisobotni yuborish"):
                requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", 
                             json={"chat_id": GURUH_ID, "text": f"<b>📊 {MAKTAB_NOMI} Monitoringi</b>\n\n{xabar_tahlili}", "parse_mode": "HTML"})
                st.success("✅ Telegramga yuborildi!")
                    
        except Exception as e:
            st.error(f"Fayl xatosi: {e}")


