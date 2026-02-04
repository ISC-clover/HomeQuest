import streamlit as st

def page_groups():
    st.title("🛡️ グループ管理")
    
    api = st.session_state.api
    me = api.get_me()
    
    if "error" in me:
        st.error("ユーザー情報の取得に失敗しました")
        return

    # -------------------------------------------
    # 処理を行う関数（コールバック）の定義
    # -------------------------------------------
    # これらはボタンが押された瞬間に（画面再描画の前に）実行されます
    
    def handle_create_group():
        # session_stateから現在の入力値を取得
        name = st.session_state.input_create_group_name
        
        if not name:
            st.session_state.group_msg = {"type": "warning", "text": "グループ名を入力してください"}
            return

        res = api.create_group(name)
        
        if "error" in res:
            st.session_state.group_msg = {"type": "error", "text": res["error"]}
        else:
            st.session_state.group_msg = {"type": "success", "text": f"グループ「{res['group_name']}」を作成しました！"}
            # ★ここで値をクリアしてもエラーになりません（再描画前なので）
            st.session_state.input_create_group_name = ""

    def handle_join_group():
        code = st.session_state.input_join_code
        
        if not code:
            st.session_state.group_msg = {"type": "warning", "text": "招待コードを入力してください"}
            return
            
        res = api.join_group(code)
        
        if "error" in res:
            st.session_state.group_msg = {"type": "error", "text": res["error"]}
        else:
            st.session_state.group_msg = {"type": "success", "text": res.get("message", "参加しました！")}
            # 入力欄をクリア
            st.session_state.input_join_code = ""

    # -------------------------------------------
    # 画面描画（メイン処理）
    # -------------------------------------------

    # もしコールバック関数でセットされたメッセージがあれば、ここで表示する
    if "group_msg" in st.session_state:
        msg = st.session_state.group_msg
        if msg["type"] == "success":
            st.success(msg["text"])
        elif msg["type"] == "error":
            st.error(msg["text"])
        elif msg["type"] == "warning":
            st.warning(msg["text"])
        # 表示したら消す（次回残らないように）
        del st.session_state.group_msg

    # タブの描画
    tab1, tab2, tab3 = st.tabs(["参加中のグループ", "新規作成", "グループに参加"])

    # 1. 参加中のグループ
    with tab1:
        st.subheader("あなたの所属グループ")
        my_groups = api.get_my_groups(me['id'])
        
        if not my_groups:
            st.info("まだグループに参加していません。")
        else:
            for group in my_groups:
                with st.expander(f"🏰 {group['group_name']} (ID: {group['id']})"):
                    st.write(f"オーナーID: {group['owner_user_id']}")
                    
                    # 詳細画面へ遷移するボタン
                    if st.button("詳細・管理へ", key=f"btn_detail_{group['id']}"):
                        st.session_state.selected_group_id = group['id'] # IDを保存
                        st.session_state.current_page = "group_detail"   # ページ切り替え
                        st.rerun()

    # 2. 新規作成
    with tab2:
        st.subheader("新しいギルドを立ち上げる")
        # keyを指定しておくと、コールバック内で st.session_state.input_create_group_name として値を取れます
        st.text_input("グループ名", key="input_create_group_name")
        
        # on_click に関数名を渡すのがポイントです（()を付けないこと）
        st.button("作成する", type="primary", on_click=handle_create_group)

    # 3. 参加（招待コード）
    with tab3:
        st.subheader("招待コードで参加")
        st.text_input("招待コードを入力", key="input_join_code")
        
        st.button("参加する", type="primary", on_click=handle_join_group)
    
    st.divider()
    if st.button("🏠 ホームに戻る"):
        st.session_state.current_page = "home"
        st.rerun()