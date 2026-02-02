import streamlit as st
import os
import base64
import quest
import reward
import setting

# --- 1. ページ設定 ---
st.set_page_config(page_title="Home Quest", layout="centered")

# --- 画像読み込み関数 ---
def get_base64(bin_file):
    with open(bin_file, 'rb') as f:
        data = f.read()
    return base64.b64encode(data).decode()

IMG_DIR = "img"

# ==========================================
# 🎮 カスタマイズ設定
# ==========================================

# ■ 勇者の位置
HERO_WIDTH = 300
HERO_TOP   = 0    

# ■ ボタンエリアの位置（画面上からの距離）
BTN_AREA_TOP = 330 

# ■ ボタンサイズ
BTN_MAIN_WIDTH  = 130
BTN_MAIN_HEIGHT = 130
BTN_SIDE_WIDTH  = 90
BTN_SIDE_HEIGHT = 90
BTN_SIDE_OFFSET = 30    

# ■ ヘッダーボタン（設定・戻る）のサイズ
BTN_HEADER_WIDTH = 50

# ==========================================

# 画像読み込み
bg_b64 = ""
if os.path.exists(f"{IMG_DIR}/background.png"):
    bg_b64 = get_base64(f"{IMG_DIR}/background.png")

btn1_b64 = ""
if os.path.exists(f"{IMG_DIR}/battle_btn.png"):
    btn1_b64 = get_base64(f"{IMG_DIR}/battle_btn.png")

btn2_b64 = ""
if os.path.exists(f"{IMG_DIR}/reward_btn.png"):
    btn2_b64 = get_base64(f"{IMG_DIR}/reward_btn.png")

btn_setting_b64 = ""
if os.path.exists(f"{IMG_DIR}/setting_btn.png"):
    btn_setting_b64 = get_base64(f"{IMG_DIR}/setting_btn.png")

btn_back_b64 = ""
if os.path.exists(f"{IMG_DIR}/back_btn.png"):
    btn_back_b64 = get_base64(f"{IMG_DIR}/back_btn.png")

# --- CSS設定 ---
st.markdown(f"""
    <style>
    .stApp {{ background-color: #000000; }}
    
    .block-container {{
        max-width: 380px;
        height: 640px;
        padding-top: 10px !important; /* 上の隙間を極限まで減らす */
        padding-bottom: 0 !important;
        padding-left: 1rem !important;
        padding-right: 1rem !important;
        margin: auto;
        border: 2px solid #333;
        border-radius: 20px;
        background-color: #222;
        background-image: url("data:image/png;base64,{bg_b64}");
        background-size: cover;
        background-position: center;
        background-repeat: no-repeat;
        position: relative;
    }}
    
    header, footer {{visibility: hidden;}}

    /* 勇者の位置 */
    .hero-container {{
        position: absolute;
        top: {HERO_TOP}px;
        left: 0;
        right: 0;
        margin: auto;
        width: {HERO_WIDTH}px;
        text-align: center;
        pointer-events: none; 
        z-index: 0;
    }}
    
    .hero-img {{
        width: 100%;
    }}

    /* ボタンエリアの位置 */
    .button-area-container {{
        position: absolute;
        top: {BTN_AREA_TOP}px;
        left: 0; 
        right: 0;
        width: 100%;
        padding-left: 1rem;
        padding-right: 1rem;
    }}

    /* ボタン共通 */
    .stButton > button {{
        border: none !important;
        background-color: transparent !important;
        background-size: cover !important;
        background-repeat: no-repeat !important;
        transition: transform 0.1s;
        display: block;
        margin-left: auto;
        margin-right: auto;
    }}
    .stButton > button:active {{ transform: scale(0.95); }}
    
    h1 {{ padding-top: 0 !important; margin-top: 0 !important; }}

    /* --- 各ボタンのデザイン --- */
    div.element-container:has(#battle-btn) + div button {{
        background-image: url("data:image/png;base64,{btn1_b64}");
        width: {BTN_MAIN_WIDTH}px !important;
        height: {BTN_MAIN_HEIGHT}px !important;
        color: transparent !important;
    }}

    div.element-container:has(#reward-btn) + div button {{
        background-image: url("data:image/png;base64,{btn2_b64}");
        width: {BTN_SIDE_WIDTH}px !important;
        height: {BTN_SIDE_HEIGHT}px !important;
        color: transparent !important;
    }}

    /* 設定ボタン */
    div.element-container:has(#setting-btn) + div button {{
        background-image: url("data:image/png;base64,{btn_setting_b64}");
        background-color: { 'transparent' if btn_setting_b64 else 'rgba(255,255,255,0.3)' } !important;
        border-radius: 50% !important;
        width: {BTN_HEADER_WIDTH}px !important;
        height: {BTN_HEADER_WIDTH}px !important;
        color: transparent !important;
        /* 右に寄せる補正 */
        margin-right: -10px !important; 
    }}

    /* 戻るボタン */
    div.element-container:has(#back-btn) + div button {{
        background-image: url("data:image/png;base64,{btn_back_b64}");
        background-color: { 'transparent' if btn_back_b64 else 'rgba(255,255,255,0.3)' } !important;
        border-radius: 50% !important;
        width: {BTN_HEADER_WIDTH}px !important;
        height: {BTN_HEADER_WIDTH}px !important;
        color: { 'transparent' if btn_back_b64 else 'white' } !important;
        /* 左に寄せる補正 */
        margin-left: -10px !important;
    }}
    
    </style>
""", unsafe_allow_html=True)

