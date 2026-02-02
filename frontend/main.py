import streamlit as st
import requests
import os

# --- 環境設定 ---
API_URL = os.getenv("BACKEND_API_URL", "http://backend:8000")
API_KEY = os.getenv("APP_API_KEY")
IMG_BASE_URL = "http://localhost:8000"

st.set_page_config(page_title="HomeQuest", layout="wide")

# --- セッション初期化 ---
if "token" not in st.session_state:
    st.session_state.token = None
if "user" not in st.session_state:
    st.session_state.user = None

# --- ヘルパー関数 ---
def get_headers(auth=True, multipart=False):
    headers = {"X-App-Key": API_KEY}
    if auth and st.session_state.token:
        headers["Authorization"] = f"Bearer {st.session_state.token}"
    return headers

def login(user_id, password):
    try:
        response = requests.post(
            f"{API_URL}/token",
            data={"username": str(user_id), "password": password},
            headers=get_headers(auth=False)
        )
        if response.status_code == 200:
            st.session_state.token = response.json()["access_token"]
            st.success("ログイン成功！")
            st.rerun()
        else:
            st.error("ログイン失敗: IDかパスワードが違います")
    except Exception as e:
        st.error(f"接続エラー: {e}")

def signup(user_name, password):
    try:
        # ユーザー作成 API を叩く
        res = requests.post(
            f"{API_URL}/users/",
            json={"user_name": user_name, "password": password},
            headers=get_headers(auth=False)
        )
        if res.status_code == 200:
            new_user = res.json()
            st.success(f"登録成功！ あなたのIDは 【 {new_user['id']} 】 です。忘れないようにメモしてください！")
            st.info("左のメニューから「ログイン」に切り替えて、このIDでログインしてください。")
        else:
            st.error(f"登録失敗: {res.text}")
    except Exception as e:
        st.error(f"接続エラー: {e}")

def create_group(user_id, group_name):
    try:
        res = requests.post(
            f"{API_URL}/groups/",
            json={"group_name": group_name, "owner_user_id": user_id},
            headers=get_headers()
        )
        if res.status_code == 200:
            st.success(f"グループ '{group_name}' を作成しました！")
            st.rerun()
        else:
            st.error(f"作成失敗: {res.text}")
    except Exception as e:
        st.error(f"エラー: {e}")

def get_current_user():
    if not st.session_state.token:
        return None
    try:
        res = requests.get(f"{API_URL}/users/me", headers=get_headers())
        if res.status_code == 200:
            return res.json()
    except:
        pass
    return None

