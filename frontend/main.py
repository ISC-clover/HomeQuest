import os
import streamlit as st
from hq_api import HomeQuestAPI
from views import home, groups, quests, shop, group_detail, quest_manage, shop_detail, quest_report, quest_review

# --- 1. 設定と初期化 ---
st.set_page_config(page_title="HomeQuest", layout="centered")

API_URL = os.getenv("BACKEND_API_URL", "http://backend:8000")
API_KEY = os.getenv("APP_API_KEY", "your_api_key")
IMAGE_BASE_URL = os.getenv("IMAGE_BASE_URL", "http://localhost:8000")

if "api" not in st.session_state:
    st.session_state.api = HomeQuestAPI(API_URL, API_KEY, IMAGE_BASE_URL)

if "current_page" not in st.session_state:
    st.session_state.current_page = "home"

if "is_logged_in" not in st.session_state:
    st.session_state.is_logged_in = False

# --- 2. ログイン画面 ---
def page_login_signup():
    st.title("⚔️ HomeQuest - ログイン")
    tab1, tab2 = st.tabs(["ログイン", "新規登録"])
    
    with tab1:
        # st.formで囲んでEnterキーでの送信を可能にする
        with st.form(key="login_form"):
            id_input = st.text_input("ユーザーID", max_chars=100)
            pass_input = st.text_input("パスワード", type="password", max_chars=100)
            login_button = st.form_submit_button("ログイン")

        if login_button:
            # 修正: True/False ではなく、レスポンスデータ（辞書）を受け取るように変更
            login_data = st.session_state.api.login(id_input, pass_input)
            
            if login_data:
                st.session_state.is_logged_in = True
                
                # --- 【重要】初回ログイン判定によるページ振り分け ---
                #  is_first_login を参照します
                if login_data.get("is_first_login"):
                    st.session_state.current_page = "groups"  # 2枚目の画像（グループ作成）へ
                else:
                    st.session_state.current_page = "home"    # 1枚目の画像（ホーム）へ
                
                st.rerun()
            else:
                st.error("ログイン失敗：IDまたはパスワードが違います")

    with tab2:
        with st.form(key="signup_form"):
            # schemas.pyに合わせて max_chars=100 を追加（100文字以上打ち込めなくする）
            new_name = st.text_input("ユーザー名", max_chars=100)
            new_pass = st.text_input("パスワード", type="password", max_chars=100)
            signup_button = st.form_submit_button("登録")

        if signup_button:
            # 入力値の検証
            if not new_name or new_name.isspace():
                st.error("ユーザー名を入力してください")
            elif len(new_name) > 100: # コピペ等でのすり抜け対策
                st.error("ユーザー名は100文字以内で入力してください")
            elif not new_pass or new_pass.isspace():
                st.error("パスワードを入力してください")
            elif len(new_pass) > 100:
                st.error("パスワードは100文字以内で入力してください")
            else:
                res = st.session_state.api.signup(new_name, new_pass)
                if "error" in res:
                    st.error(res["error"])
                else:
                    st.success(f"登録完了！あなたのIDは {res['id']} です。忘れずに記録してください。")

# --- 3. メインルーティング ---
def main():
    if not st.session_state.is_logged_in:
        page_login_signup()
        return

    # ルーティング分岐
    if st.session_state.current_page == "home":
        home.page_home()
    elif st.session_state.current_page == "groups":
        groups.page_groups()
    elif st.session_state.current_page == "group_detail":
        group_detail.page_group_detail()
    elif st.session_state.current_page == "shop":
        shop.page_shop()
    elif st.session_state.current_page == "shop_detail":
        shop_detail.page_shop_detail()
    elif st.session_state.current_page == "quests":
        quests.page_quests()
    elif st.session_state.current_page == "quest_manage":
        quest_manage.page_quest_manage()
    elif st.session_state.current_page == "quest_report":
        quest_report.page_quest_report()
    elif st.session_state.current_page == "quest_review":
        quest_review.page_quest_review()
    else:
        home.page_home()
    
if __name__ == "__main__":
    main()