import streamlit as st
import pandas as pd
import os
import requests
import re
import random
from groq import Groq

# --- 1. SOZLAMALAR ---
try:
    MAKTAB_NOMI = "1-sonli umumta'lim maktabi"
    DIREKTOR_FIO = "Mahmudov Matyoqub Narzulloyevich"
    TO_GRI_PAROL = "informatika2024"
    MONITORING_KODI = "admin777"
    
    BOT_TOKEN = st.secrets["TELEGRAM_BOT_TOKEN"]
    GURUH_ID = st.secrets["TELEGRAM_GURUH_ID"]
    GROQ_API_KEY = st.secrets["GROQ_API_KEY"]
    
    client = Groq(api_key=GROQ_API_KEY)
except Exception:
    st.error("⚠️ Secrets ma'lumotlarida xatolik bor!")
    st.stop()

# --- 2. BAZANI YUKLASH ---
@st.cache_data
def yuklash():
    files = [f for f in os.listdir('.') if f.lower().endswith(('.xlsx', '.xls'))]
    all_sheets = {}
    for f in files:
        try:
            sheets = pd.read_excel(f, sheet_name=None, dtype=str)
            for name, df in sheets.items():
                if not df.empty:
                    df.columns = [str(c).strip().lower() for c in df.columns]
                    all_sheets[f"{f} | {name}"] = df
        except: continue
    return all_sheets

sheets_baza = yuklash()

# --- 3. DIZAYN VA KIRISH ---
st.set_page_config(page_title=MAKTAB_NOMI, layout="wide")

if "authenticated" not in st.session_state:
    st.title(f"🏫 {MAKTAB_NOMI}")
    p_in = st.text_input("Kirish paroli:", type="password", key="main_auth_key")
    if st.button("Kirish", key="main_auth_btn"):
        if p_in == TO_GRI_PAROL:
            st.session_state.authenticated = True
            st.rerun()
        else: st.error("Xato!")
    st.stop()

# --- 4. SIDEBAR ---
with st.sidebar:
    st.title(f"🏛 {MAKTAB_NOMI}")
    st.write(f"👤 **Direktor:** {DIREKTOR_FIO}")
    menu = st.radio("Bo'limni tanlang:", ["🤖 AI Muloqot", "📊 Jurnal Monitoringi"], key="nav_menu")
    st.divider()
    st.info("💡 Bilim - najotdir.")

# --- 5. AI MULOQOT (MUKAMMAL VA FAROSATLI VARIANT) ---
if menu == "🤖 AI Muloqot":
    st.title("🤖 Maktab AI yordamchisi")
    
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    if savol := st.chat_input("Qanday yordam bera olaman?", key="chat_input_v3"):
        st.session_state.messages.append({"role": "user", "content": savol})
        with st.chat_message("user"):
            st.markdown(savol)
        
        with st.chat_message("assistant"):
            q_low = savol.lower().strip()
            topildi = False
            
            # 1. IJTIMOIY MULOQOT (Salom, rahmat...)
            ijtimoiy = {
                "rahmat": "Sizdan ham Alloh rozi bo'lsin! Doim xizmatingizdaman. 😊",
                "salom": "Vaalaykum assalom! Maktabimiz tizimiga xush kelibsiz. Qanday yordam kerak? 🏛",
                "xayr": "Xayr, sog' bo'ling! Ishlaringizda rivoj tilayman. 👋",
                "zo'r": "Katta rahmat! Sizga manzur bo'lganidan juda xursandman. 🌟"
            }
            
            for k, j in ijtimoiy.items():
                if k in q_low:
                    st.markdown(j)
                    st.session_state.messages.append({"role": "assistant", "content": j})
                    topildi = True
                    break

            # 2. BAZADAN AQLLI QIDIRUV
            if not topildi:
                # Kalit so'zlarni aniqlash
                is_list_req = any(x in q_low for x in ["ro'yxat", "hamma", "barcha", "jadval"])
                is_teacher_req = any(x in q_low for x in ["o'qituvchi", "ustoz", "pedagog", "xodim"])
                
                # Qidiruv uchun toza so'zni olish
                search_word = q_low
                for w in ["top", "ber", "chiqar", "ro'yxati", "haqida", "izla", "ko'rsat"]:
                    search_word = search_word.replace(w, "").strip()

                for key, df in sheets_baza.items():
                    # A) Agar butun ro'yxat so'ralgan bo'lsa
                    if is_list_req and is_teacher_req:
                        if "o'qituvchi" in key.lower() or "xodim" in key.lower():
                            msg = "📋 Mana, maktabimiz o'qituvchilari ro'yxati:"
                            st.info(msg)
                            st.dataframe(df, use_container_width=True)
                            st.session_state.messages.append({"role": "assistant", "content": msg})
                            topildi = True
                            break
                    
                    # B) Agar aniq ism yoki ma'lumot qidirilayotgan bo'lsa
                    elif len(search_word) >= 3:
                        mask = df.apply(lambda r: r.astype(str).str.contains(search_word, case=False, na=False).any(), axis=1)
                        res_df = df[mask]
                        if not res_df.empty:
                            msg = f"🔍 **{search_word.capitalize()}** bo'yicha ma'lumotlarni topdim:"
                            st.success(msg)
                            st.dataframe(res_df, use_container_width=True)
                            st.session_state.messages.append({"role": "assistant", "content": msg})
                            topildi = True
                            break

            # 3. AGAR HECH NARSA TOPILMASA -> GROQ AI
            if not topildi:
                try:
                    res = client.chat.completions.create(
                        messages=[
                            {"role": "system", "content": f"Sen {MAKTAB_NOMI}ning aqlli yordamchisisan. Samimiy va o'zbekona lutf bilan gaplash. Bazada yo'q narsani so'rashsa, muloyimlik bilan tushuntir."},
                            {"role": "user", "content": savol}
                        ],
                        model="llama-3.3-70b-versatile"
                    )
                    ai_javob = res.choices[0].message.content
                    st.markdown(ai_javob)
                    st.session_state.messages.append({"role": "assistant", "content": ai_javob})
                except:
                    st.error("AI hozirda band. Keyinroq urinib ko'ring.")
                    # --- 6. MONITORING (SENING MANTIQING) ---
