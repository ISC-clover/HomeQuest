import time
import streamlit as st
import base64  # 背景画像を読み込むために必要

def page_shop_detail():
    # --- 🖼️ 背景画像の設定 (Base64変換) ---
    # shop.png を読み込んで、CSSで背景に設定します
    bg_img_path = "static/images/shop.png" 
    
    try:
        with open(bg_img_path, "rb") as f:
            data = f.read()
            bin_str = base64.b64encode(data).decode()
        bg_css = f'url("data:image/png;base64,{bin_str}")'
    except:
        # 画像がない場合の予備（落ち着いたダークブラウン）
        bg_css = "#3e2723"

    # ==========================================
    # 💻 [修正] カスタムCSS
    #  背景画像の組み込みと、それに合わせたUI調整
    # ==========================================
    st.markdown(f"""
    <style>
        /* 画面全体の背景 */
        [data-testid="stAppViewContainer"] {{
            background-image: {bg_css};
            background-size: cover;
            background-position: center;
            background-attachment: fixed; /* スクロールしても背景は固定 */
            color: #d7ccc8;
        }}
        [data-testid="stHeader"] {{
            background-color: rgba(0,0,0,0); /* ヘッダーを透明に */
        }}

        /* 木札風のタイトル看板 */
        .shop-sign {{
            background-color: rgba(141, 110, 99, 0.9); /* 少し透明に */
            border: 6px solid #bcaaa4;
            border-radius: 15px;
            padding: 20px;
            text-align: center;
            box-shadow: 0 4px 8px rgba(0,0,0,0.5);
            margin-bottom: 30px;
            /* margin-top: -50px; 画像に合わせて調整するため、一旦コメントアウト */
        }}
        .shop-sign h1 {{
            margin: 0;
            color: #fff8e1; /* 文字色を明るく */
            font-family: 'Courier New', Courier, monospace;
            font-weight: bold;
            text-shadow: 2px 2px 2px rgba(0,0,0,0.5); /* 文字に影を付ける */
        }}

        /* 羊皮紙風のポイント表示エリア */
        .point-scroll {{
            background-color: rgba(255, 248, 225, 0.9); /* 少し透明に */
            border: 4px solid #bcaaa4;
            border-radius: 5px;
            padding: 15px;
            margin-bottom: 25px;
            text-align: center;
            box-shadow: inset 0 0 15px rgba(141, 110, 99, 0.5);
            color: #3e2723;
        }}
        .point-scroll h3 {{
            margin: 0;
            color: #5d4037;
            font-size: 1.1em;
        }}
        .point-value {{
            color: #c2185b;
            font-size: 1.8em;
            font-weight: bold;
        }}

        /* 商品棚 (Shelf) のデザイン */
        .shop-shelf-container {{
            border: 10px solid #5d4037;
            background-color: rgba(62, 39, 35, 0.8); /* 画像が透けるように半透明に */
            padding: 25px;
            border-radius: 10px;
            box-shadow: 0 10px 20px rgba(0,0,0,0.7);
            margin-bottom: 30px;
            backdrop-filter: blur(2px); /* 背景を少しぼかす */
        }}

        /* 商品アイテムカード */
        .item-card {{
            background-color: rgba(215, 204, 200, 0.95); /* カードも少し透明に */
            border: 2px solid #a1887f;
            border-radius: 8px;
            padding: 18px;
            margin: 12px 0;
            box-shadow: 2px 2px 5px rgba(0,0,0,0.3);
            transition: transform 0.2s;
            height: 100%;
            color: #3e2723;
        }}
        .item-card:hover {{
            transform: translateY(-3px);
        }}
        .item-card h3 {{
            color: #5d4037;
            margin-top: 0;
            font-size: 1.3em;
        }}

        /* アイテム価格とボタンエリアのレイアウト */
        .item-action-area {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-top: 15px;
            padding-top: 10px;
            border-top: 1px solid #bcaaa4;
        }}
        .item-price {{
            font-size: 1.2em;
            font-weight: bold;
            color: #3e2723;
        }}
        .item-price code {{
            background-color: rgba(0,0,0,0.1);
            color: #d81b60;
            padding: 2px 5px;
            border-radius: 3px;
        }}
        
        /* 店主メニュー (st.expander) のデザイン */
        .stExpander {{
            background-color: rgba(141, 110, 99, 0.5); /* 透明度を上げる */
            border: 2px solid #a1887f;
            border-radius: 8px;
            margin-bottom: 20px;
            backdrop-filter: blur(2px);
        }}

        /* ボタンの色を変更して見やすく */
        .stButton button {{
            color: white !important;
            background-color: #4CAF50 !important;
            border-color: #4CAF50 !important;
        }}
        .stButton button:hover {{
            background-color: #45a049 !important;
            border-color: #45a049 !important;
        }}
        .stButton button:disabled {{
            background-color: #cccccc !important;
            color: #666666 !important;
        }}
    </style>
    """, unsafe_allow_html=True)

    # === [ここから画面描画] ===
    api = st.session_state.api
    
    # 1. 必要な情報の取得
    group_id = st.session_state.get("shop_group_id")
    if not group_id:
        st.error("グループが選択されていません")
        if st.button("戻る", key="back_to_shop_btn"):
            st.session_state.current_page = "shop"
            st.rerun()
        return

    # グループ詳細を取得
    group = api.get_group_detail(group_id)
    me = api.get_me()

    if "error" in group or "error" in me:
        st.error("データの取得に失敗しました")
        return

    # 自分の情報を特定
    my_member_info = next((m for m in group["users"] if m["id"] == me["id"]), None)
    if not my_member_info:
        st.error("あなたはこのグループのメンバーではありません")
        return

    my_points = my_member_info["points"]
    is_host = my_member_info.get("is_host", False) or (group["owner_user_id"] == me["id"])

    # 木札風のヘッダー看板
    st.markdown(f"""
    <div class="shop-sign">
        <h1>🛍️ {group['group_name']} のショップ</h1>
    </div>
    """, unsafe_allow_html=True)

    # 「お店を出る」ボタン
    if st.button("← 店を出る", key="exit_shop_btn"):
        st.session_state.current_page = "shop"
        st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)

    # 羊皮紙風の所持ポイント表示
    st.markdown(f"""
    <div class="point-scroll">
        <h3>💰 現在の所持ポイント</h3>
        <p class="point-value">{my_points} pt</p>
    </div>
    """, unsafe_allow_html=True)

    # ------------------------------
    # 3. ホスト用：アイテム追加エリア
    # ------------------------------
    if is_host:
        with st.expander("⚒️ 店主メニュー：新しい商品を入荷する"):
            st.write("ショップの棚に新しいアイテムを並べます")
            
            # 1段目：商品名と価格
            c1, c2 = st.columns([3, 1])
            new_name = c1.text_input("商品名", placeholder="例: ポーション、英雄の剣", key="shop_new_name")
            new_cost = c2.number_input("価格 (pt)", min_value=1, value=100, step=10, key="shop_new_cost")
            
            # 2段目：説明文
            new_desc = st.text_area("説明文", placeholder="アイテムの効果や受け渡し方法など", key="shop_new_desc")
            
            # 3段目：購入制限設定
            is_limited = st.checkbox("購入回数を制限する", key="shop_is_limited")
            
            limit_val = None
            if is_limited:
                st.caption("オプション設定")
                limit_val = st.number_input("上限回数", min_value=1, value=1, step=1, key="shop_limit_val")

            # 送信ボタン
            if st.button("入荷する", type="primary", key="shop_add_btn", use_container_width=True):
                if not new_name:
                    st.warning("商品名を入力してください")
                else:
                    res = api.add_shop_item(group_id, new_name, new_cost, new_desc, limit_per_user=limit_val)
                    if "error" in res:
                        st.error(res["error"])
                    else:
                        st.success(f"「{new_name}」を入荷しました！")
                        time.sleep(1)
                        st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)

    # ------------------------------
    # 4. 商品一覧エリア
    # ------------------------------
    items = group.get("shops", [])

    if not items:
        st.markdown(f"""
        <div class="point-scroll">
            <h2 style="color: #3e2723; margin:0;">📦 商品入荷待ち...</h2>
            <p style="color: #5d4037; margin-top:10px;">店主が商品を並べるのを待ちましょう。</p>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.subheader(f"⚔️ ショップの棚 ({len(items)})")
        
        # 商品棚 (Shelf) の枠組みを開始
        st.markdown('<div class="shop-shelf-container">', unsafe_allow_html=True)

        shelf_cols = st.columns(2)
        
        for i, item in enumerate(items):
            # 棚の列を特定
            with shelf_cols[i % 2]:
                
                # アイテムカードを描画
                st.markdown(f"""
                <div class="item-card">
                    <div>
                        <h3>{item['item_name']}</h3>
                        <p class="description">{item.get('description') or "説明なし"}</p>
                    </div>
                    <div class="item-action-area">
                        <div class="item-price">価格: <code>{item['cost_points']} pt</code></div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                # ボタンエリア
                action_col1, action_col2 = st.columns([2, 1]) # 購入ボタンを大きく

                # 購入ボタン
                with action_col1:
                    can_buy = my_points >= item['cost_points']
                    btn_label = "購入する" if can_buy else "Pt不足"
                    if st.button(btn_label, key=f"buy_{item['id']}", disabled=not can_buy, type="primary" if can_buy else "secondary", use_container_width=True):
                        res = api.purchase_item(item['id'])
                        if "error" in res:
                            st.error(res["error"])
                        else:
                            st.balloons() # お祝いエフェクト
                            st.success(f"購入しました！")
                            time.sleep(1.5)
                            st.rerun()

                # 削除ボタン（ホストのみ）
                if is_host:
                    with action_col2:
                        st.markdown('<div class="del-button-container">', unsafe_allow_html=True)
                        if st.button("🗑️", key=f"del_{item['id']}", help="商品を削除", use_container_width=True):
                            api.delete_shop_item(item['id'])
                            st.rerun()
                        st.markdown('</div>', unsafe_allow_html=True)

                st.markdown("<br>", unsafe_allow_html=True) # アイテム間の隙間

        # 商品棚の枠組みを終了
        st.markdown('</div>', unsafe_allow_html=True)