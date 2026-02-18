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
    st.error("⚠️ Secrets bo'limida ma'lumotlar xato yoki yetishmayapti!")
    st.stop()

# --- 2. HIKMATLI SO'ZLAR ---
HIKMATLAR = [
    "Ilm - najotdir.",
    "Ustoz - otangdek ulug'.",
    "Kitob - bilim manbai.",
    "O'qishdan to'xtagan odam, fikrlashdan ham to'xtaydi.",
    "Ilm qaytariqlari bilan go'zal."
]

# --- 3. BAZANI YUKLASH ---
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
                    key = f"{f.lower()} | {name.lower()}"
                    all_sheets[key] = df
        except:
            continue
    return all_sheets

sheets_baza = yuklash()

# --- 4. DIZAYN VA XAVFSIZLIK ---
st.set_page_config(page_title=MAKTAB_NOMI, layout="wide")

if "authenticated" not in st.session_state:
    st.title(f"🏫 {MAKTAB_NOMI}")
    parol = st.text_input("Kirish paroli:", type="password", key="login_pass")
    if st.button("Kirish", key="login_btn"):
        if parol == TO_GRI_PAROL:
            st.session_state.authenticated = True
            st.rerun()
        else:
            st.error("Parol xato!")
    st.stop()

# --- 5. SIDEBAR (FAQAT BIR MARTA!) ---
with st.sidebar:
    st.title(f"🏛 {MAKTAB_NOMI}")
    st.write(f"👤 **Direktor:** {DIREKTOR_FIO}")
    st.divider()
    # "key" parametri orqali Duplicate xatosi oldi olinadi
    menu = st.radio("Bo'limni tanlang:", ["🤖 AI Muloqot", "📊 Jurnal Monitoringi"], key="nav_menu")
    st.divider()
    st.subheader("💡 Kun hikmati:")
    st.info(random.choice(HIKMATLAR))
    # --- 6. AI MULOQOT (MAKSIMAL ANIQ QIDIRUV) ---
if menu == "🤖 AI Muloqot":
    st.title("🤖 Maktab AI yordamchisi")
    
    if "messages" not in st.session_state: st.session_state.messages = []
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]): st.markdown(msg["content"])

    if savol := st.chat_input("Ism yozing (masalan: JALILOVA yoki Dilfuza)..."):
        st.session_state.messages.append({"role": "user", "content": savol})
        with st.chat_message("user"): st.markdown(savol)
        
        with st.chat_message("assistant"):
            q = savol.upper().strip() # Qidiruvni KATTA harfga o'giramiz
            topildi = False
            
            # 1. RO'YXAT so'ralsa
            if "RO'YXAT" in q or "KIMLAR BOR" in q:
                if sheets_baza:
                    st.success("📋 Maktab bazasidagi pedagoglar:")
                    for key, df in sheets_baza.items():
                        # Ustun nomini qidirish (pedagogning ismi familiyasi)
                        col_name = next((c for c in df.columns if "pedagog" in c or "ismi" in c), df.columns[0])
                        st.dataframe(df[[col_name]], use_container_width=True)
                    topildi = True
                else:
                    st.warning("Baza topilmadi. Fayllarni GitHub-ga yuklang.")
                    topildi = True

            # 2. ISHNI QIDIRISH (Harflarga e'tibor bermasdan)
            elif sheets_baza:
                for key, df in sheets_baza.items():
                    # Har bir qatorni matnga aylantirib, ichidan qidiramiz
                    mask = df.apply(lambda row: row.astype(str).str.contains(savol, case=False, na=False).any(), axis=1)
                    res_df = df[mask]
                    if not res_df.empty:
                        st.success(f"🔍 '{savol}' bo'yicha topilgan ma'lumot:")
                        st.dataframe(res_df, use_container_width=True)
                        topildi = True; break

            # 3. Agar bazada bo'lmasa Groq AI javob beradi
            if not topildi:
                try:
                    chat_completion = client.chat.completions.create(
                        messages=[{"role": "system", "content": f"Sen {MAKTAB_NOMI} yordamchisisan. O'qituvchilarga ochiq darslarda yordam ber."},
                                 {"role": "user", "content": savol}],
                        model="llama-3.3-70b-versatile",
                    )
                    javob = chat_completion.choices[0].message.content
                    st.markdown(javob)
                    st.session_state.messages.append({"role": "assistant", "content": javob})
                except:
                    st.error("AI bilan bog'lanishda xato.")# --- 6. AI MULOQOT (MAKSIMAL ANIQ QIDIRUV) ---