# --- 状態管理 ---
if "page" not in st.session_state:
    st.session_state.page = "home"

# ==========================================
#  メイン画面 (Home)
# ==========================================
if st.session_state.page == "home":
    
    # --- ヘッダー（確実なカラム配置） ---
    # [空白(7) : 設定(1)] の比率で、強制的に右端へ追いやる
    c_void, c_set = st.columns([7, 1.2]) 
    
    with c_set:
        st.markdown('<span id="setting-btn"></span>', unsafe_allow_html=True)
        label = "" if btn_setting_b64 else "⚙"
        if st.button(label, key="btn_setting"):
            st.session_state.page = "setting"
            st.rerun()

    # --- 勇者エリア ---
    if os.path.exists(f"{IMG_DIR}/brave.png"):
        st.markdown(f"""
            <div class="hero-container">
                <img src="data:image/png;base64,{get_base64(f"{IMG_DIR}/brave.png")}" class="hero-img">
            </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
            <div class="hero-container" style="color:white; border:1px dashed white; padding-top:80px;">
                勇者画像なし
            </div>
        """, unsafe_allow_html=True)


    # --- ボタンエリア ---
    st.markdown(f'<div style="margin-top: {BTN_AREA_TOP}px;"></div>', unsafe_allow_html=True)

    col_left, col_center, col_right = st.columns([1, 1.2, 1])

    # ▼ 左エリア
    with col_left:
        st.markdown(f'<div style="height: {BTN_SIDE_OFFSET}px;"></div>', unsafe_allow_html=True)

    # ▼ 中央エリア
    with col_center:
        st.markdown('<span id="battle-btn"></span>', unsafe_allow_html=True)
        if st.button("戦", key="btn_battle"):
            st.session_state.page = "quest"
            st.rerun()

    # ▼ 右エリア
    with col_right:
        st.markdown(f'<div style="height: {BTN_SIDE_OFFSET}px;"></div>', unsafe_allow_html=True)
        st.markdown('<span id="reward-btn"></span>', unsafe_allow_html=True)
        if st.button("報", key="btn_reward"):
            st.session_state.page = "reward"
            st.rerun()

# ==========================================
#  各画面の呼び出し
# ==========================================
elif st.session_state.page == "quest":
    quest.show_quest_screen()

elif st.session_state.page == "reward":
    reward.show_reward_screen()

elif st.session_state.page == "setting":
    setting.show_setting_screen()