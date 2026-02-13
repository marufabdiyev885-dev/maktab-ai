with st.chat_message("assistant"):
        s = savol.lower()
        
        # 1. BAZADAN QIDIRUV
        mask = df.apply(lambda row: row.astype(str).str.contains(savol, case=False, na=False).any(), axis=1)
        res = df[mask]
        
        # 2. JAVOBNI SHAKLLANTIRISH (AI suhbatini simulyatsiya qilish)
        if not res.empty:
            st.success(f"Ma'rufjon aka, bazadan {len(res)} ta ma'lumot topdim!")
            st.dataframe(res)
            
            # AI uslubida xulosa (bazadagi ma'lumotga qarab)
            if len(res) == 1:
                javob = f"Mana, siz so'ragan {savol} haqida barcha ma'lumotlar. Yana kimni qidirib beray?"
            else:
                javob = f"Ro'yxatda bir nechta {savol} bor ekan. Jadvaldan o'zingizga keraklisini tanlab oling."
        else:
            # Agar bazada bo'lmasa, AI o'zidan gapiradi
            salomlar = ["salom", "assalom", "qalay", "yaxshimi", "ishlar", "nima gap"]
            if any(word in s for word in salomlar):
                javob = "Vaalaykum assalom, Ma'rufjon aka! Kayfiyatlar qalay? Maktab bazasi bilan ishlashga tayyorman, buyuravering!"
            else:
                javob = f"Afsuski, bazada '{savol}' bo'yicha ma'lumot yo'q ekan. Balki ismda xato bordir? Yoki boshqa narsa so'raysizmi?"

        st.markdown(javob)
        st.session_state.messages.append({"role": "assistant", "content": javob})
