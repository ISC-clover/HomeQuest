import streamlit as st
import os
import base64

def page_home():
    # 背景画像を設定（画像をBase64で埋め込み、配布構成に依存しないようにする）
    img_path = os.path.normpath(os.path.join(os.path.dirname(__file__), '..', 'static', 'images', 'background.png'))
    if os.path.exists(img_path):
        with open(img_path, 'rb') as f:
            img_b64 = base64.b64encode(f.read()).decode()
        img_url = f"data:image/png;base64,{img_b64}"
    else:
        # フォールバック（ファイルが見つからなければ通常のパスを指定）
        img_url = '/frontend/static/images/background.png'

    st.markdown(f"""
        <style>
        .stApp {{
            background-image: url('{img_url}');
            /* 画像全体を見せる（余白が出る場合あり） */
            background-size: contain;
            background-repeat: no-repeat;
            background-position: center top;
            background-attachment: fixed;
            background-color: #f8f8f8;
            min-height: 100vh;
        }}
        /* コンテンツを読みやすくするための半透明のオーバーレイ（薄め） */
        .stApp > .main {{
            background: rgba(255,255,255,0.55);
            padding: 1rem;
            border-radius: 8px;
        }}
        </style>
        """, unsafe_allow_html=True)

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