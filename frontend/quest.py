import streamlit as st

def show_quest_screen():
    # --- ヘッダーエリア（左上ボタン配置） ---
    # 左(2):右(8) の割合で分割
    col_left, col_right = st.columns([2, 8])
    
    with col_left:
        # ここに main.py で作ったデザイン(CSS)を適用する目印をつける
        st.markdown('<span id="back-btn"></span>', unsafe_allow_html=True)
        # 戻るボタン（画像がないときは ⬅️ が出る）
        if st.button("⬅️", key="back_quest"):
            st.session_state.page = "home"
            st.rerun()
            
    with col_right:
        # タイトルを少し下げて表示（ボタンと高さを合わせるため）
        st.markdown("<h1 style='color: white; font-size: 28px; margin-top: 10px;'>⚔️ クエスト</h1>", unsafe_allow_html=True)
    
    st.write("---")
    
    # 中身
    quests = [
        {"name": "おさら洗い", "pt": 50},
        {"name": "ゴミ出し", "pt": 30}
    ]
    for q in quests:
        st.markdown(f"""
        <div style="background:#f4e4bc; padding:15px; border-radius:10px; margin:10px; border:2px solid #503214; color:#3C2814;">
            <b style="font-size:18px;">{q['name']}</b> 
            <span style="float:right; color:#963232; font-weight:bold; font-size:18px;">{q['pt']}pt</span>
        </div>
        """, unsafe_allow_html=True)