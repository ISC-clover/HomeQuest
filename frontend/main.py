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
        id_input = st.text_input("ユーザーID", key="login_id")
        pass_input = st.text_input("パスワード", type="password", key="login_pass")
        if st.button("ログイン", type="primary"):
            if st.session_state.api.login(id_input, pass_input):
                st.session_state.is_logged_in = True
                st.rerun()
            else:
                st.error("ログイン失敗")

    with tab2:
        new_name = st.text_input("ユーザー名")
        new_pass = st.text_input("パスワード", type="password")
        if st.button("登録"):
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

    # ルーティング分岐を追加
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