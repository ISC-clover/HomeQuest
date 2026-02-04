import streamlit as st
from PIL import Image

def page_quest_report():
    st.title("📸 クエスト報告")
    
    api = st.session_state.api
    quest_id = st.session_state.get("report_quest_id")
    
    if not quest_id:
        st.error("クエストが選択されていません")
        if st.button("戻る"):
            st.session_state.current_page = "quests"
            st.rerun()
        return

    # クエスト情報を再取得できないため（IDしか持ってきていない）、
    # 本来はAPIでget_quest(id)すべきですが、簡易的に表示だけ行います
    
    if st.button("← キャンセルして戻る"):
        st.session_state.current_page = "quests"
        del st.session_state["report_quest_id"]
        st.rerun()

    st.markdown("###証拠写真をアップロードしてください")
    
    uploaded_file = st.file_uploader("画像を選択", type=["jpg", "jpeg", "png"])
    
    if uploaded_file is not None:
        # プレビュー表示
        image = Image.open(uploaded_file)
        st.image(image, caption='送信する画像', use_container_width=True)
        
        if st.button("送信する", type="primary"):
            with st.spinner("送信中..."):
                # API呼び出し
                res = api.complete_quest(
                    quest_id, 
                    uploaded_file, # ファイルオブジェクト
                    uploaded_file.name, 
                    uploaded_file.type
                )
                
                if "error" in res:
                    st.error(res["error"])
                else:
                    st.success("提出しました！ホストの承認をお待ちください。")
                    # 状態をクリアして一覧に戻る
                    del st.session_state["report_quest_id"]
                    import time
                    time.sleep(1.5)
                    st.session_state.current_page = "quests"
                    st.rerun()