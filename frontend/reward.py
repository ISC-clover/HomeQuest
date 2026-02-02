import streamlit as st
import os

def show_reward_screen():
    st.markdown("""
        <style>
        .block-container {
            background-image: none !important;
            background-color: #DAA520 !important;
        }
        </style>
    """, unsafe_allow_html=True)
    
    # --- ヘッダーエリア ---
    col_left, col_right = st.columns([2, 8])
    
    with col_left:
        st.markdown('<span id="back-btn"></span>', unsafe_allow_html=True)
        if st.button("⬅️", key="back_reward"):
            st.session_state.page = "home"
            st.rerun()
            
    with col_right:
        st.markdown("<h1 style='color: white; font-size: 28px; margin-top: 10px;'>💰 ほうび</h1>", unsafe_allow_html=True)

    st.write("---")
    st.write("よくやった！褒美を受け取るがよい！")
    
    if os.path.exists("img/reward_btn.png"):
        c1, c2, c3 = st.columns([1, 2, 1])
        with c2:
            st.image("img/reward_btn.png", use_container_width=True)