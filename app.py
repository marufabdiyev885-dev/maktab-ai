import streamlit as st
import requests

# 1. Sozlamalar (Sizning maktabingizga mos)
SCHOOL_ID = "1000001352999"
REPORT_URL = f"https://schools.emaktab.uz/v2/reports/default?school={SCHOOL_ID}&report=paid-access-school&year=2025"

st.title("🚀 Tezkor eMaktab Monitoring")

# Cookie kiritish
cookie = st.text_area("Cookie-ni kiriting (F12 orqali olingan):")

if st.button("Ma'lumotlarni yashin tezligida olish"):
    if cookie:
        headers = {
            'User-Agent': 'Mozilla/5.0',
            'Cookie': cookie,
            'Accept': 'application/json' # Biz serverdan HTML emas, JSON so'rayapmiz
        }
        
        # Sahifani so'raymiz
        res = requests.get(REPORT_URL, headers=headers)
        
        # Agar eMaktab JSON formatda javob bersa (ba'zan shunday bo'ladi):
        try:
            data = res.json()
            # Bu yerda jadvalni yuklamasdan, JSON ichidagi raqamlarni chiqarish mumkin
            st.success("Ma'lumotlar server bazasidan olindi!")
            st.json(data) 
        except:
            # Agar JSON bermasa, HTML ichidan eng muhim raqamlarni bitta qatorda ajratib olamiz
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(res.content, 'html.parser')
            
            # Rasmda ko'ringan umumiy raqamlarni ajratib olish (Umumiy %, o'quvchilar soni)
            # Bu jadvalni yuklamasdan tepada turadigan xulosani olish
            summary = soup.find('div', class_='report-summary') 
            if summary:
                st.info(f"Xulosa: {summary.get_text(strip=True)}")
            else:
                st.warning("Jadval yuklanmadi, lekin sahifa kodi olindi. Brauzerda sessiyangiz faolligini tekshiring.")
    else:
        st.error("Cookie bo'sh!")