# --- メインアプリ画面 ---
def main_app():
    user = get_current_user()
    if not user:
        st.session_state.token = None
        st.rerun()
        return

    # サイドバー
    st.sidebar.title(f"👤 {user['user_name']}")
    if st.sidebar.button("ログアウト"):
        st.session_state.token = None
        st.rerun()

    # グループ情報の取得
    try:
        res = requests.get(f"{API_URL}/users/{user['id']}/groups", headers=get_headers())
        groups = res.json() if res.status_code == 200 else []
    except:
        st.error("サーバー通信エラー")
        return

    # --- グループ未所属の場合：グループ作成画面を表示 ---
    if not groups:
        st.warning("まだグループに参加していません。")
        st.subheader("🏠 新しいグループ（家）を作る")
        new_group_name = st.text_input("グループ名（例: 佐藤家, チームA）")
        if st.button("グループ作成"):
            if new_group_name:
                create_group(user['id'], new_group_name)
            else:
                st.error("グループ名を入力してください")
        return

    # --- 以下、通常画面 ---
    group_options = {g['group_name']: g['id'] for g in groups}
    selected_group_name = st.sidebar.selectbox("グループ選択", list(group_options.keys()))
    group_id = group_options[selected_group_name]

    # グループ詳細取得
    g_res = requests.get(f"{API_URL}/groups/{group_id}", headers=get_headers())
    if g_res.status_code != 200:
        st.error("グループ取得失敗")
        return
    group_data = g_res.json()
    
    my_info = next((u for u in group_data['users'] if u['id'] == user['id']), None)
    is_host = my_info['is_host'] if my_info else False

    st.title(f"🏠 {group_data['group_name']}")
    
    tab1, tab2, tab3 = st.tabs(["📜 クエスト", "💎 ショップ", "👥 メンバー"])

    # [クエストタブ]
    with tab1:
        st.header("クエストボード")
        if is_host:
            st.info("🛡️ 管理者メニュー: 報告の承認")
            sub_res = requests.get(f"{API_URL}/groups/{group_id}/submissions", headers=get_headers())
            if sub_res.status_code == 200:
                submissions = sub_res.json()
                if not submissions:
                    st.write("承認待ちの報告はありません")
                for sub in submissions:
                    with st.expander(f"報告: {sub['quest_title']} (User: {sub['user_id']})"):
                        if sub['proof_image_path']:
                            st.image(f"{IMG_BASE_URL}/{sub['proof_image_path']}", width=300)
                        c1, c2 = st.columns(2)
                        with c1:
                            if st.button("承認", key=f"ok_{sub['id']}"):
                                requests.post(f"{API_URL}/submissions/{sub['id']}/review", json={"approved": True}, headers=get_headers())
                                st.rerun()
                        with c2:
                            if st.button("却下", key=f"ng_{sub['id']}"):
                                requests.post(f"{API_URL}/submissions/{sub['id']}/review", json={"approved": False}, headers=get_headers())
                                st.rerun()
            st.divider()

        # クエスト一覧と報告
        quests = group_data.get("quests", [])
        for q in quests:
            with st.container(border=True):
                c1, c2 = st.columns([3, 2])
                c1.subheader(q['quest_name'])
                c1.write(f"報酬: {q['reward_points']} pt | {q['description']}")
                
                uploaded_file = c2.file_uploader("写真", type=['jpg','png'], key=f"u_{q['id']}")
                if c2.button("報告する", key=f"b_{q['id']}"):
                    if uploaded_file:
                        files = {"file": (uploaded_file.name, uploaded_file, uploaded_file.type)}
                        requests.post(f"{API_URL}/quests/{q['id']}/complete", headers=get_headers(multipart=True), files=files)
                        st.success("報告しました！")
                    else:
                        st.error("写真が必要です")

    # [ショップタブ]
    with tab2:
        st.header("ショップ")
        for s in group_data.get("shops", []):
            with st.container(border=True):
                c1, c2 = st.columns([3,1])
                c1.write(f"**{s['item_name']}** ({s['cost_points']} pt)")
                if c2.button("交換", key=f"s_{s['id']}"):
                    if my_info['points'] >= s['cost_points']:
                        requests.post(f"{API_URL}/shops/{s['id']}/purchase", headers=get_headers())
                        st.balloons()
                        st.rerun()
                    else:
                        st.error("ポイント不足")

    # [メンバータブ]
    with tab3:
        st.header("メンバー")
        for m in sorted(group_data.get("users", []), key=lambda x: x['points'], reverse=True):
            role = "👑" if m['is_host'] else "👤"
            st.write(f"{role} {m['user_name']} : {m['points']} pt")

# --- エントリーポイント (ログイン/登録切り替え) ---
if not st.session_state.token:
    st.title("🏠 HomeQuest")
    
    # サイドバーで切り替え
    auth_mode = st.sidebar.radio("メニュー", ["ログイン", "新規登録"])
    
    if auth_mode == "新規登録":
        st.header("新規ユーザー登録")
        new_name = st.text_input("ユーザー名（ニックネーム）")
        new_pass = st.text_input("パスワード", type="password")
        if st.button("登録する"):
            if new_name and new_pass:
                signup(new_name, new_pass)
            else:
                st.error("すべて入力してください")
                
    else:
        st.header("ログイン")
        uid = st.text_input("ユーザーID (数字)")
        pwd = st.text_input("パスワード", type="password")
        if st.button("ログイン"):
            if uid.isdigit():
                login(uid, pwd)
            else:
                st.error("IDは数字で入力してください")
else:
    main_app()