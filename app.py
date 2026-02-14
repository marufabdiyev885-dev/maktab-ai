import streamlit as st
import random

# --- 1. ASOSIY SOZLAMALAR ---
MAKTAB_NOMI = "1-sonli umumiy o'rta ta'lim maktabi"
TO_GRI_PAROL = "informatika2024"

st.set_page_config(page_title=MAKTAB_NOMI, layout="wide")

# --- 2. DIZAYN (TEPADAGI OQ JOYNI YO'QOTISH) ---
def set_bg(url):
    st.markdown(
        f"""
        <style>
        /* Ekranning eng tepasidagi bo'shliqlarni nolga tushiramiz */
        .stApp {{
            background: linear-gradient(rgba(0,0,0,0.6), rgba(0,0,0,0.6)), url("{url}");
            background-size: cover;
            background-position: center;
            background-attachment: fixed;
        }}

        /* Streamlitning standart oq tepa qismini (header) yashiramiz */
        header {{visibility: hidden;}}
        .main .block-container {{
            padding-top: 0rem;
            padding-bottom: 0rem;
            padding-left: 0rem;
            padding-right: 0rem;
        }}

        /* Matnlar uchun uslub */
        .white-text {{
            color: white;
            text-align: center;
            text-shadow: 2px 2px 10px rgba(0,0,0,1);
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            width: 100%;
        }}
        
        .school-title {{
            font-size: 42px;
            font-weight: bold;
            padding-top: 80px; /* Tepadan masofani rasm ichida beramiz */
        }}

        .login-title {{
            font-size: 28px;
            margin-top: 20px;
        }}

        /* Input maydonchasi */
        div[data-baseweb="input"] {{
            background-color: rgba(255, 255, 255, 0.9) !important;
            border-radius: 12px !important;
            max-width: 350px;
            margin: auto;
        }}
        
        /* Tugma markazda */
        .stButton button {{
            max-width: 350px;
            display: block;
            margin: 0 auto;
        }}
        </style>
        """,
        unsafe_allow_html=True
    )

# --- 3. LOGIN EKRANI ---
if "authenticated" not in st.session_state:
    # Rasm manzili
    bg_url = "https://images.unsplash.com/photo-1509062522246-3755977927d7?q=80&w=1600"
    set_bg(bg_url)

    # 1. Maktab nomi
    st.markdown(f'<div class="white-text school-title">🏛 {MAKTAB_NOMI}</div>', unsafe_allow_html=True)
    
    st.write("<br>", unsafe_allow_html=True)

    # 2. Tizimga kirish yozuvi
    st.markdown('<div class="white-text login-title">Tizimga kirish</div>', unsafe_allow_html=True)

    # 3. Markaziy qism (Parol va tugma)
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        parol = st.text_input("", placeholder="Parolni kiriting...", type="password", key="login_pass", label_visibility="collapsed")
        
        if st.button("Kirish 🚀", use_container_width=True):
            if parol == TO_GRI_PAROL:
                st.session_state.authenticated = True
                st.rerun()
            else:
                st.error("❌ Parol noto'g'ri!")
    st.stop()

# --- 4. KIRGANDAN KEYINGI QISM ---
st.success("Tizimga kirdingiz!")
