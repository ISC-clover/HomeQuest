# ==========================================
# ページ全体の基本設定
# ==========================================
SET_PAGE_CONFIG = {
    "page_title": "HomeQuest",
    "page_icon": "🏠",
    "layout": "wide",
    "initial_sidebar_state": "expanded",
}

# ==========================================
# 余計な表示を消す・見た目を整えるCSS
# ==========================================
HIDE_ST_STYLE = """
<style>
    /* Deployボタンを消す */
    .stAppDeployButton { display: none !important; }
    
    /* 右上の三点リーダーとその周りを消す */
    #MainMenu { display: none !important; }
    [data-testid="stHeaderActionElements"] { display: none !important; }
    
    /* 画面一番下の「Made with Streamlit」を消す */
    footer { display: none !important; }
    
    /* 「Enterを押して適用」のヒント文字を消す */
    [data-testid="InputInstructions"] { display: none !important; }

</style>
"""