import time
import streamlit as st
import base64
from datetime import datetime as dt

def page_shop():
    # --- 🖼️ 背景画像の設定 (shop.png を使用) ---
    bg_img_path = "static/images/shop.png" 
    try:
        with open(bg_img_path, "rb") as f:
            data = f.read()
            bin_str = base64.b64encode(data).decode()
        bg_css = f'url("data:image/png;base64,{bin_str}")'
    except:
        bg_css = "#3e2723" # 画像がない場合の予備色

    # === 🌟 ファンタジーCSS注入 ===
    st.markdown(f"""
    <style>
        /* 全体背景: 商店街の画像を表示 */
        [data-testid="stAppViewContainer"] {{
            background-image: {bg_css};
            background-size: cover;
            background-position: center;
            background-attachment: fixed;
            color: #d7ccc8;
        }}
        [data-testid="stHeader"] {{
            background-color: rgba(0,0,0,0);
        }}
        
        /* タイトル看板 */
        .main-title {{
            background-color: rgba(62, 39, 35, 0.85);
            border: 5px solid #8d6e63;
            border-radius: 15px;
            padding: 20px;
            text-align: center;
            margin-bottom: 25px;
            box-shadow: 0 10px 20px rgba(0,0,0,0.5);
        }}

        /* タブ（お店の看板風） */
        .stTabs [data-baseweb="tab-list"] {{
            gap: 8px;
            background-color: rgba(93, 64, 55, 0.8);
            padding: 10px 10px 0 10px;
            border-radius: 10px 10px 0 0;
        }}
        .stTabs [data-baseweb="tab"] {{
            background-color: rgba(141, 110, 99, 0.6);
            border-radius: 5px 5px 0 0;
            color: #fff;
            padding: 10px 20px;
            border: none;
        }}
        .stTabs [aria-selected="true"] {{
            background-color: #fff8e1 !important;
            color: #3e2723 !important;
            font-weight: bold;
        }}

        /* 所持ポイント（羊皮紙風） */
        .point-banner {{
            background-color: rgba(255, 248, 225, 0.9);
            border: 3px solid #bcaaa4;
            border-radius: 5px;
            padding: 15px;
            text-align: center;
            margin-bottom: 20px;
            box-shadow: inset 0 0 15px rgba(141, 110, 99, 0.5);
            color: #3e2723;
        }}

        /* 商品棚の枠組み */
        .shelf-container {{
            background-color: rgba(43, 29, 26, 0.8);
            border: 8px solid #5d4037;
            padding: 20px;
            border-radius: 10px;
            margin-top: 10px;
            backdrop-filter: blur(3px);
        }}

        /* 商品カード */
        .item-card {{
            background-color: rgba(215, 204, 200, 0.95);
            border: 2px solid #a1887f;
            border-radius: 8px;
            padding: 15px;
            color: #3e2723;
            height: 100%;
            box-shadow: 2px 2px 5px rgba(0,0,0,0.3);
        }}
        
        /* 履歴（掲示板風） */
        .history-card {{
            background-color: rgba(255, 248, 225, 0.1);
            border-left: 5px solid #8d6e63;
            padding: 12px;
            margin-bottom: 8px;
            color: #fff8e1;
        }}

        /* ボタンの調整 */
        .stButton button {{
            border-radius: 5px;
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

    st.markdown('<div class="main-title"><h1>🛍️ ショップ</h1></div>', unsafe_allow_html=True)
    
    # --- 🌟 セッション管理 ---
    if "local_bought" not in st.session_state:
        st.session_state.local_bought = {}
    
    api = st.session_state.api
    me = api.get_me()
    
    if "error" in me:
        st.error("ログイン情報を取得できませんでした")
        return

    my_groups = api.get_my_groups(me["id"])
    if not my_groups:
        st.info("まだどのグループにも所属していないようです。")
        if st.button("🏠 広場に戻る"):
            st.session_state.current_page = "home"
            st.rerun()
        return

    # --- 🌟 便利関数 ---
    def format_time(iso_str):
        if not iso_str: return "日時不明"
        try:
            parsed = dt.fromisoformat(str(iso_str).replace('Z', '+00:00'))
            return parsed.strftime("%Y/%m/%d %H:%M")
        except:
            return str(iso_str)[:16].replace('T', ' ')

    # --- 自分の全購入履歴を取得 ---
    all_my_purchases = []
    try:
        res_my = api.get_my_purchases()
        if isinstance(res_my, list): all_my_purchases = res_my
        elif isinstance(res_my, dict):
            for key in ["purchases", "data", "items", "history"]:
                if key in res_my and isinstance(res_my[key], list):
                    all_my_purchases = res_my[key]
                    break
    except: pass

    # グループごとのタブを作成
    group_names = [f"🏰 {g['group_name']}" for g in my_groups]
    group_tabs = st.tabs(group_names)

    for idx, group_info in enumerate(my_groups):
        with group_tabs[idx]:
            group_id = group_info["id"]
            group = api.get_group_detail(group_id)
            
            if "error" in group:
                st.error(f"グループの情報を読み込めませんでした。")
                continue

            my_member_info = next((m for m in group["users"] if m["id"] == me["id"]), None)
            if not my_member_info:
                st.warning("メンバー登録が確認できませんでした。")
                continue

            my_points = my_member_info["points"]
            is_host = my_member_info.get("is_host", False) or (group["owner_user_id"] == me["id"])

            # 💰 所持ポイント表示
            st.markdown(f"""
            <div class="point-banner">
                <h4 style="margin:0;">💰 {group['group_name']} での所持金</h4>
                <div style="font-size: 1.8em; color: #d81b60; font-weight: bold;">{my_points} <small>pt</small></div>
            </div>
            """, unsafe_allow_html=True)

            # --- 履歴のカウントロジック ---
            group_history = []
            try:
                res_gh = api.get_purchase_history(group_id)
                if isinstance(res_gh, list): group_history = res_gh
                elif isinstance(res_gh, dict):
                    for key in ["purchases", "data", "items", "history"]:
                        if key in res_gh and isinstance(res_gh[key], list):
                            group_history = res_gh[key]
                            break
            except: pass

            purchase_counts_by_name = {}
            # 自分の購入分をカウント
            my_h = [h for h in group_history if h.get("user_id") == me["id"]] if group_history else all_my_purchases
            for h in my_h:
                name = h.get('item_name')
                if name: purchase_counts_by_name[name] = purchase_counts_by_name.get(name, 0) + 1

            # --- ギルド内メニュー（サブタブ） ---
            sub_titles = ["🛒 お買い物", "📜 履歴"]
            if is_host: sub_titles = ["🛒 お買い物", "🆕 入荷", "🛠️ 管理", "📜 全履歴"]
            sub_tabs = st.tabs(sub_titles)

            # --- [サブタブ0] お買い物 ---
            with sub_tabs[0]:
                items = group.get("shops", [])
                if not items:
                    st.info("📦 現在、このグループの棚には商品が並んでいないようです。")
                else:
                    st.markdown('<div class="shelf-container">', unsafe_allow_html=True)
                    cols = st.columns(2)
                    for i, item in enumerate(items):
                        with cols[i % 2]:
                            limit = item.get('limit_per_user')
                            bought_count = max(purchase_counts_by_name.get(item['item_name'], 0), st.session_state.local_bought.get(item['id'], 0))
                            is_limit_reached = limit is not None and limit > 0 and bought_count >= limit
                            limit_text = f" (残り {max(0, limit - bought_count)} 回)" if limit else ""
                            
                            st.markdown(f"""
                            <div class="item-card">
                                <h4 style="margin:0;">{item['item_name']}</h4>
                                <p style="font-size:0.85em; color:#5d4037; margin:5px 0;">{item.get('description') or "不思議なアイテム"}</p>
                                <div style="font-weight:bold; color:#d81b60;">💰 {item['cost_points']} pt<span style="font-size:0.8em; color:#8d6e63;">{limit_text}</span></div>
                            </div>
                            """, unsafe_allow_html=True)

                            # 購入アクション
                            has_enough = my_points >= item['cost_points']
                            can_buy = has_enough and not is_limit_reached
                            btn_label = "✅ 上限到達" if is_limit_reached else ("購入する" if has_enough else "Pt不足")
                            
                            if st.button(btn_label, key=f"buy_{group_id}_{item['id']}", disabled=not can_buy, type="primary" if can_buy else "secondary", use_container_width=True):
                                res = api.purchase_item(item['id'])
                                if "error" in res: st.error(res["error"])
                                else:
                                    st.session_state.local_bought[item['id']] = bought_count + 1
                                    st.balloons()
                                    st.success(f"「{item['item_name']}」を手に入れた！")
                                    time.sleep(1.2); st.rerun()
                            st.write("") 
                    st.markdown('</div>', unsafe_allow_html=True)

            # --- ホスト機能 ---
            if is_host:
                with sub_tabs[1]:
                    st.write("### ⚒️ 新しいアイテムを並べる")
                    if f"fk_{group_id}" not in st.session_state: st.session_state[f"fk_{group_id}"] = 0
                    fk = st.session_state[f"fk_{group_id}"]
                    
                    c1, c2 = st.columns([3, 1])
                    new_name = c1.text_input("商品名", key=f"n_{group_id}_{fk}")
                    new_cost = c2.number_input("価格(pt)", 1, 1000000, 100, key=f"c_{group_id}_{fk}")
                    new_desc = st.text_area("説明（効果や受け渡し方法）", key=f"d_{group_id}_{fk}")
                    
                    is_limited = st.checkbox("1人あたりの購入回数を制限する", key=f"lc_{group_id}_{fk}")
                    limit_val = st.number_input("購入上限回数", 1, 100, 1, key=f"lv_{group_id}_{fk}") if is_limited else None
                    
                    if st.button("商品を棚に並べる", key=f"add_{group_id}_{fk}", type="primary", use_container_width=True):
                        if new_name:
                            api.add_shop_item(group_id, new_name, new_cost, new_desc, limit_per_user=limit_val)
                            st.session_state[f"fk_{group_id}"] += 1
                            st.success(f"「{new_name}」を入荷しました！")
                            time.sleep(1); st.rerun()

                with sub_tabs[2]:
                    st.write("### 📦 在庫の整理")
                    for item in items:
                        with st.container(border=True):
                            ca, cb = st.columns([4, 1])
                            ca.write(f"**{item['item_name']}**\n\n{item['cost_points']} pt")
                            if cb.button("🗑️", key=f"del_{group_id}_{item['id']}", help="この商品を棚から下ろす", use_container_width=True):
                                api.delete_shop_item(item['id'])
                                st.rerun()

            # --- 履歴表示 ---
            history_tab_idx = 3 if is_host else 1
            with sub_tabs[history_tab_idx]:
                st.write("### 📜 最近の購入履歴")
                if not group_history:
                    st.info("まだ取引の記録はないようです。")
                else:
                    for h in group_history[:20]: # 直近20件
                        u_name = h.get('user_name') or h.get('username') or '旅人'
                        i_name = h.get('item_name') or '謎の宝'
                        pts = h.get('cost_points') or h.get('points') or '---'
                        date = format_time(h.get('created_at') or h.get('purchased_at') or '')
                        
                        st.markdown(f"""
                        <div class="history-card">
                            <span style="color:#bcaaa4; font-size:0.8em;">📜 {date}</span><br>
                            <b>{u_name}</b> が <b>{i_name}</b> を <b>{pts}pt</b> で手に入れたようだ。
                        </div>
                        """, unsafe_allow_html=True)

    st.divider()
    if st.button("🏠 ホームに戻る", key="back_home", use_container_width=True):
        st.session_state.current_page = "home"
        st.rerun()