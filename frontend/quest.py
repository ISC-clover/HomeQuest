import streamlit as st
import os
import base64
import textwrap

IMG_DIR = "img"

# ==========================================
#  【画像ファイル設定】
# ==========================================
FILE_HEADER = "quest_header.png"
FILE_FRAME  = "quest_frame.png"
FILE_FOOTER = "quest_footer.png"
FILE_BACK   = "back_btn.png"

# ==========================================
#  【位置調整】
# ==========================================
BOARD_MARGIN_TOP = -30
FOOTER_MARGIN_TOP = -15  
APP_WIDTH = 380          
FRAME_HEIGHT = 450       

# ==========================================

def get_base64(bin_file):
    try:
        with open(bin_file, 'rb') as f:
            data = f.read()
        return base64.b64encode(data).decode()
    except FileNotFoundError:
        return ""

def show_quest_screen():
    # --- 画像読み込み ---
    header_b64   = get_base64(os.path.join(IMG_DIR, FILE_HEADER))
    frame_b64    = get_base64(os.path.join(IMG_DIR, FILE_FRAME))
    footer_b64   = get_base64(os.path.join(IMG_DIR, FILE_FOOTER))
    back_btn_b64 = get_base64(os.path.join(IMG_DIR, FILE_BACK))

    if "quest_tab" not in st.session_state:
        st.session_state.quest_tab = "active"

    # --- CSS適用 ---
    st.markdown(textwrap.dedent(f"""
    <style>
    /* 全体の位置調整 */
    .block-container {{
        max-width: {APP_WIDTH}px;
        padding-top: 0rem !important;
        padding-bottom: 0rem !important;
        margin-top: -40px !important; 
        margin: auto;
    }}
    
    [data-testid="stHorizontalBlock"] {{
        gap: 0.2rem !important;
    }}
    
    div.row-widget.stButton {{ margin-bottom: 0px !important; }}

    /* ============================================================
       【1】基本ルール（通常ボタン＝タブ）：
       少し太く(55px)して、文字サイズも少し上げます
       ============================================================ */
    div.stButton > button[data-testid="stBaseButton-secondary"] {{
        background-image: url("data:image/png;base64,{header_b64}") !important;
        background-size: 100% 100% !important;
        background-repeat: no-repeat !important;
        background-color: transparent !important;
        border: none !important;
        box-shadow: none !important;
        
        color: #5d4037 !important;
        font-weight: bold !important;
        font-size: 14px !important; /* 文字も少し大きく */
        
        height: 55px !important;      /* ★高さを55pxにアップ */
        line-height: 55px !important; /* 行間も合わせる */
        padding: 0 !important;        
        margin: 0 !important;
        width: 100% !important;       
    }}

    /* ============================================================
       【2】例外ルール（重要ボタン＝戻るボタン）：
       ============================================================ */
    div.stButton > button[data-testid="stBaseButton-primary"] {{
        background-image: url("data:image/png;base64,{back_btn_b64}") !important;
        background-size: contain !important;
        background-position: left center !important;
        background-repeat: no-repeat !important;
        background-color: transparent !important;
        border: none !important;
        box-shadow: none !important;
        
        color: transparent !important;
        width: 60px !important;
        height: 50px !important;
        padding-top: 0px !important;
    }}
    
    div.stButton > button:active, div.stButton > button:focus {{
        background-color: transparent !important;
        border: none !important;
        box-shadow: none !important;
    }}

    /* メインボード */
    .board-container {{
        width: 100%;
        height: {FRAME_HEIGHT}px;
        background-image: url("data:image/png;base64,{frame_b64}");
        background-size: 100% 100%;
        margin-top: {BOARD_MARGIN_TOP}px;
        position: relative;
    }}

    /* フッター */
    .footer-container {{
        width: 250px;
        height: 60px;
        background-image: url("data:image/png;base64,{footer_b64}");
        background-size: contain;
        background-repeat: no-repeat;
        background-position: center;
        margin: {FOOTER_MARGIN_TOP}px auto 0 auto;
        text-align: center;
        line-height: 60px;
        color: #5d4037;
        font-weight: bold;
    }}
    </style>
    """), unsafe_allow_html=True)

    # ============================================================
    #  レイアウト作成
    # ============================================================

    # --- 1行目：戻るボタン ---
    row1_col1, row1_dummy = st.columns([1, 5])
    with row1_col1:
        if st.button("戻", key="btn_back", type="primary"):
            st.session_state.page = "home"
            st.rerun()

    # --- 2行目：タブボタン ---
    row2_col1, row2_col2, row2_col3 = st.columns(3)
    
    current = st.session_state.quest_tab

    # ★ここが重要変更点！ use_container_width=True をつけました ★
    with row2_col1:
        label = "▼クエスト" if current == "active" else "クエスト"
        if st.button(label, key="tab_1", use_container_width=True):
            st.session_state.quest_tab = "active"
            st.rerun()

    with row2_col2:
        label = "▼判定中" if current == "pending" else "判定中"
        if st.button(label, key="tab_2", use_container_width=True):
            st.session_state.quest_tab = "pending"
            st.rerun()

    with row2_col3:
        label = "▼履歴" if current == "history" else "履歴"
        if st.button(label, key="tab_3", use_container_width=True):
            st.session_state.quest_tab = "history"
            st.rerun()

    # --- ボードエリア ---
    st.markdown(f'<div class="board-container"></div>', unsafe_allow_html=True)

    # --- フッター ---
    st.markdown(f'<div class="footer-container">+クエスト追加+</div>', unsafe_allow_html=True)

if __name__ == "__main__":
    show_quest_screen()