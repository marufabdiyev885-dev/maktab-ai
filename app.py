# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
import re

# --- 1. SOZLAMALAR ---
st.set_page_config(page_title="eMaktab Monitoring", layout="wide")

# --- 2. JADVALNI OLISH FUNKSIYASI ---
def get_emaktab_data(school_id, cookie):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Cookie': cookie
    }
    # Rasmda ko'ringan aniq URL
    url = f"https://schools.emaktab.uz/v2/reports/default?school={school_id}&report=paid-access-school&year=2025"
    
    try:
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            return None, f"Xato: Status {response.status_code}"

        soup = BeautifulSoup(response.content, 'html.parser')
        rows = []
        
        # Sahifadagi barcha qatorlarni tekshiramiz
        for tr in soup.find_all('tr'):
            tds = tr.find_all('td')
            if len(tds) >= 4:
                sinf = tds[0].get_text(strip=True)
                foiz = tds[3].get_text(strip=True)
                
                # Faqat sinf nomi bor qatorlarni olamiz (Masalan: 1-A)
                if re.search(r'\d+-[A-ZА-Я]', sinf):
                    rows.append([sinf, foiz])
        
        if rows:
            return pd.DataFrame(rows, columns=['Sinf', 'Kundalik %']), "OK"
        return None, "Jadval topilmadi. Cookie xato yoki muddati o'tgan."
    except Exception as e:
        return None, str(e)

# --- 3. INTERFEYS ---
st.title("📊 eMaktab: Kundalikka kirish")

# Yon panelda sozlamalar
with st.sidebar:
    st.header("Sozlamalar")
    school_id = st.text_input("Maktab ID:", value="1000001352999")
    cookie_input = st.text_area("Brauzer Cookie (nusxalab qo'ying):", height=200)
    st.info("Cookie olish uchun: F12 -> Network -> Sahifani yangilang -> Har qanday so'rovni tanlang -> Headers -> Cookie matnini nusxalang.")

# Asosiy tugma
if st.button("Jadvalni yuklash"):
    if not cookie_input:
        st.error("Cookie kiritilmagan!")
    else:
        df, msg = get_emaktab_data(school_id, cookie_input)
        if df is not None:
            st.success(msg)
            st.table(df) # Rasmda ko'ringan tartibda jadval chiqaradi
            
            # Telegramga yuborish tugmasi (faqat jadval chiqsa ko'rinadi)
            st.session_state.table_df = df
        else:
            st.error(msg)

# Telegram bo'limi
if "table_df" in st.session_state:
    if st.button("📢 Telegramga yuborish"):
        # Telegram sozlamalaringizni buni yerga qo'ying
        st.write("Telegramga yuborish funksiyasi chaqirildi...")
