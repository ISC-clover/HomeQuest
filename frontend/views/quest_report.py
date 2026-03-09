import streamlit as st
from PIL import Image
import time
import utils

def page_quest_report():
    utils.shop_css()
    st.markdown('<div class="main-title"><h1>📸 クエスト報告</h1></div>', unsafe_allow_html=True)
    
    api = st.session_state.api
    quest_id = st.session_state.get("report_quest_id")
    
    # --- 1. IDチェック ---
    if not quest_id:
        st.error("クエストが選択されていません")
        if st.button("戻る"):
            st.session_state.current_page = "quests"
            st.rerun()
        return

    # --- 2. 提出済みガード (NEW!) ---
    # クエストボードと同じロジックで、既に提出済みでないか最終確認します
    with st.spinner("提出状況を確認中..."):
        # ユーザーが所属する全グループから、このクエストのログがあるか探す
        # (APIの設計上、所属グループを回る必要があります)
        me = api.get_me()
        my_groups = api.get_my_groups(me["id"])
        
        already_submitted = False
        for g in my_groups:
            logs = api.get_my_submissions(g["id"])
            if isinstance(logs, list):
                if any(l["quest_id"] == quest_id and l["status"] in ["approved", "pending"] for l in logs):
                    already_submitted = True
                    break

    if already_submitted:
        st.warning("⚠️ このクエストは既に報告済みか、現在審査中です。")
        if st.button("クエスト一覧に戻る"):
            st.session_state.current_page = "quests"
            del st.session_state["report_quest_id"]
            st.rerun()
        return # ここで処理を終了し、以下のフォームを表示させない

    # --- 3. メインフォーム ---
    if st.button("← キャンセルして戻る"):
        st.session_state.current_page = "quests"
        del st.session_state["report_quest_id"]
        st.rerun()

    st.markdown(f"### クエストID: {quest_id}")
    st.markdown("証拠写真をアップロードしてください")
    
    uploaded_file = st.file_uploader("画像を選択", type=["jpg", "jpeg", "png"])
    
    if uploaded_file is not None:
        image = Image.open(uploaded_file)
        st.image(image, caption='送信する画像', use_container_width=True)
        
        if st.button("送信する", type="primary"):
            with st.spinner("送信中..."):
                res = api.complete_quest(quest_id, uploaded_file)
                
                if "error" in res:
                    st.error(res["error"])
                else:
                    st.success("提出しました！ホストの承認をお待ちください。")
                    
                    # 状態をクリアして一覧に戻る
                    if "report_quest_id" in st.session_state:
                        del st.session_state["report_quest_id"]
                    
                    time.sleep(1.5)
                    st.session_state.current_page = "quests"
                    st.rerun()

    utils.back_to_home()