if menu == "🤖 AI Muloqot":
    st.title("🤖 Maktab AI yordamchisi")
    
    if "messages" not in st.session_state: st.session_state.messages = []
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]): st.markdown(msg["content"])

    if savol := st.chat_input("Ism yozing (masalan: JALILOVA yoki Dilfuza)..."):
        st.session_state.messages.append({"role": "user", "content": savol})
        with st.chat_message("user"): st.markdown(savol)
        
        with st.chat_message("assistant"):
            q = savol.upper().strip() # Qidiruvni KATTA harfga o'giramiz
            topildi = False
            
            # 1. RO'YXAT so'ralsa
            if "RO'YXAT" in q or "KIMLAR BOR" in q:
                if sheets_baza:
                    st.success("📋 Maktab bazasidagi pedagoglar:")
                    for key, df in sheets_baza.items():
                        # Ustun nomini qidirish (pedagogning ismi familiyasi)
                        col_name = next((c for c in df.columns if "pedagog" in c or "ismi" in c), df.columns[0])
                        st.dataframe(df[[col_name]], use_container_width=True)
                    topildi = True
                else:
                    st.warning("Baza topilmadi. Fayllarni GitHub-ga yuklang.")
                    topildi = True

            # 2. ISHNI QIDIRISH (Harflarga e'tibor bermasdan)
            elif sheets_baza:
                for key, df in sheets_baza.items():
                    # Har bir qatorni matnga aylantirib, ichidan qidiramiz
                    mask = df.apply(lambda row: row.astype(str).str.contains(savol, case=False, na=False).any(), axis=1)
                    res_df = df[mask]
                    if not res_df.empty:
                        st.success(f"🔍 '{savol}' bo'yicha topilgan ma'lumot:")
                        st.dataframe(res_df, use_container_width=True)
                        topildi = True; break

            # 3. Agar bazada bo'lmasa Groq AI javob beradi
            if not topildi:
                try:
                    chat_completion = client.chat.completions.create(
                        messages=[{"role": "system", "content": f"Sen {MAKTAB_NOMI} yordamchisisan. O'qituvchilarga ochiq darslarda yordam ber."},
                                 {"role": "user", "content": savol}],
                        model="llama-3.3-70b-versatile",
                    )
                    javob = chat_completion.choices[0].message.content
                    st.markdown(javob)
                    st.session_state.messages.append({"role": "assistant", "content": javob})
                except:
                    st.error("AI bilan bog'lanishda xato.")# --- 6. AI MULOQOT (MAKSIMAL ANIQ QIDIRUV) ---
