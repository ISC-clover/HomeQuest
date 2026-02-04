import streamlit as st
import time

def page_group_detail():
    api = st.session_state.api
    
    # セッションから選択中のグループIDを取得
    group_id = st.session_state.get("selected_group_id")
    if not group_id:
        st.error("グループが選択されていません")
        if st.button("一覧に戻る"):
            st.session_state.current_page = "groups"
            st.rerun()
        return

    # データ取得
    group = api.get_group_detail(group_id)
    me = api.get_me()
    
    if "error" in group or "error" in me:
        st.error("データの取得に失敗しました")
        return

    # --- 権限チェック ---
    my_id = me["id"]
    owner_id = group["owner_user_id"]
    is_owner = (my_id == owner_id)
    
    # メンバーリストから自分の情報を探し、ホスト権限を持っているか確認
    my_member_info = next((m for m in group["users"] if m["id"] == my_id), None)
    is_host = my_member_info["is_host"] if my_member_info else False
    
    # オーナーは自動的にホスト権限を持つ扱いにする
    if is_owner:
        is_host = True

    # === 画面描画 ===
    st.title(f"🏰 {group['group_name']}")
    st.caption(f"Group ID: {group['id']} | Owner: ID {owner_id}")
    
    if st.button("← グループ一覧に戻る"):
        st.session_state.current_page = "groups"
        st.rerun()
        
    st.divider()

    # ------------------------------
    # 1. ホスト・オーナー用管理エリア
    # ------------------------------
    if is_host:
        st.subheader("🛠️ 管理メニュー")
        
        # タブで機能を整理
        manage_tabs = ["招待コード", "クエスト管理"]
        if is_owner:
            manage_tabs.extend(["権限管理", "グループ設定"])
            
        tabs = st.tabs(manage_tabs)

        # -- A. 招待コード --
        with tabs[0]:
            current_code = group.get("invite_code")

            # 1. すでにコードがある場合
            if current_code:
                st.markdown(f"#### 🎟️ 招待コード: `{current_code}`")
                st.caption("メンバーにこのコードを共有してください")
                
                # 再生成ボタン
                if st.button("🔄 コードを再生成する", help="古いコードは無効になります"):
                    # APIを叩いて新しいコードを取得
                    res = api.reset_invite_code(group_id)
                    
                    if "error" in res:
                        st.error(res["error"])
                    else:
                        # APIが新しいコードを返してくれる場合 (例: {"invite_code": "NEW123"})
                        new_code = res.get("invite_code") or res.get("code")
                        msg = f"新しいコード「{new_code}」を発行しました！" if new_code else "コードを更新しました"
                        st.toast(msg, icon="✅")
                        
                        time.sleep(1)
                        st.rerun()

            # 2. まだコードがない場合
            else:
                st.info("招待コードはまだ発行されていません")
                
                # 生成ボタン
                if st.button("➕ コードを生成する", type="primary"):
                    # APIを叩いてコードを生成
                    res = api.generate_invite_code(group_id)
                    
                    if "error" in res:
                        st.error(res["error"])
                    else:
                        # APIが生成したコードを返してくれる場合
                        new_code = res.get("invite_code") or res.get("code")
                        msg = f"コード「{new_code}」を発行しました！" if new_code else "コードを生成しました"
                        st.toast(msg, icon="🎉")
                        
                        time.sleep(1)
                        st.rerun()

        # -- B. クエスト管理 --
        with tabs[1]:
            st.write("新しいクエストを作成してメンバーに挑戦させましょう！")
            if st.button("📜 クエスト追加画面へ", type="primary"):
                st.session_state.current_page = "quest_add"
                st.rerun()

        # -- C. 権限管理（オーナーのみ）--
        if is_owner:
            with tabs[2]:
                st.write("メンバーIDを指定して、ホスト権限を変更または追放します。")
                
                col_input, col_action = st.columns([1, 2])
                with col_input:
                    target_user_id = st.number_input("対象ユーザーID", min_value=1, step=1, key="target_uid")
                
                with col_action:
                    st.write("アクション")
                    c1, c2, c3 = st.columns(3)
                    with c1:
                        if st.button("🛡️ ホストに昇格"):
                            if target_user_id == my_id:
                                st.error("自分自身の権限は変更できません")
                            else:
                                res = api.update_member_role(group_id, target_user_id, True)
                                if "error" in res:
                                    st.error(res["error"])
                                else:
                                    st.success(res["message"])
                                    time.sleep(1)
                                    st.rerun()
                    with c2:
                        if st.button("⬇️ ホスト剥奪"):
                            if target_user_id == my_id:
                                st.error("自分自身の権限は変更できません")
                            else:
                                res = api.update_member_role(group_id, target_user_id, False)
                                if "error" in res:
                                    st.error(res["error"])
                                else:
                                    st.success(res["message"])
                                    time.sleep(1)
                                    st.rerun()
                    with c3:
                        if st.button("🚫 追放する", type="primary"):
                            if target_user_id == my_id:
                                st.error("自分自身を追放することはできません")
                            else:
                                res = api.kick_member(group_id, target_user_id)
                                if "error" in res:
                                    st.error(res["error"])
                                else:
                                    st.success(res["message"])
                                    time.sleep(1)
                                    st.rerun()

        # -- D. グループ設定（オーナーのみ）--
        if is_owner:
            with tabs[3]:
                st.error("⚠️ この操作は取り消せません")
                if st.button("💣 グループを完全に削除する", type="primary"):
                    res = api.delete_group(group_id)
                    if "error" in res:
                        st.error(res["error"])
                    else:
                        st.success("グループを削除しました")
                        time.sleep(1)
                        st.session_state.current_page = "groups"
                        st.rerun()

        st.divider()

    # ------------------------------
    # 2. メンバー一覧表示
    # ------------------------------
    st.subheader(f"👥 メンバー ({len(group['users'])})")
    
    # 見やすいようにカード形式で表示
    for member in group['users']:
        with st.container():
            # アイコン決定
            icon = "👤"
            role_text = "メンバー"
            if member['id'] == owner_id:
                icon = "👑"
                role_text = "オーナー"
            elif member['is_host']:
                icon = "🛡️"
                role_text = "ホスト"
            
            st.markdown(f"""
            **{icon} {member['user_name']}** <span style='color:gray; font-size:0.8em;'>(ID: {member['id']})</span>  
            <span style='background-color:#eee; padding:2px 6px; border-radius:4px; font-size:0.8em;'>{role_text}</span> 
            Points: {member['points']}
            """, unsafe_allow_html=True)
            st.markdown("---")

    # ------------------------------
    # 3. 離脱ボタン（オーナー以外）
    # ------------------------------
    if not is_owner:
        st.markdown("<br><br>", unsafe_allow_html=True)
        with st.expander("⚠️ グループから抜ける"):
            st.warning("本当にこのグループから抜けますか？ポイントなどは失われる可能性があります。")
            if st.button("脱退する", type="primary"):
                res = api.leave_group(group_id)
                if "error" in res:
                    st.error(res["error"])
                else:
                    st.success("グループから脱退しました")
                    time.sleep(1)
                    st.session_state.current_page = "groups"
                    st.rerun()