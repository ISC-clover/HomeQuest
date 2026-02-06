import streamlit as st

def page_shop():
    st.title("🛍️ ショップ")
    st.write("ショップを開くグループを選択してください")

    api = st.session_state.api
    
    # ユーザー情報取得
    me = api.get_me()
    if "error" in me:
        st.error("ログイン情報を取得できませんでした")
        return

    # 参加グループ取得
    my_groups = api.get_my_groups(me["id"])
    if not my_groups:
        st.info("まだグループに参加していません")
        if st.button("🏠 ホームに戻る"):
            st.session_state.current_page = "home"
            st.rerun()
        return

    # グループ一覧表示
    for group in my_groups:
        with st.container(border=True):
            col1, col2 = st.columns([3, 1])
            with col1:
                st.subheader(f"🏰 {group['group_name']}")
            with col2:
                # ショップ画面へ遷移するボタン
                if st.button("入店する", key=f"shop_enter_{group['id']}", type="primary", use_container_width=True):
                    st.session_state.shop_group_id = group['id'] # ショップ用のIDを保存
                    st.session_state.current_page = "shop_detail"
                    st.rerun()
    st.divider()
    if st.button("🏠 ホームに戻る"):
        st.session_state.current_page = "home"
        st.rerun()