elif menu == "📊 Jurnal Monitoringi":
    st.title("📊 Jurnal Monitoringi")
    
    if "m_auth" not in st.session_state:
        st.session_state.m_auth = False
        
    if not st.session_state.m_auth:
        m_input = st.text_input("Monitoring kodi:", type="password", key="mon_input")
        if st.button("Kirish", key="mon_btn"):
            if m_input == MONITORING_KODI:
                st.session_state.m_auth = True
                st.rerun()
            else:
                st.error("Kod xato!")
        st.stop()
    
    j_fayl = st.file_uploader("Excel faylni yuklang", type=['xlsx', 'xls', 'html'], key="uploader")
    
    if j_fayl:
        try:
            # Faylni o'qishning bir nechta usulini sinab ko'ramiz
            try:
                # 1-usul: Standart Excel (openpyxl)
                df_j = pd.read_excel(j_fayl, engine='openpyxl')
            except Exception:
                try:
                    # 2-usul: Eski Excel (.xls - xlrd)
                    j_fayl.seek(0)
                    df_j = pd.read_excel(j_fayl, engine='xlrd')
                except Exception:
                    try:
                        # 3-usul: HTML formatidagi Excel
                        j_fayl.seek(0)
                        df_j = pd.read_html(j_fayl, header=0)[0]
                    except Exception:
                        # 4-usul: Engine belgilamasdan urinish
                        j_fayl.seek(0)
                        df_j = pd.read_excel(j_fayl)

            # Ustunlarni tozalash
            df_j.columns = [str(c).replace('\n', ' ').strip() for c in df_j.columns]
            
            kamchiliklar = []
            if len(df_j.columns) >= 6:
                for _, row in df_j.iterrows():
                    name = str(row.iloc[0]) # 0-ustun: Ismlar
                    val = str(row.iloc[5])  # 5-ustun: Baholar holati
                    
                    if any(x in name.lower() for x in ["tuman", "muassasa", "o'qituvchi", "f.i.sh"]):
                        continue
                        
                    nums = re.findall(r'(\d+)', val)
                    if len(nums) >= 2:
                        baho_bor, jami = int(nums[0]), int(nums[1])
                        if baho_bor < jami:
                            farq = jami - baho_bor
                            kamchiliklar.append(f"❌ **{name}**: {farq} ta jurnal chala ({val})")
                
                st.subheader("📋 Tekshiruv Natijasi:")
                st.dataframe(df_j, use_container_width=True)
                
                xabar_text = "✅ Hammasi to'liq!" if not kamchiliklar else "⚠️ **Kamchiliklar:**\n\n" + "\n".join(kamchiliklar)
                if not kamchiliklar: st.success(xabar_text)
                else: st.warning(xabar_text)
                
                st.divider()
                if st.button("📢 Telegramga yuborish", key="tg_btn"):
                    requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", 
                                 json={"chat_id": GURUH_ID, "text": f"<b>📊 Monitoring</b>\n\n{xabar_text}", "parse_mode": "HTML"})
                    st.success("✅ Telegramga yuborildi!")
            else:
                st.error(f"Faylda ustunlar yetarli emas. Topildi: {len(df_j.columns)} ta.")
                
        except Exception as e:
            st.error(f"Faylni o'qishda kutilmagan xato: {e}")


