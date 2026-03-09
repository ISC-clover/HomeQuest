from datetime import datetime as dt
import streamlit as st
import base64

#時間をわかりやすく変換する関数
def format_time(iso_str):
    if not iso_str: return "日時不明"
    try:
        parsed = dt.fromisoformat(str(iso_str).replace('Z', '+00:00'))
        local_time = parsed.astimezone()
        return local_time.strftime("%Y/%m/%d %H:%M")
    except:
        return str(iso_str)[:16].replace('T', ' ')

def shop_css():
    # 指定の暗いグレー色を背景として使用
    bg_css = "#2d2d2d"

    # === 🌟 ファンタジーCSS注入 ===
    st.markdown(f"""
    <style>
        /* 全体背景: 暗いグレー背景を使用 */
        [data-testid="stAppViewContainer"] {{
            background-color: {bg_css};
            background-image: none;
            color: #ffffff;
        }}
        [data-testid="stHeader"] {{
            background-color: rgba(0,0,0,0);
        }}
        
        /* タイトル看板 */
        .main-title {{
            background-color: rgba(62, 39, 35, 0.85);
            border: 5px solid #8d6e63;
            border-radius: 15px;
            padding: 20px;
            text-align: center;
            margin-bottom: 25px;
            box-shadow: 0 10px 20px rgba(0,0,0,0.5);
        }}
        .main-title h1 {{
            margin: 0;
            color: #fff8e1;
            font-family: 'Courier New', Courier, monospace;
            font-weight: bold;
            text-shadow: 2px 2px 2px rgba(0,0,0,0.5);
        }}

        /* タブ（お店の看板風） */
        .stTabs [data-baseweb="tab-list"] {{
            gap: 8px;
            background-color: rgba(93, 64, 55, 0.8);
            padding: 10px 10px 0 10px;
            border-radius: 10px 10px 0 0;
        }}
        .stTabs [data-baseweb="tab"] {{
            background-color: rgba(141, 110, 99, 0.6);
            border-radius: 5px 5px 0 0;
            color: #fff;
            padding: 10px 20px;
            border: none;
        }}
        .stTabs [aria-selected="true"] {{
            background-color: #fff8e1 !important;
            color: #3e2723 !important;
            font-weight: bold;
        }}

        /* 所持ポイント（羊皮紙風） */
        .point-banner {{
            background-color: rgba(255, 248, 225, 0.9);
            border: 3px solid #bcaaa4;
            border-radius: 5px;
            padding: 15px;
            text-align: center;
            margin-bottom: 20px;
            box-shadow: inset 0 0 15px rgba(141, 110, 99, 0.5);
            color: #3e2723;
        }}

        /* 商品棚の枠組み */
        .shelf-container {{
            background-color: rgba(43, 29, 26, 0.8);
            border: 8px solid #5d4037;
            padding: 20px;
            border-radius: 10px;
            margin-top: 10px;
            backdrop-filter: blur(3px);
        }}

        /* 商品カード */
        .item-card {{
            background-color: rgba(215, 204, 200, 0.95);
            border: 2px solid #a1887f;
            border-radius: 8px;
            padding: 15px;
            color: #3e2723;
            height: 100%;
            box-shadow: 2px 2px 5px rgba(0,0,0,0.3);
        }}
        
        /* 履歴（掲示板風） */
        .history-card {{
            background-color: rgba(255, 248, 225, 0.1);
            border-left: 5px solid #8d6e63;
            padding: 12px;
            margin-bottom: 8px;
            color: #fff8e1;
        }}

        /* ボタンの調整 */
        .stButton button {{
            border-radius: 5px;
            color: white !important;
            background-color: #4CAF50 !important;
            border-color: #4CAF50 !important;
        }}
        .stButton button:hover {{
            background-color: #45a049 !important;
            border-color: #45a049 !important;
        }}
        .stButton button:disabled {{
            background-color: #cccccc !important;
            color: #666666 !important;
        }}
    </style>
    """, unsafe_allow_html=True)

def back_to_home():
        st.divider()
        if st.button("🏠 ホームに戻る", key="back_home_bot"):
            st.session_state.current_page = "home"
            st.rerun()