if menu == "🤖 AI Muloqot":
    st.title("🤖 Maktab AI yordamchisi")
    
    if "messages" not in st.session_state: st.session_state.messages = []
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]): st.markdown(msg["content"])

    if savol := st.chat_input("Ism yozing (masalan: JALILOVA yoki Dilfuza)..."):
        st.session_state.messages.append({"role": "user", "content": savol})
        with st.chat_message("user"): st.markdown(savol)
        
        with st.chat_message("assistant"):
            q = savol.upper().strip() # Qidiruvni KATTA harfga o'giramiz
            topildi = False
            
            # 1. RO'YXAT so'ralsa
            if "RO'YXAT" in q or "KIMLAR BOR" in q:
                if sheets_baza:
                    st.success("📋 Maktab bazasidagi pedagoglar:")
                    for key, df in sheets_baza.items():
                        # Ustun nomini qidirish (pedagogning ismi familiyasi)
                        col_name = next((c for c in df.columns if "pedagog" in c or "ismi" in c), df.columns[0])
                        st.dataframe(df[[col_name]], use_container_width=True)
                    topildi = True
                else:
                    st.warning("Baza topilmadi. Fayllarni GitHub-ga yuklang.")
                    topildi = True

            # 2. ISHNI QIDIRISH (Harflarga e'tibor bermasdan)
            elif sheets_baza:
                for key, df in sheets_baza.items():
                    # Har bir qatorni matnga aylantirib, ichidan qidiramiz
                    mask = df.apply(lambda row: row.astype(str).str.contains(savol, case=False, na=False).any(), axis=1)
                    res_df = df[mask]
                    if not res_df.empty:
                        st.success(f"🔍 '{savol}' bo'yicha topilgan ma'lumot:")
                        st.dataframe(res_df, use_container_width=True)
                        topildi = True; break

            # 3. Agar bazada bo'lmasa Groq AI javob beradi
            if not topildi:
                try:
                    chat_completion = client.chat.completions.create(
                        messages=[{"role": "system", "content": f"Sen {MAKTAB_NOMI} yordamchisisan. O'qituvchilarga ochiq darslarda yordam ber."},
                                 {"role": "user", "content": savol}],
                        model="llama-3.3-70b-versatile",
                    )
                    javob = chat_completion.choices[0].message.content
                    st.markdown(javob)
                    st.session_state.messages.append({"role": "assistant", "content": javob})
                except:
                    st.error("AI bilan bog'lanishda xato.")
                    # --- 6. AI MULOQOT (MAKSIMAL ANIQ QIDIRUV) ---
if menu == "🤖 AI Muloqot":
    st.title("🤖 Maktab AI yordamchisi")
    
    if "messages" not in st.session_state: st.session_state.messages = []
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]): st.markdown(msg["content"])

    if savol := st.chat_input("Ism yozing (masalan: JALILOVA yoki Dilfuza)..."):
        st.session_state.messages.append({"role": "user", "content": savol})
        with st.chat_message("user"): st.markdown(savol)
        
        with st.chat_message("assistant"):
            q = savol.upper().strip() # Qidiruvni KATTA harfga o'giramiz
            topildi = False
            
            # 1. RO'YXAT so'ralsa
            if "RO'YXAT" in q or "KIMLAR BOR" in q:
                if sheets_baza:
                    st.success("📋 Maktab bazasidagi pedagoglar:")
                    for key, df in sheets_baza.items():
                        # Ustun nomini qidirish (pedagogning ismi familiyasi)
                        col_name = next((c for c in df.columns if "pedagog" in c or "ismi" in c), df.columns[0])
                        st.dataframe(df[[col_name]], use_container_width=True)
                    topildi = True
                else:
                    st.warning("Baza topilmadi. Fayllarni GitHub-ga yuklang.")
                    topildi = True

            # 2. ISHNI QIDIRISH (Harflarga e'tibor bermasdan)
            elif sheets_baza:
                for key, df in sheets_baza.items():
                    # Har bir qatorni matnga aylantirib, ichidan qidiramiz
                    mask = df.apply(lambda row: row.astype(str).str.contains(savol, case=False, na=False).any(), axis=1)
                    res_df = df[mask]
                    if not res_df.empty:
                        st.success(f"🔍 '{savol}' bo'yicha topilgan ma'lumot:")
                        st.dataframe(res_df, use_container_width=True)
                        topildi = True; break

            # 3. Agar bazada bo'lmasa Groq AI javob beradi
            if not topildi:
                try:
                    chat_completion = client.chat.completions.create(
                        messages=[{"role": "system", "content": f"Sen {MAKTAB_NOMI} yordamchisisan. O'qituvchilarga ochiq darslarda yordam ber."},
                                 {"role": "user", "content": savol}],
                        model="llama-3.3-70b-versatile",
                    )
                    javob = chat_completion.choices[0].message.content
                    st.markdown(javob)
                    st.session_state.messages.append({"role": "assistant", "content": javob})
                except:
                    st.error("AI bilan bog'lanishda xato.")
                   # --- 7. MONITORING (XATOLIKLARNI TUZATUVCHI VARIANT) ---
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




