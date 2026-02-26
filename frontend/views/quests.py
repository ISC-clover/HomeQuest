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
    is_host = False
    host_groups = {} 
    for g in my_groups:
        if g.get("owner_user_id") == me["id"]:
            is_host = True
            host_groups[g["id"]] = g["group_name"]
        else:
            detail = api.get_group_detail(g["id"])
            if isinstance(detail, dict) and "users" in detail:
                my_info = next((u for u in detail["users"] if u["id"] == me["id"]), None)
                if my_info and my_info.get("is_host"):
                    is_host = True
                    host_groups[g["id"]] = g["group_name"]

    # ----------------------------------
    # 3. 役割に応じてタブの中身を完全に分ける
    # ----------------------------------
    if is_host:
        # ホスト（親）が見る4つのタブ
        tab_titles = ["⚔️ クエストに挑戦", "👀 承認待ち一覧", "📝 クエスト作成", "🛠️ クエスト管理"]
    else:
        # 子供（プレイヤー）が見る3つのタブ
        tab_titles = ["⚔️ クエストに挑戦", "⏳ 承認待ち", "✅ 完了済みのクエスト"]
    
    tabs = st.tabs(tab_titles)

    # 共通のデータ準備（仕分け）
    all_todo = [] 
    all_pending = [] 
    all_done = [] 

    for g in my_groups:
        detail = api.get_group_detail(g["id"])
        quest_lookup = {q["id"]: q for q in detail["quests"]} if detail and "quests" in detail else {}
        my_history = api.get_my_submissions(g["id"])
        status_map = {}
        
        if isinstance(my_history, list):
            for log in my_history:
                q_id = log.get("quest_id")
                status = log.get("status")
                status_map[q_id] = status 
                
                current_q = quest_lookup.get(q_id)
                q_title = current_q.get("quest_name") if current_q else (log.get("quest_title") or "クエスト")
                q_reward = current_q.get("reward_points") if current_q else (log.get("reward_points") or 0)
                
                info = {"group_name": g["group_name"], "quest_title": str(q_title), "reward": q_reward, "date": log.get("completed_at", "")}

                if status == "approved":
                    all_done.append(info)
                elif status == "pending":
                    all_pending.append(info)

        if detail and "quests" in detail:
            now = dt.now()
            for q in detail["quests"]:
                # 子供の場合、承認待ちや完了済みは挑戦中から消す
                if not is_host and status_map.get(q["id"]) in ["approved", "pending"]:
                    continue
                
                s_t, e_t = q.get("start_time"), q.get("end_time")
                try:
                    s_time = dt.fromisoformat(s_t) if s_t else None
                    e_time = dt.fromisoformat(e_t) if e_t else None
                except: continue
                if (s_time is None or s_time <= now) and (e_time is None or e_time >= now):
                    all_todo.append({"group_name": g["group_name"], "q": q, "gid": g["id"]})

    # --- タブ[0]: ⚔️ クエストに挑戦 (共通) ---
    with tabs[0]:
        st.subheader("新しいクエスト")
        if not all_todo: st.info("挑戦できるクエストはありません。")
        else:
            for item in all_todo:
                q, gname, gid = item["q"], item["group_name"], item["gid"]
                with st.container(border=True):
                    c1, c2 = st.columns([3, 1])
                    c1.markdown(f"**{q['quest_name']}**")
                    c1.caption(f"🏰 {gname} | 💰 {q['reward_points']} pt")
                    if c2.button("挑戦する", key=f"btn_q_{q['id']}_{gid}"):
                        st.session_state.report_quest_id = q["id"]
                        st.session_state.selected_group_id = gid
                        st.session_state.current_page = "quest_report"
                        st.rerun()

    if not is_host:
        # ----------------------------------
        # 子供専用：承認待ち & 完了済み
        # ----------------------------------
        with tabs[1]:
            st.subheader("承認待ちの報告")
            if not all_pending: st.info("現在、承認待ちのクエストはありません。")
            else:
                for item in all_pending:
                    with st.container(border=True):
                        st.markdown(f"⏳ **{item['quest_title']}**")
                        st.caption(f"🏰 {item['group_name']} | 💰 {item['reward']} pt")

        with tabs[2]:
            st.subheader("クリアした記録")
            if not all_done: st.info("まだ完了したクエストはありません。")
            else:
                sorted_done = sorted(all_done, key=lambda x: x['date'] if x['date'] else "", reverse=True)
                for item in sorted_done:
                    with st.container(border=True):
                        st.markdown(f"✅ **{item['quest_title']}**")
                        date_str = item['date'].replace('T', ' ')[:10] if item['date'] else "達成！"
                        st.caption(f"🏰 {item['group_name']} | 💰 {item['reward']} pt | {date_str}")
    else:
        # ----------------------------------
        # ホスト専用：承認・作成・管理
        # ----------------------------------
        with tabs[1]:
            st.subheader("承認待ち一覧")
            has_p = False
            for gid, gname in host_groups.items():
                subs = api.get_pending_submissions(gid)
                if isinstance(subs, list) and subs:
                    has_p = True
                    for sub in subs:
                        with st.container(border=True):
                            ca, cb = st.columns([3, 1])
                            ca.write(f"👤 **{sub.get('user_name')}** → **{sub.get('quest_title')}**")
                            if cb.button("確認する", key=f"chk_sub_{sub['id']}", type="primary"):
                                st.session_state.review_target_log = sub
                                st.session_state.current_page = "quest_review"
                                st.rerun()
            if not has_p: st.info("承認待ちの報告はありません。")

        with tabs[2]:
            st.subheader("クエスト作成")
            
            # 🌟【ここが追加ポイント！】分身の術（Key-busting）の準備
            if "quest_form_key" not in st.session_state:
                st.session_state.quest_form_key = 0
            qfk = st.session_state.quest_form_key

            tgid = st.selectbox("グループ", list(host_groups.keys()), format_func=lambda x: host_groups[x], key=f"tgid_{qfk}")
            name = st.text_input("クエスト名", key=f"q_name_{qfk}")
            rew = st.number_input("報酬", min_value=1, value=100, key=f"q_rew_{qfk}")
            
            if st.button("作成する", key=f"create_btn_{qfk}", type="primary"):
                if name.strip(): # 名前が空っぽの時は作れないようにガード！
                    api.create_quest(tgid, name, "", rew, dt.now().isoformat(), (dt.now()+datetime.timedelta(days=7)).isoformat())
                    st.success("作成完了！")
                    
                    # 🌟 次に画面を描画するときに、鍵(Key)の番号を増やして新しくする！
                    st.session_state.quest_form_key += 1
                    
                    time.sleep(1)
                    st.rerun()
                else:
                    st.warning("⚠️ クエスト名を入力してください！")

        with tabs[3]:
            st.subheader("クエスト管理")
            mgid = st.selectbox("グループ", list(host_groups.keys()), format_func=lambda x: host_groups[x], key="m_s_h")
            if st.button("管理画面を開く"):
                st.session_state.manage_group_id = mgid
                st.session_state.current_page = "quest_manage"
                st.rerun()

    st.divider()
    if st.button("🏠 ホームに戻る", key="back_home_bot"):
        st.session_state.current_page = "home"
        st.rerun()