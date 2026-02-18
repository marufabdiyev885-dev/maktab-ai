# --- 6. AI MULOQOT (TOZALANGAN VARIANT) ---
if menu == "🤖 AI Muloqot":
    st.title("🤖 Maktab AI yordamchisi")
    if "messages" not in st.session_state: 
        st.session_state.messages = []
    
    # Oldingi xabarlarni chiqarish
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]): 
            st.markdown(msg["content"])

    if savol := st.chat_input("Ism yozing...", key="ai_chat_input_v4"):
        st.session_state.messages.append({"role": "user", "content": savol})
        with st.chat_message("user"): 
            st.markdown(savol)
        
        with st.chat_message("assistant"):
            q_lower = savol.lower().strip()
            suhbat_sozlari = ["salom", "yaxshi", "rahmat", "ahvoling", "qalay", "nima gap", "ok"]
            
            # Bazadan qidirish natijasi uchun vaqtinchalik o'zgaruvchi
            qidiruv_matni = ""
            found_df = None
            
            # 1. Qidiruv mantiqi (Faqat ism bo'lsa)
            if not any(x in q_lower for x in suhbat_sozlari) and len(q_lower) >= 3:
                target_sheets = sheets_baza
                search_term = savol
                
                if "o'qituvchi" in q_lower or "ustoz" in q_lower:
                    target_sheets = {k: v for k, v in sheets_baza.items() if any(x in k.lower() for x in ["o'qituvchi", "pedagog"])}
                    search_term = q_lower.replace("o'qituvchi", "").replace("ustoz", "").strip()
                elif "o'quvchi" in q_lower or "sinf" in q_lower:
                    target_sheets = {k: v for k, v in sheets_baza.items() if any(x in k.lower() for x in ["o'quvchi", "sinf"])}
                    search_term = q_lower.replace("o'quvchi", "").replace("sinf", "").strip()

                for key, df in target_sheets.items():
                    mask = df.apply(lambda row: row.astype(str).str.contains(search_term, case=False, na=False).any(), axis=1)
                    res_df = df[mask]
                    if not res_df.empty:
                        qidiruv_matni = f"🔍 Bazadan topildi ({key}):"
                        found_df = res_df
                        break

            # 2. AI Javobi
            if found_df is not None:
                st.markdown(qidiruv_matni)
                st.dataframe(found_df, use_container_width=True)
                st.session_state.messages.append({"role": "assistant", "content": qidiruv_matni})
            else:
                try:
                    chat_completion = client.chat.completions.create(
                        messages=[{"role": "system", "content": f"Sen {MAKTAB_NOMI} AI yordamchisisan. Samimiy javob ber."},
                                 {"role": "user", "content": savol}],
                        model="llama-3.3-70b-versatile",
                    )
                    javob = chat_completion.choices[0].message.content
                    st.markdown(javob)
                    st.session_state.messages.append({"role": "assistant", "content": javob})
                except:
                    st.error("AI hozirda band.")

# --- 7. MONITORING (O'ZGARISHSIZ) ---
elif menu == "📊 Jurnal Monitoringi":
    # Monitoring kodi bu yerda (Section 7 dagi kod) faqat shu bo'lim tanlanganda ishlaydi.
