import streamlit as st

def show_setting_screen():
    # --- ヘッダーエリア ---
    col_left, col_right = st.columns([2, 8])
    
    with col_left:
        st.markdown('<span id="back-btn"></span>', unsafe_allow_html=True)
        if st.button("⬅️", key="back_setting"):
            st.session_state.page = "home"
            st.rerun()
            
    with col_right:
        st.markdown("<h1 style='color: white; font-size: 28px; margin-top: 10px;'>⚙️ 設定</h1>", unsafe_allow_html=True)
    
    st.write("---")
    
    st.markdown("<div style='color:white; background:rgba(0,0,0,0.5); padding:10px; border-radius:10px;'>", unsafe_allow_html=True)
    st.write("▼ ユーザー設定")
    user_name = st.text_input("勇者の名前", value=st.session_state.get("user_name", "勇者"))
    st.markdown("</div>", unsafe_allow_html=True)

    st.write("")
    if st.button("✅ 保存する", use_container_width=True):
        st.session_state.user_name = user_name
        st.success("保存しました！")