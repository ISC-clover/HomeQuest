import requests
from typing import Optional, Dict, Any

class HomeQuestAPI:
    def __init__(self, api_url: str, api_key: str, image_base_url: str = None):
        self.api_url = api_url.rstrip("/")
        self.image_base_url = (image_base_url or api_url).rstrip("/")
        self.api_key = api_key
        self.token = None

    def get_full_image_url(self, path: str) -> Optional[str]:
        if not path:
            return None
        if path.startswith("http"):
            return path
        clean_path = path.lstrip("/")
        return f"{self.image_base_url}/{clean_path}"

    def _get_headers(self, multipart=False) -> Dict[str, str]:
        headers = {"X-App-Key": self.api_key}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        if not multipart:
            headers["Content-Type"] = "application/json"
        return headers

    def _handle_response(self, response: requests.Response) -> Any:
        try:
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            print(f"API Error: {e}")
            try:
                return {"error": response.json().get("detail", str(e))}
            except:
                return {"error": str(e)}
        except Exception as e:
            print(f"Connection Error: {e}")
            return {"error": "Connection failed"}

    # --- 認証・ユーザー関連 ---

    def health_check(self):
        res = requests.get(f"{self.api_url}/", headers=self._get_headers())
        return self._handle_response(res)

    def signup(self, user_name, password):
        payload = {"user_name": user_name, "password": password}
        res = requests.post(f"{self.api_url}/users", json=payload, headers=self._get_headers())
        return self._handle_response(res)

    def login(self, user_id, password):
        data = {"username": str(user_id), "password": password}
        headers = {"X-App-Key": self.api_key} 
        res = requests.post(f"{self.api_url}/token", data=data, headers=headers)
        
        result = self._handle_response(res)
        if result and "access_token" in result:
            self.token = result["access_token"]
            return True
        return False

    def get_me(self):
        res = requests.get(f"{self.api_url}/users/me", headers=self._get_headers())
        return self._handle_response(res)

    def get_my_groups(self, user_id: int):
        res = requests.get(f"{self.api_url}/users/{user_id}/groups", headers=self._get_headers())
        return self._handle_response(res)

    def get_my_purchases(self):
        res = requests.get(f"{self.api_url}/users/me/purchases", headers=self._get_headers())
        return self._handle_response(res)

    # --- グループ管理 ---

    def create_group(self, group_name: str):
        res = requests.post(
            f"{self.api_url}/groups", 
            json={"group_name": group_name}, 
            headers=self._get_headers()
        )
        return self._handle_response(res)

    def get_group_detail(self, group_id: int):
        res = requests.get(f"{self.api_url}/groups/{group_id}", headers=self._get_headers())
        return self._handle_response(res)

    def generate_invite_code(self, group_id: int):
        res = requests.post(f"{self.api_url}/groups/{group_id}/invite_code", headers=self._get_headers())
        return self._handle_response(res)
    
    def reset_invite_code(self, group_id: int):
        res = requests.post(f"{self.api_url}/groups/{group_id}/reset_invite_code", headers=self._get_headers())
        return self._handle_response(res)

    def join_group(self, invite_code: str):
        res = requests.post(
            f"{self.api_url}/groups/join", 
            json={"invite_code": invite_code}, 
            headers=self._get_headers()
        )
        return self._handle_response(res)

    def update_member_role(self, group_id: int, target_user_id: int, is_host: bool):
        res = requests.put(
            f"{self.api_url}/groups/{group_id}/members/{target_user_id}/role",
            json={"is_host": is_host},
            headers=self._get_headers()
        )
        return self._handle_response(res)

    def kick_member(self, group_id: int, target_user_id: int):
        res = requests.delete(
            f"{self.api_url}/groups/{group_id}/members/{target_user_id}",
            headers=self._get_headers()
        )
        return self._handle_response(res)
    
    def leave_group(self, group_id: int):
        """グループから脱退する"""
        if not self.token:
            return {"error": "Unauthorized"}
            
        try:
            resp = requests.post(
                f"{self.api_url}/groups/{group_id}/leave",
                headers=self._get_headers()
            )
            if resp.status_code == 200:
                return resp.json()
            elif resp.status_code == 400:
                return {"error": "このグループには所属していません"}
            else:
                return {"error": f"Failed to leave: {resp.text}"}
        except Exception as e:
            return {"error": str(e)}
        
    def delete_group(self, group_id: int):
        """グループ削除（オーナーのみ）"""
        res = requests.delete(f"{self.api_url}/groups/{group_id}", headers=self._get_headers())
        return self._handle_response(res)

    # --- クエスト関連 ---

    def create_quest(self, group_id: int, name: str, desc: str, points: int, start_time: str, end_time: str):
        payload = {
            "quest_name": name,
            "description": desc,
            "reward_points": points,
            "start_time": start_time,
            "end_time": end_time
        }
        res = requests.post(
            f"{self.api_url}/groups/{group_id}/quests", 
            json=payload, 
            headers=self._get_headers()
        )
        return self._handle_response(res)

    def delete_quest(self, quest_id: int):
        res = requests.delete(f"{self.api_url}/quests/{quest_id}", headers=self._get_headers())
        return self._handle_response(res)

    def complete_quest(self, quest_id: int, uploaded_file):
        files = {
            "file": (
                uploaded_file.name,
                uploaded_file.getvalue(),
                uploaded_file.type
            )
        }

        res = requests.post(
            f"{self.api_url}/quests/{quest_id}/complete",
            files=files,
            headers=self._get_headers(multipart=True)
        )
        return self._handle_response(res)

    def get_pending_submissions(self, group_id: int):
        res = requests.get(f"{self.api_url}/groups/{group_id}/submissions", headers=self._get_headers())
        return self._handle_response(res)

    def review_submission(self, log_id: int, approved: bool):
        res = requests.post(
            f"{self.api_url}/submissions/{log_id}/review",
            json={"approved": approved},
            headers=self._get_headers()
        )
        return self._handle_response(res)
    
    def get_quest_history(self, group_id: int):
        res = requests.get(f"{self.api_url}/groups/{group_id}/history/quests", headers=self._get_headers())
        return self._handle_response(res)

    # --- ショップ関連 ---

    def add_shop_item(self, group_id: int, item_name: str, cost: int, description: str = None, limit_per_user: int = None):
        """ショップアイテムを追加（購入制限対応）"""
        payload = {
            "item_name": item_name,
            "cost_points": cost,
            "description": description,
            "limit_per_user": limit_per_user
        }
        res = requests.post(
            f"{self.api_url}/groups/{group_id}/shops",
            json=payload,
            headers=self._get_headers()
        )
        return self._handle_response(res)

    def delete_shop_item(self, item_id: int):
        res = requests.delete(f"{self.api_url}/shops/{item_id}", headers=self._get_headers())
        return self._handle_response(res)

    def purchase_item(self, item_id: int):
        res = requests.post(f"{self.api_url}/shops/{item_id}/purchase", headers=self._get_headers())
        return self._handle_response(res)

    def get_purchase_history(self, group_id: int):
        res = requests.get(f"{self.api_url}/groups/{group_id}/history/purchases", headers=self._get_headers())
        return self._handle_response(res)
    
    def get_my_submissions(self, group_id: int):
        """自分の提出履歴を取得"""
        res = requests.get(
            f"{self.api_url}/groups/{group_id}/my_submissions",
            headers=self._get_headers()
        )
        return self._handle_response(res)