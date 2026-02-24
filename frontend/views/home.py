import streamlit as st

def page_home():
    # 背景画像を設定（画像ファイルをワークスペースの uploads/home_bg.png に置いてください）
    st.markdown(
        """
        <style>
        .stApp {
            background-image: url('/frontend/static/images/background.png');
            background-size: cover;
            background-position: center;
            background-attachment: fixed;
        }
        /* コンテンツを読みやすくするための半透明のオーバーレイ */
        .stApp > .main {
            background: rgba(255,255,255,0.85);
            padding: 1rem;
            border-radius: 8px;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    st.title("🏰 ホーム")
    
    # ユーザー情報の取得
    me = st.session_state.api.get_me()
    if "error" not in me:
        st.write(f"ようこそ、 **{me['user_name']}** (ID: {me['id']})")
    
    st.divider()
    
    # --- メニューボタン ---
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🛡️ グループ", use_container_width=True):
            st.session_state.current_page = "groups"
            st.rerun()
            
        if st.button("📜 クエスト", use_container_width=True):
            st.session_state.current_page = "quests"
            st.rerun()
            
    with col2:
        if st.button("💰 ショップ", use_container_width=True):
            st.session_state.current_page = "shop"
            st.rerun()

    # --- サイドバーにログアウト ---
    with st.sidebar:
        st.write(f"ログイン中: {me.get('user_name', '')}")
        if st.button("ログアウト"):
            st.session_state.is_logged_in = False
            st.session_state.api.token = None
            st.session_state.current_page = "home"
            st.rerun()