import os
import time
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
    
    # --- 現在のポイントと報酬ポイントを取得して計算準備 ---
    group_id = target_log.get("group_id")
    user_id = target_log.get("user_id")
    quest_id = target_log.get("quest_id")
    
    current_points = 0
    reward_points = 0
    
    if group_id:
        # グループの詳細情報を取得して、今の正確なポイントを調べる
        detail = api.get_group_detail(group_id)
        if isinstance(detail, dict):
            # ① 提出者の「現在のポイント」を探す
            users = detail.get("users", [])
            u_info = next((u for u in users if u["id"] == user_id), None)
            if u_info:
                current_points = u_info.get("points", 0)
            
            # ② クエストの「報酬ポイント」を探す
            quests = detail.get("quests", [])
            q_info = next((q for q in quests if q["id"] == quest_id), None)
            if q_info:
                reward_points = q_info.get("reward_points", 0)
            elif "reward_points" in target_log:
                reward_points = target_log.get("reward_points", 0)

    # --- 画像表示ロジック (IMAGE_BASE_URL使用版) ---
    proof_path = target_log.get("proof_image_path")
    if proof_path:
        filename = os.path.basename(proof_path)
        image_base_url = os.getenv("IMAGE_BASE_URL", "http://localhost:8000")
        if image_base_url.endswith("/"):
            image_base_url = image_base_url[:-1]
            
        image_url = f"{image_base_url}/static/{filename}"
        
        st.write("▼ 証拠画像")
        st.image(image_url, caption="提出された画像")
    else:
        st.warning("画像が見つかりません")

    st.divider()
    
    # 承認・却下ボタンエリア
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("💮 承認する", type="primary", use_container_width=True):
            # ボタンを押した瞬間に、本物の計算チェックを行う！
            MAX_POINTS = 2147483647
            
            if current_points + reward_points > MAX_POINTS:
                # 足し算してオーバーするなら、裏側にデータを送る前にストップ！
                st.error("⚠️ 承認エラー：ポイント上限(2147483647 pt)に達してしまいます！")
                st.info(f"💡 **原因：** {user_name} さんの現在のポイント（{current_points} pt）に、今回の報酬（{reward_points} pt）を足すと、上限(2147483647 pt)を超えてしまいます。\n\n**解決方法：** 先に {user_name} さんにショップでアイテムを買ってもらい、ポイントを減らしてから再度承認してください！")
            else:
                # 計算して大丈夫なら、実際に承認処理をする！
                res = api.review_submission(target_log["id"], approved=True)
                
                if "error" in res:
                    st.error(f"⚠️ エラーが発生しました: {res['error']}")
                else:
                    st.balloons()
                    st.success("承認しました！")
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
                time.sleep(1)
                st.session_state.current_page = "quests"
                st.rerun()