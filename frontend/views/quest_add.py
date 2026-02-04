import streamlit as st

def page_quest_add():
    st.title("📜 新規クエスト追加")
    st.info("🚧 工事中：ここにクエスト作成フォームが入ります")
    
    # 戻るボタン
    if st.button("詳細画面に戻る"):
        st.session_state.current_page = "group_detail"
        st.rerun()