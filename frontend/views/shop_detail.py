import streamlit as st
import time

def page_shop_detail():
    api = st.session_state.api
    
    # 1. 必要な情報の取得
    group_id = st.session_state.get("shop_group_id")
    if not group_id:
        st.error("グループが選択されていません")
        if st.button("戻る"):
            st.session_state.current_page = "shop"
            st.rerun()
        return

    # グループ詳細（アイテム一覧、メンバー情報含む）を取得
    group = api.get_group_detail(group_id)
    me = api.get_me()

    if "error" in group or "error" in me:
        st.error("データの取得に失敗しました")
        return

    # 2. 権限とポイントの確認
    my_id = me["id"]
    
    # 自分の情報を特定
    my_member_info = next((m for m in group["users"] if m["id"] == my_id), None)
    if not my_member_info:
        st.error("あなたはこのグループのメンバーではありません")
        return

    my_points = my_member_info["points"]
    is_host = my_member_info["is_host"]
    if group["owner_user_id"] == my_id:
        is_host = True

    # === 画面描画 ===
    
    # ヘッダー
    col_head1, col_head2 = st.columns([1, 3])
    with col_head1:
        if st.button("← お店を出る"):
            st.session_state.current_page = "shop"
            st.rerun()
    with col_head2:
        st.title(f"🛍️ {group['group_name']} 雑貨店")

    # 所持ポイント表示
    st.markdown(f"""
    <div style="background-color: #f0f2f6; padding: 15px; border-radius: 10px; margin-bottom: 20px; text-align: center;">
        <h3 style="margin:0; color: #555;">💰 所持ポイント: <span style="color: #d63384; font-size: 1.5em;">{my_points} pt</span></h3>
    </div>
    """, unsafe_allow_html=True)

    # ------------------------------
    # 3. ホスト用：アイテム追加エリア
    # ------------------------------
    if is_host:
        with st.expander("🛠️ 店主メニュー：商品を入荷する"):
            st.write("新しいアイテムをショップに並べます")
            
            # --- ここから st.form を使わずに直接ウィジェットを置きます ---
            
            # 1段目：商品名と価格
            c1, c2 = st.columns([3, 1])
            new_name = c1.text_input("商品名", placeholder="例: ポーション、肩たたき券", key="shop_new_name")
            new_cost = c2.number_input("価格 (pt)", min_value=1, value=100, step=10, key="shop_new_cost")
            
            # 2段目：説明文
            new_desc = st.text_area("説明文", placeholder="アイテムの効果や受け渡し方法など", key="shop_new_desc")
            
            # 3段目：購入制限設定
            # チェックボックスを変更すると即座に画面更新され、下の入力欄が出現します
            is_limited = st.checkbox("1人あたりの購入回数を制限する", key="shop_is_limited")
            
            limit_val = None
            if is_limited:
                st.caption("オプション設定")
                limit_val = st.number_input(
                    "上限回数", 
                    min_value=1, 
                    value=1, 
                    step=1,
                    help="1ユーザーが購入できる最大回数です",
                    key="shop_limit_val"
                )

            # 送信ボタン（通常のボタンなので、Enterキーでは発火しません）
            if st.button("入荷する", type="primary", key="shop_add_btn"):
                if not new_name:
                    st.warning("商品名を入力してください")
                else:
                    # 処理ロジックは前回と同じ
                    res = api.add_shop_item(
                        group_id, 
                        new_name, 
                        new_cost, 
                        new_desc, 
                        limit_per_user=limit_val 
                    )
                    
                    if "error" in res:
                        st.error(res["error"])
                    else:
                        st.success(f"「{new_name}」を入荷しました！")
                        time.sleep(1)
                        st.rerun()

    st.divider()

    # ------------------------------
    # 4. 商品一覧エリア
    # ------------------------------
    items = group.get("shops", []) # APIのレスポンスに合わせてキーは "shops"

    if not items:
        st.info("📦 現在、販売されているアイテムはありません。")
    else:
        st.subheader(f"商品一覧 ({len(items)})")
        
        # グリッド表示 (2列)
        cols = st.columns(2)
        for i, item in enumerate(items):
            with cols[i % 2]:
                with st.container(border=True):
                    st.subheader(item['item_name'])
                    st.caption(item.get('description') or "説明なし")
                    st.markdown(f"**価格:** `{item['cost_points']} pt`")
                    
                    # ボタンエリア
                    action_col1, action_col2 = st.columns(2)
                    
                    # 購入ボタン
                    with action_col1:
                        can_buy = my_points >= item['cost_points']
                        btn_label = "購入する" if can_buy else "Pt不足"
                        
                        if st.button(btn_label, key=f"buy_{item['id']}", disabled=not can_buy, type="primary" if can_buy else "secondary"):
                            # 購入API呼び出し
                            res = api.purchase_item(item['id'])
                            if "error" in res:
                                st.error(res["error"])
                            else:
                                st.balloons() # お祝いエフェクト
                                st.success(f"「{item['item_name']}」を購入しました！")
                                time.sleep(1.5)
                                st.rerun()

                    # 削除ボタン（ホストのみ）
                    if is_host:
                        with action_col2:
                            if st.button("🗑️ 削除", key=f"del_{item['id']}"):
                                res = api.delete_shop_item(item['id'])
                                if "error" in res:
                                    st.error(res["error"])
                                else:
                                    st.toast("商品を削除しました")
                                    time.sleep(1)
                                    st.rerun()