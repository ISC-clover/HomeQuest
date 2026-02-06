import os
import streamlit as st

def page_quest_review():
    st.title("🔍 クエスト承認")
    api = st.session_state.api
    
    # セッションから対象データを取得
    target_log = st.session_state.get("review_target_log")
    
    if not target_log:
        st.error("データが見つかりません")
        if st.button("戻る"):
            st.session_state.current_page = "quests"
            st.rerun()
        return

    if st.button("← 一覧に戻る"):
        st.session_state.current_page = "quests"
        del st.session_state["review_target_log"]
        st.rerun()

    st.divider()
    
    # ユーザー名とクエスト名の表示
    user_name = target_log.get("user_name") or f"ID: {target_log.get('user_id')}"
    quest_title = target_log.get("quest_title") or f"ID: {target_log.get('quest_id')}"
    
    st.subheader(f"チャレンジャー: {user_name}")
    st.info(f"クエスト: **{quest_title}**")
    
    # --- 画像表示ロジック (IMAGE_BASE_URL使用版) ---
    proof_path = target_log.get("proof_image_path")
    if proof_path:
        filename = os.path.basename(proof_path)
        
        # 環境変数からベースURLを取得 (例: http://localhost:8000)
        # 取得できない場合のフォールバックとして localhost:8000 を入れています
        image_base_url = os.getenv("IMAGE_BASE_URL", "http://localhost:8000")
        
        # 末尾のスラッシュ有無を考慮してURL結合
        if image_base_url.endswith("/"):
            image_base_url = image_base_url[:-1]
            
        image_url = f"{image_base_url}/static/{filename}"
        
        st.write("▼ 証拠画像")
        # use_container_width=True を削除しても動きますが、警告通りにするなら以下
        st.image(image_url, caption="提出された画像")
    else:
        st.warning("画像が見つかりません")

    st.divider()
    
    # 承認・却下ボタンエリア
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("💮 承認する", type="primary", use_container_width=True):
            res = api.review_submission(target_log["id"], approved=True)
            if "error" in res:
                st.error(res["error"])
            else:
                st.balloons()
                st.success("承認しました！")
                import time
                time.sleep(1)
                st.session_state.current_page = "quests"
                st.rerun()
                
    with col2:
        if st.button("❌ 却下する", type="secondary", use_container_width=True):
            res = api.review_submission(target_log["id"], approved=False)
            if "error" in res:
                st.error(res["error"])
            else:
                st.info("却下しました")
                import time
                time.sleep(1)
                st.session_state.current_page = "quests"
                st.rerun()