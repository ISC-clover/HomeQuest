from datetime import datetime as dt
import streamlit as st

#時間をわかりやすく変換する関数
def format_time(iso_str):
    if not iso_str: return "日時不明"
    try:
        parsed = dt.fromisoformat(str(iso_str).replace('Z', '+00:00'))
        local_time = parsed.astimezone()
        return local_time.strftime("%Y/%m/%d %H:%M")
    except:
        return str(iso_str)[:16].replace('T', ' ')

def back_to_home():
        st.divider()
        if st.button("🏠 ホームに戻る", key="back_home_bot"):
            st.session_state.current_page = "home"
            st.rerun()