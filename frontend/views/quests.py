import datetime, time
import streamlit as st
from datetime import datetime as dt

def page_quests():
    st.title("🛡️ クエストボード")

    api = st.session_state.api
    me = api.get_me()
    
    # 1. 参加グループを取得
    my_groups = api.get_my_groups(me["id"])
    if not my_groups or (isinstance(my_groups, dict) and "error" in my_groups):
        st.info("まだグループに参加していません")
        if st.button("🏠 ホームに戻る", key="back_home_top"):
            st.session_state.current_page = "home"
            st.rerun()
        return

    # 2. ホスト権限判定
    host_groups = {} 
    for g in my_groups:
        if g.get("owner_user_id") == me["id"]:
            host_groups[g["id"]] = g["group_name"]
        else:
            detail = api.get_group_detail(g["id"])
            if isinstance(detail, dict) and "users" in detail:
                my_info = next((u for u in detail["users"] if u["id"] == me["id"]), None)
                if my_info and my_info.get("is_host"):
                    host_groups[g["id"]] = g["group_name"]

    # 3. メインタブ
    tab_titles = ["⚔️ クエストに挑戦", "✅ 完了済みのクエスト"]
    if host_groups:
        tab_titles += ["👀 承認待ち一覧", "📝 クエスト作成", "🛠️ クエスト管理"]
    
    tabs = st.tabs(tab_titles)

    all_todo = [] 
    all_done = [] 

    for g in my_groups:
        # --- A. 最新のクエスト情報を取得して辞書にする ---
        detail = api.get_group_detail(g["id"])
        quest_lookup = {}
        if detail and "quests" in detail:
            for q in detail["quests"]:
                quest_lookup[q["id"]] = q

        # --- B. 自分の履歴を取得して照合 ---
        my_history = api.get_my_submissions(g["id"])
        status_map = {}
        
        if isinstance(my_history, list):
            for log in my_history:
                q_id = log.get("quest_id")
                status = log.get("status")
                status_map[q_id] = status 
                
                if status == "approved":
                    current_q = quest_lookup.get(q_id)
                    if current_q:
                        q_title = current_q.get("quest_name")
                        q_reward = current_q.get("reward_points")
                    else:
                        q_title = log.get("quest_title") or log.get("quest_name") or "完了済みのクエスト"
                        q_reward = log.get("reward_points") or 0
                    
                    all_done.append({
                        "group_name": g["group_name"],
                        "quest_title": str(q_title),
                        "reward": q_reward,
                        "date": log.get("completed_at", "")
                    })

        # --- C. 挑戦中リストの作成 ---
        if detail and "quests" in detail:
            now = dt.now()
            for q in detail["quests"]:
                if status_map.get(q["id"]) == "approved": continue
                s_t, e_t = q.get("start_time"), q.get("end_time")
                try:
                    s_time = dt.fromisoformat(s_t) if s_t else None
                    e_time = dt.fromisoformat(e_t) if e_t else None
                except: continue
                if (s_time is None or s_time <= now) and (e_time is None or e_time >= now):
                    all_todo.append({"group_name": g["group_name"], "q": q, "status": status_map.get(q["id"]), "gid": g["id"]})

    # --- Tab 0: ⚔️ クエストに挑戦 ---
    with tabs[0]:
        st.subheader("挑戦中のクエスト")
        if not all_todo:
            st.info("挑戦できるクエストはありません。")
        else:
            for item in all_todo:
                q, status, gname, gid = item["q"], item["status"], item["group_name"], item["gid"]
                with st.container(border=True):
                    c1, c2 = st.columns([3, 1])
                    c1.markdown(f"**{q['quest_name']}**")
                    c1.caption(f"🏰 {gname} | 💰 {q['reward_points']} pt")
                    if status == "pending":
                        c2.info("⏳ 審査中")
                    else:
                        if c2.button("挑戦する", key=f"btn_q_{q['id']}_{gid}"):
                            st.session_state.report_quest_id = q["id"]
                            st.session_state.selected_group_id = gid
                            st.session_state.current_page = "quest_report"
                            st.rerun()

    # --- Tab 1: ✅ 完了済みのクエスト ---
    with tabs[1]:
        st.subheader("クリアした証（冒険 of 記録）")
        if not all_done:
            st.info("まだ完了したクエストはありません。")
        else:
            sorted_done = sorted(all_done, key=lambda x: x['date'] if x['date'] else "", reverse=True)
            for item in sorted_done:
                with st.container(border=True):
                    st.markdown(f"✅ **{item['quest_title']}**")
                    date_str = item['date'].replace('T', ' ')[:16] if item['date'] else "達成！"
                    reward_disp = f"{item['reward']} pt" if item['reward'] > 0 else "獲得済み"
                    st.caption(f"🏰 {item['group_name']} | 💰 {reward_disp} | 達成日: {date_str}")

    # --- ホスト専用タブ (維持) ---
    if host_groups:
        with tabs[2]:
            st.subheader("承認待ち")
            has_p = False
            for gid, gname in host_groups.items():
                subs = api.get_pending_submissions(gid)
                if isinstance(subs, list) and subs:
                    has_p = True
                    for sub in subs:
                        with st.container(border=True):
                            ca, cb = st.columns([3, 1])
                            ca.write(f"👤 **{sub.get('user_name')}** が **{sub.get('quest_title')}** を報告")
                            if cb.button("確認する", key=f"chk_sub_{sub['id']}"):
                                st.session_state.review_target_log = sub
                                st.session_state.current_page = "quest_review"
                                st.rerun()
            if not has_p: st.info("なし")
        with tabs[3]:
            st.subheader("新規登録")
            tgid = st.selectbox("グループ", list(host_groups.keys()), format_func=lambda x: host_groups[x])
            name = st.text_input("名前")
            rew = st.number_input("報酬", min_value=1, value=100)
            if st.button("作成", type="primary"):
                api.create_quest(tgid, name, "", rew, dt.now().isoformat(), (dt.now()+datetime.timedelta(days=7)).isoformat())
                st.success("完了！"); time.sleep(1); st.rerun()
        with tabs[4]:
            st.subheader("管理")
            mgid = st.selectbox("管理グループ", list(host_groups.keys()), format_func=lambda x: host_groups[x], key="m_s")
            if st.button("管理画面へ"):
                st.session_state.manage_group_id = mgid
                st.session_state.current_page = "quest_manage"
                st.rerun()

    st.divider()
    if st.button("🏠 ホームに戻る", key="back_home_bot"):
        st.session_state.current_page = "home"
        st.rerun()