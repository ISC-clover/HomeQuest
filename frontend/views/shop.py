import time
import streamlit as st

def page_shop():
    st.title("🛍️ ショップ")
    
    api = st.session_state.api
    me = api.get_me()
    
    if "error" in me:
        st.error("ログイン情報を取得できませんでした")
        return

    my_groups = api.get_my_groups(me["id"])
    if not my_groups:
        st.info("まだグループに参加していません")
        if st.button("🏠 ホームに戻る"):
            st.session_state.current_page = "home"
            st.rerun()
        return

    # --- 自分の全購入履歴を取得（上限チェック用） ---
    all_my_purchases = []
    try:
        res_my = api.get_my_purchases()
        if isinstance(res_my, list): 
            all_my_purchases = res_my
        elif isinstance(res_my, dict):
            for key in ["purchases", "data", "items", "history"]:
                if key in res_my and isinstance(res_my[key], list):
                    all_my_purchases = res_my[key]
                    break
    except Exception:
        pass

    group_names = [f"🏰 {g['group_name']}" for g in my_groups]
    group_tabs = st.tabs(group_names)

    for idx, group_info in enumerate(my_groups):
        with group_tabs[idx]:
            group_id = group_info["id"]
            group = api.get_group_detail(group_id)
            
            if "error" in group:
                st.error(f"データの取得に失敗しました: {group['group_name']}")
                continue

            my_member_info = next((m for m in group["users"] if m["id"] == me["id"]), None)
            if not my_member_info:
                st.warning("メンバー情報が見つかりません")
                continue

            my_points = my_member_info["points"]
            is_host = my_member_info.get("is_host", False)
            if group["owner_user_id"] == me["id"]:
                is_host = True

            st.markdown(f"""
            <div style="background-color: #f0f2f6; padding: 10px; border-radius: 10px; margin-bottom: 15px; text-align: center;">
                <h4 style="margin:0; color: #555;">💰 {group['group_name']} での所持ポイント: 
                <span style="color: #d63384;">{my_points} pt</span></h4>
            </div>
            """, unsafe_allow_html=True)

            items = group.get("shops", [])
            group_item_ids = {item['id'] for item in items}
            
            # --- グループ全体の履歴を取得（みんなの履歴用） ---
            group_history = []
            try:
                res_gh = api.get_purchase_history(group_id)
                if isinstance(res_gh, list):
                    group_history = res_gh
                elif isinstance(res_gh, dict):
                    for key in ["purchases", "data", "items", "history"]:
                        if key in res_gh and isinstance(res_gh[key], list):
                            group_history = res_gh[key]
                            break
            except Exception:
                pass

            # --- 購入回数をカウント ---
            purchase_counts = {}
            if group_history and not is_host:
                for h in group_history:
                    if h.get("user_id") == me["id"]:
                        item_id = h.get('shop_id') or h.get('item_id')
                        if item_id:
                            purchase_counts[item_id] = purchase_counts.get(item_id, 0) + 1
            else:
                for p in all_my_purchases:
                    p_item_id = p.get('shop_id') or p.get('item_id')
                    if p.get("group_id") == group_id or p_item_id in group_item_ids:
                        if p_item_id: 
                            purchase_counts[p_item_id] = purchase_counts.get(p_item_id, 0) + 1

            # 🌟 タブをスッキリ整理！（交換承認や、もちものを削除）
            if is_host:
                sub_tab_titles = ["🛒 お買い物", "🆕 商品を入荷", "🛠️ 管理", "📜 みんなの履歴"]
            else:
                sub_tab_titles = ["🛒 お買い物", "📜 みんなの履歴"]
            
            sub_tabs = st.tabs(sub_tab_titles)

            # --- [サブタブ0] お買い物 (共通) ---
            with sub_tabs[0]:
                if not items:
                    st.info("📦 現在、販売されているアイテムはありません。")
                else:
                    cols = st.columns(2)
                    for i, item in enumerate(items):
                        with cols[i % 2]:
                            with st.container(border=True):
                                st.subheader(item['item_name'])
                                st.caption(item.get('description') or "説明なし")
                                
                                limit = item.get('limit_per_user')
                                bought_count = purchase_counts.get(item['id'], 0)
                                is_limit_reached = False
                                
                                limit_text = ""
                                if limit is not None and limit > 0:
                                    limit_text = f" (残り {limit - bought_count} 回)"
                                    if bought_count >= limit:
                                        is_limit_reached = True

                                st.markdown(f"**💰 {item['cost_points']} pt**{limit_text}")
                                
                                has_enough_points = my_points >= item['cost_points']
                                can_buy = has_enough_points and not is_limit_reached
                                
                                if is_limit_reached:
                                    btn_label = "✅ 購入上限"
                                elif not has_enough_points:
                                    btn_label = "Pt不足"
                                else:
                                    btn_label = "購入する"

                                if st.button(btn_label, key=f"buy_{group_id}_{item['id']}", 
                                             disabled=not can_buy, 
                                             type="primary" if can_buy else "secondary", 
                                             use_container_width=True):
                                    res = api.purchase_item(item['id'])
                                    if "error" in res: st.error(res["error"])
                                    else:
                                        st.balloons()
                                        st.success(f"「{item['item_name']}」を購入！親に見せてね！")
                                        time.sleep(1.5); st.rerun()

            if is_host:
                # --- ホスト専用タブ ---
                with sub_tabs[1]:
                    st.subheader("新しい商品を入荷する")
                    c1, c2 = st.columns([3, 1])
                    new_name = c1.text_input("商品名", key=f"new_name_{group_id}")
                    new_cost = c2.number_input("価格 (pt)", min_value=1, value=100, key=f"new_cost_{group_id}")
                    new_desc = st.text_area("説明文", key=f"new_desc_{group_id}")
                    
                    is_limited = st.checkbox("1人あたりの購入回数を制限する", key=f"limit_check_{group_id}")
                    limit_val = None
                    if is_limited:
                        limit_val = st.number_input("上限回数", min_value=1, value=1, step=1, key=f"limit_val_{group_id}")

                    if st.button("入荷する", key=f"add_btn_{group_id}", type="primary"):
                        if new_name:
                            api.add_shop_item(group_id, new_name, new_cost, new_desc, limit_per_user=limit_val)
                            st.success("入荷しました！"); time.sleep(1); st.rerun()

                with sub_tabs[2]:
                    st.subheader("在庫管理")
                    for item in items:
                        with st.container(border=True):
                            ca, cb = st.columns([4, 1])
                            ca.write(f"**{item['item_name']}**")
                            if cb.button("🗑️", key=f"del_{group_id}_{item['id']}", use_container_width=True):
                                api.delete_shop_item(item['id'])
                                st.rerun()
                                
                with sub_tabs[3]:
                    st.subheader("📜 みんなの購入記録")
                    if not group_history:
                        st.info("まだ誰もアイテムを購入していません。")
                    else:
                        for h in group_history:
                            with st.container(border=True):
                                st.write(f"👤 **{h.get('user_name', 'メンバー')}** が 🎁 **{h.get('item_name', 'アイテム')}** を購入")
                                st.caption(f"💰 {h.get('cost_points', '---')} pt | 購入日: {h.get('created_at', '')[:10]}")

            else:
                # --- 子供専用タブ ---
                with sub_tabs[1]:
                    st.subheader("📜 みんなの購入記録")
                    st.info("💡 買ったものは、この画面をホストに見せて交換してもらおう！")
                    if not group_history:
                        st.info("まだ誰もアイテムを購入していません。")
                    else:
                        for h in group_history:
                            with st.container(border=True):
                                st.write(f"👤 **{h.get('user_name', 'メンバー')}** が 🎁 **{h.get('item_name', 'アイテム')}** を購入")
                                st.caption(f"💰 {h.get('cost_points', '---')} pt | 購入日: {h.get('created_at', '')[:10]}")

    st.divider()
    if st.button("🏠 ホームに戻る", key="back_home"):
        st.session_state.current_page = "home"
        st.rerun()