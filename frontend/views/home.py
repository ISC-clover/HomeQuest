import streamlit as st
import os
import base64

def page_home():
    # --- 背景画像を設定（既存の処理をそのまま保持） ---
    img_path = os.path.normpath(os.path.join(os.path.dirname(__file__), '..', 'static', 'images', 'background.png'))
    if os.path.exists(img_path):
        with open(img_path, 'rb') as f:
            img_b64 = base64.b64encode(f.read()).decode()
        img_url = f"data:image/png;base64,{img_b64}"
    else:
        # フォールバック
        img_url = '/frontend/static/images/background.png'

    # --- カスタムCSS（背景設定 ＋ 新レイアウト用のボタン設定） ---
    st.markdown(f"""
        <style>
        /* 既存の背景・オーバーレイ設定 */
        .stApp {{
            background-image: url('{img_url}');
            background-size: 90% auto;
            background-repeat: no-repeat;
            background-position: 100% top;
            background-attachment: fixed;
            background-color: #f8f8f8;
        }}
        .stApp > .main {{
            background: rgba(255,255,255,0.85);
            padding: 1rem;
            border-radius: 8px;
        }}
        
        /* 新規: 下部の3つのボタンを四角く大きくするための設定 */
        div[data-testid="column"] button {{
            height: 120px;
            font-size: 18px;
            font-weight: bold;
            border-radius: 15px;
        }}
        
        /* 新規: 右上の設定ボタンだけは通常サイズに戻す */
        .settings-btn button {{
            height: auto !important;
            padding: 5px 15px !important;
        }}
        </style>
        """, unsafe_allow_html=True)

    # --- ユーザー情報の取得（既存の処理をそのまま保持） ---
    me = st.session_state.api.get_me()
    user_name = me.get('user_name', 'ゲスト') if "error" not in me else 'ゲスト'

    st.write("") # 余白

    # --- 中央エリア：ステータスバー、キャラクター、吹き出し (d) ---
    col_left, col_center, col_right = st.columns([1, 6, 1]) # 中央を広く取るために比率を調整
    
    with col_left:
        # ラフ案左側の縦棒（HPとEXPのプログレスバー）
        st.caption("❤️ HP")
        st.progress(80) # 仮の数値
        st.caption("✨ EXP")
        st.progress(45) # 仮の数値

    with col_center:
        # 吹き出し (d)
        st.markdown("""
            <div style="border: 2px solid #ccc; border-radius: 15px; padding: 10px; margin-bottom: 15px; text-align: center; background-color: rgba(255,255,255,0.9); color: black;">
                「今日もクエストがんばろう！」
            </div>
        """, unsafe_allow_html=True)

        # --- キャラクター画像を表示 ---
        # 画像の正しいパスを取得
        char_img_path = os.path.normpath(os.path.join(os.path.dirname(__file__), '..', 'static', 'images', 'character.png'))
        
        # 画像が存在するか確認してから表示
        if os.path.exists(char_img_path):
            # use_container_width=True で、中央カラムの幅いっぱいに大きく表示します
            st.image(char_img_path, width=900)
        else:
            st.error("勇者はお出かけ中のようです...")
        
        # ユーザー名を表示
        st.markdown(f"<p style='text-align: center; margin-top: 10px; font-weight: bold;'>{user_name}</p>", unsafe_allow_html=True)

    st.write("")
    st.write("---") # 地面のような区切り線

    # --- 下部：メインメニューボタン（3列配置） ---
    menu_col1, menu_col2, menu_col3 = st.columns(3)

    with menu_col1:
        if st.button("🛡️ グループ", use_container_width=True):
            st.session_state.current_page = "groups"
            st.rerun()

    with menu_col2:
        # クエスト（メイン機能っぽく目立たせるため type="primary" にしています）
        if st.button("⚔️ クエスト", type="primary", use_container_width=True):
            st.session_state.current_page = "quests"
            st.rerun()

    with menu_col3:
        if st.button("🎁 ショップ", use_container_width=True):
            st.session_state.current_page = "shop"
            st.rerun()

    # --- サイドバーにログアウト（既存の処理をそのまま保持） ---
    with st.sidebar:
        st.write(f"ログイン中: {user_name}")
        if st.button("ログアウト"):
            st.session_state.is_logged_in = False
            st.session_state.api.token = None
            st.session_state.current_page = "home"
            st.rerun()