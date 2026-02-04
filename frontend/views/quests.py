import streamlit as st
import datetime
from datetime import datetime as dt
import time

def page_quests():
    st.title("🛡️ クエストボード")

    api = st.session_state.api
    me = api.get_me()
    
    # 1. 参加グループを取得
    my_groups = api.get_my_groups(me["id"])
    if not my_groups:
        st.info("まだグループに参加していません")
        if st.button("🏠 ホームに戻る"):
            st.session_state.current_page = "home"
            st.rerun()
        return

    # 2. ホスト権限を持つグループを抽出
    host_groups = {} # {id: name}
    
    for g in my_groups:
        # 自分がオーナーなら無条件で権限あり
        if g.get("owner_user_id") == me["id"]:
            host_groups[g["id"]] = g["group_name"]
        else:
            # オーナーでなければ詳細を取得して is_host を確認
            # (キャッシュしていないので都度取得になります)
            detail = api.get_group_detail(g["id"])
            if detail:
                my_info = next((u for u in detail["users"] if u["id"] == me["id"]), None)
                if my_info and my_info.get("is_host"):
                    host_groups[g["id"]] = g["group_name"]

    # --- タブ表示 ---
    # ホスト権限がある場合のみ、作成・管理・承認タブを表示
    if host_groups:
        # タブ順序: 挑戦 -> 承認待ち -> 作成 -> 管理
        tabs = st.tabs(["⚔️ クエストに挑戦", "👀 承認待ち一覧", "📝 クエスト作成", "🛠️ クエスト管理"])
    else:
        tabs = st.tabs(["⚔️ クエストに挑戦"])

    # ----------------------------------
    # Tab 1: クエストに挑戦 (全ユーザー)
    # ----------------------------------
    with tabs[0]:
        st.write("現在受注可能なクエスト一覧")
        
        has_active_quests = False
        
        for g in my_groups:
            detail = api.get_group_detail(g["id"])
            if not detail or not detail.get("quests"):
                continue
            
            # 自分の提出ログを取得
            my_logs = api.get_my_submissions(g["id"])

            # quest_id -> status の map を作成
            status_map = {}
            if not isinstance(my_logs, dict):  # APIエラーでなければ
                status_map = {
                    log["quest_id"]: log["status"]
                    for log in my_logs
                    if log.get("status") in ["approved", "pending"]
                }

            # 有効なクエスト抽出
            active_quests = []
            now = dt.now()
            for q in detail["quests"]:
                s_time = dt.fromisoformat(q["start_time"]) if q["start_time"] else None
                e_time = dt.fromisoformat(q["end_time"]) if q["end_time"] else None
                
                is_started = s_time is None or s_time <= now
                is_ended = e_time is not None and e_time < now
                
                if is_started and not is_ended:
                    active_quests.append(q)

            if active_quests:
                has_active_quests = True
                with st.expander(f"🏰 {g['group_name']} ({len(active_quests)})", expanded=True):
                    for q in active_quests:
                        c1, c2 = st.columns([3, 1])
                        c1.markdown(f"**{q['quest_name']}** (💰 {q['reward_points']} pt)")
                        if q.get("description"):
                            c1.caption(q["description"])
                        
                        # ---- ボタン制御ロジック（安全版） ----
                        status = status_map.get(q["id"])

                        if status == "approved":
                            c2.info("✅ 完了")
                        elif status == "pending":
                            c2.info("⏳ 審査中")
                        else:
                            if c2.button("報告する", key=f"rep_{q['id']}"):
                                st.session_state.report_quest_id = q["id"]
                                st.session_state.current_page = "quest_report"
                                st.rerun()

        if not has_active_quests:
            st.info("現在、挑戦できるクエストはありません。")

    # ホスト権限がない場合はここで終了（タブが1つしかないため）
    if not host_groups:
        st.divider()
        if st.button("🏠 ホームに戻る"):
            st.session_state.current_page = "home"
            st.rerun()
        return

    # ----------------------------------
    # Tab 2: 承認待ち一覧 (ホスト用)
    # ----------------------------------
    with tabs[1]:
        st.subheader("承認待ちのクエスト提出")
        st.caption("メンバーから報告されたクエストを確認し、承認または却下します。")
        
        has_pending = False
        
        # ホスト権限のある各グループについて確認
        for gid, gname in host_groups.items():
            # 承認待ちリストを取得
            submissions = api.get_pending_submissions(gid)
            
            # APIエラー回避
            if isinstance(submissions, dict) and "error" in submissions:
                continue
                
            if submissions:
                has_pending = True
                st.markdown(f"**{gname}**")
                for sub in submissions:
                    with st.container(border=True):
                        cols = st.columns([3, 1])
                        # user_nameなどがAPIレスポンスに含まれている前提
                        u_name = sub.get("user_name", "Unknown User")
                        q_title = sub.get("quest_title", "Unknown Quest")
                        submitted_at = sub.get("completed_at", "")
                        
                        # 日時のフォーマット整形 (YYYY-MM-DDTHH:MM:SS -> YYYY/MM/DD HH:MM)
                        if submitted_at:
                            try:
                                submitted_at = submitted_at.replace("T", " ")[:16]
                            except:
                                pass

                        cols[0].write(f"👤 **{u_name}** が **{q_title}** を完了報告")
                        cols[0].caption(f"提出日時: {submitted_at}")
                            
                        # 確認ボタン: 承認画面へ遷移
                        if cols[1].button("確認する", key=f"check_{sub['id']}", type="primary"):
                            st.session_state.review_target_log = sub
                            st.session_state.current_page = "quest_review" # 承認画面へ
                            st.rerun()
                            
        if not has_pending:
            st.info("現在、承認待ちのクエストはありません")

    # ----------------------------------
    # Tab 3: クエスト作成 (ホスト用)
    # ----------------------------------
    with tabs[2]:
        st.subheader("新規クエスト登録")
        
        # グループ選択
        target_group_id = st.selectbox(
            "作成するグループ",
            options=list(host_groups.keys()),
            format_func=lambda x: host_groups[x],
            key="create_q_group"
        )
        
        # 入力フォーム
        q_name = st.text_input("クエスト名", placeholder="例: お風呂洗い", key="q_new_name")
        q_desc = st.text_area("説明", placeholder="完了条件など", key="q_new_desc")
        q_reward = st.number_input("報酬ポイント", min_value=1, value=100, step=10, key="q_new_reward")
        
        st.markdown("---")
        st.write("📅 **期間設定 (必須)**")

        # 日時設定（必須化）
        col_d1, col_d2 = st.columns(2)
        
        with col_d1:
            st.caption("開始日時")
            d_s = st.date_input("開始日", value=dt.now(), key="q_start_d")
            t_s = st.time_input("開始時間", value=dt.now().time(), key="q_start_t")
            
        with col_d2:
            st.caption("終了日時")
            # デフォルトは翌日の同時刻
            default_end = dt.now() + datetime.timedelta(days=1)
            d_e = st.date_input("終了日", value=default_end, key="q_end_d")
            t_e = st.time_input("終了時間", value=default_end.time(), key="q_end_t")

        # datetime結合
        start_dt = dt.combine(d_s, t_s)
        end_dt = dt.combine(d_e, t_e)

        # 検証ロジック: 終了が開始より前になっていないか？
        is_valid_time = True
        if end_dt <= start_dt:
            st.warning("⚠️ 終了日時は開始日時より後に設定してください")
            is_valid_time = False

        st.markdown("---")
        
        # 登録ボタン
        if st.button("クエストを作成する", type="primary", key="btn_create_q", disabled=not is_valid_time):
            if not q_name:
                st.error("クエスト名を入力してください")
            elif not is_valid_time:
                st.error("期間設定を確認してください")
            else:
                # ISOフォーマットに変換
                start_str = start_dt.isoformat()
                end_str = end_dt.isoformat()
                
                res = api.create_quest(
                    target_group_id, 
                    q_name, 
                    q_desc, 
                    q_reward, 
                    start_str, # 必ず値が入る
                    end_str    # 必ず値が入る
                )
                if "error" in res:
                    st.error(res["error"])
                else:
                    st.success(f"クエスト「{q_name}」を作成しました！")
                    time.sleep(1)
                    st.rerun()

    # ----------------------------------
    # Tab 4: クエスト管理 (画面遷移)
    # ----------------------------------
    with tabs[3]:
        st.subheader("クエスト管理・削除")
        st.write("管理するグループを選択して、管理画面へ移動します。")
        
        manage_group_id = st.selectbox(
            "グループを選択",
            options=list(host_groups.keys()),
            format_func=lambda x: host_groups[x],
            key="manage_q_group"
        )
        
        if st.button("管理画面を開く", type="primary"):
            st.session_state.manage_group_id = manage_group_id
            st.session_state.current_page = "quest_manage" 
            st.rerun()
            
    st.divider()
    if st.button("🏠 ホームに戻る"):
        st.session_state.current_page = "home"
        st.rerun()