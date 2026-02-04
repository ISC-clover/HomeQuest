import time
import streamlit as st
from datetime import datetime as dt

def page_quest_manage():
    api = st.session_state.api
    
    # セッションから選択されたグループIDを取得
    group_id = st.session_state.get("manage_group_id")
    if not group_id:
        st.error("グループが選択されていません")
        if st.button("戻る"):
            st.session_state.current_page = "quests"
            st.rerun()
        return

    # グループ詳細を取得
    detail = api.get_group_detail(group_id)
    if "error" in detail:
        st.error("データの取得に失敗しました")
        return

    # ヘッダーエリア
    col_h1, col_h2 = st.columns([1, 3])
    with col_h1:
        if st.button("← 戻る"):
            st.session_state.current_page = "quests"
            st.rerun()
    with col_h2:
        st.title(f"🛠️ {detail['group_name']} クエスト管理")
    
    st.divider()

    # クエストの分類
    all_quests = detail.get("quests", [])
    now = dt.now()
    
    active_q = []   # 表示中
    reserved_q = [] # 予約済み（未来）
    ended_q = []    # 終了（過去）
    
    for q in all_quests:
        s_time = dt.fromisoformat(q["start_time"]) if q["start_time"] else None
        e_time = dt.fromisoformat(q["end_time"]) if q["end_time"] else None
        
        if s_time and s_time > now:
            reserved_q.append(q)
        elif e_time and e_time < now:
            ended_q.append(q)
        else:
            active_q.append(q)
            
    # タブで表示
    m_tabs = st.tabs([
        f"🟢 表示中 ({len(active_q)})", 
        f"🟡 予約済み ({len(reserved_q)})", 
        f"🔴 表示終了 ({len(ended_q)})"
    ])
    
    # リスト表示用の関数 (DRY)
    def render_quest_row(quests):
        if not quests:
            st.info("クエストはありません")
            return
            
        for q in quests:
            with st.container(border=True):
                c1, c2 = st.columns([5, 1])
                with c1:
                    st.subheader(f"{q['quest_name']} (💰{q['reward_points']})")
                    if q.get("description"):
                        st.caption(q["description"])
                    
                    # 期間表示
                    period_str = ""
                    if q.get("start_time"):
                        period_str += f"開始: {q['start_time'].replace('T', ' ')} "
                    if q.get("end_time"):
                        period_str += f" / 終了: {q['end_time'].replace('T', ' ')}"
                    
                    if period_str:
                        st.markdown(f"<small style='color:gray'>{period_str}</small>", unsafe_allow_html=True)
                
                with c2:
                    st.write("") # 上の隙間
                    # 削除ボタン
                    if st.button("🗑️", key=f"del_{q['id']}", help="クエストを削除"):
                        res = api.delete_quest(q['id'])
                        if "error" in res:
                            st.error(res["error"])
                        else:
                            st.toast("削除しました", icon="🗑️")
                            time.sleep(1)
                            st.rerun()

    with m_tabs[0]:
        render_quest_row(active_q)
    with m_tabs[1]:
        st.caption("※ 開始日時が未来のクエストです。")
        render_quest_row(reserved_q)
    with m_tabs[2]:
        st.caption("※ 終了日時を過ぎたクエストです。")
        render_quest_row(ended_q)