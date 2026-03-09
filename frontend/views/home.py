import streamlit as st
import os
import base64

def page_home():
    # --- 画像のベース64変換関数 ---
    def get_base64_img(path):
        if os.path.exists(path):
            with open(path, 'rb') as f:
                return base64.b64encode(f.read()).decode()
        return None

    # 合成済みの背景画像を読み込み
    bg_path = os.path.normpath(os.path.join(os.path.dirname(__file__), '..', 'static', 'images', 'background.png'))
    bg_b64 = get_base64_img(bg_path)

    # --- CSSで要素の位置を強制固定 ---
    st.markdown(f"""
        <style>
        /* 画面全体の固定 */
        .stApp {{
            background-image: url('data:image/png;base64,{bg_b64}');
            background-size: cover;
            background-position: center;
            height: 100vh;
            width: 100vw;
            overflow: hidden !important;
        }}
        .stApp > .main {{ background: transparent; }}

        /* ★ 1. 吹き出しを頭の上に固定 */
        .speech-bubble {{
            position: fixed;
            top: 10vh;
            left: 50%;
            transform: translateX(-50%);
            background-color: rgba(255, 255, 255, 0.85);
            border: 3px solid #333;
            border-radius: 15px;
            padding: 15px;
            text-align: center;
            color: #111;
            font-size: 1.2rem;
            font-weight: bold;
            width: 80%;
            max-width: 600px;
            box-shadow: 2px 4px 10px rgba(0,0,0,0.3);
            z-index: 50;
        }}

        /* ★ 2. ヘッダー部を画面「上部」に固定 */
        div[data-testid="stHorizontalBlock"]:has(.header-marker) {{
            position: fixed;
            top: 2vh;
            left: 50%;
            transform: translateX(-50%);
            width: 95%;
            z-index: 100;
        }}

        /* ★ 3. ネームプレートを固定 */
        .name-plate {{
            position: fixed;
            bottom: 15vh;
            left: 50%;
            transform: translateX(-50%);
            font-weight: bold;
            color: white;
            text-shadow: 2px 2px 4px black, -1px -1px 4px black;
            font-size: 1.3rem;
            z-index: 50;
            width: 100%;
            text-align: center;
        }}

        /* ★ 4. メニューボタン群を画面の「さらに下」に固定 */
        div[data-testid="stHorizontalBlock"]:has(.menu-marker) {{
            position: fixed;
            bottom: 2vh; /* ←ここを5vhから2vhにしてさらに下げました！ */
            left: 50%;
            transform: translateX(-50%);
            width: 90%;
            max-width: 800px;
            z-index: 100;
        }}

        /* RPG風メインボタンの装飾 */
        button[kind="primary"] {{
            height: 60px !important;
            font-size: 18px !important;
            font-weight: bold;
            border-radius: 12px;
            background-color: rgba(0, 40, 60, 0.8) !important;
            border: 2px solid #00d4ffaa !important;
            color: white !important;
            box-shadow: 0px 4px 15px rgba(0,0,0,0.6);
            transition: 0.3s;
        }}
        
        button[kind="primary"]:hover {{
            background-color: rgba(0, 100, 150, 0.9) !important;
            border-color: #ffffff !important;
            transform: translateY(-2px);
        }}

        /* 余計な要素を隠す */
        [data-testid="stHeader"], [data-testid="stImageToolbar"] {{
            display: none !important;
        }}
        </style>
    """, unsafe_allow_html=True)

    # --- ユーザー情報の取得 ---
    me = st.session_state.api.get_me()
    user_name = me.get('user_name', 'ゲスト') if "error" not in me else 'ゲスト'

    # --- ① 上部：ヘッダー（ログイン・ログアウト） ---
    h_left, h_right = st.columns([4, 1])
    with h_left:
        st.markdown(f"<span class='header-marker'></span><p style='color: white; text-shadow: 2px 2px 4px black; font-size: 1.2rem; margin-top: 10px; margin-left: 10px;'>👤 <b>{user_name}</b> ログイン中</p>", unsafe_allow_html=True)
    with h_right:
        if st.button("ログアウト", key="logout_top"):
            st.session_state.is_logged_in = False
            st.session_state.current_page = "home"
            st.rerun()

    # --- ② 吹き出し ---
    st.markdown(f'<div class="speech-bubble">「今日もクエストがんばろう、{user_name}！」</div>', unsafe_allow_html=True)

    # --- ③ ネームプレート ---
    st.markdown(f'<div class="name-plate">{user_name}</div>', unsafe_allow_html=True)

    # --- ④ 下部：メインメニュー ---
    # ★ポイント：3つのカラムすべてに同じ目印を置くことで、強制的に高さを揃えます！
    menu_col1, menu_col2, menu_col3 = st.columns(3)
    
    with menu_col1:
        st.markdown("<div class='menu-marker' style='display:none;'></div>", unsafe_allow_html=True)
        if st.button("🛡️ グループ", type="primary", use_container_width=True, key="btn_grp"):
            st.session_state.current_page = "groups"; st.rerun()
            
    with menu_col2:
        st.markdown("<div class='menu-marker' style='display:none;'></div>", unsafe_allow_html=True)
        if st.button("⚔️ クエスト", type="primary", use_container_width=True, key="btn_qst"):
            st.session_state.current_page = "quests"; st.rerun()
            
    with menu_col3:
        st.markdown("<div class='menu-marker' style='display:none;'></div>", unsafe_allow_html=True)
        if st.button("🎁 ショップ", type="primary", use_container_width=True, key="btn_shp"):
            st.session_state.current_page = "shop"; st.rerun()