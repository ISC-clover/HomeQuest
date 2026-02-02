from sqlalchemy.orm import Session
import models, schemas, auth, secrets, os, models
from datetime import datetime
from zoneinfo import ZoneInfo
from sqlalchemy import desc

PASSWORD_PEPPER = os.getenv("PASSWORD_PEPPER", "D3fqv1t_53c2e7_pe9qe2")

# --- User ---
def create_user(db: Session, user: schemas.UserCreate):
    # auth.py の関数を使って安全にハッシュ化
    hashed_password = auth.get_password_hash(user.password)
    
    db_user = models.User(
        user_name=user.user_name,
        password=hashed_password
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def get_users(db: Session):
    users = db.query(models.User).all()
    results = []
    
    for user in users:
        group_ids = (
            db.query(models.UserGroup.group_id)
            .filter(models.UserGroup.user_id == user.id)
            .all()
        )
        group_ids = [gid for (gid,) in group_ids]
    
        results.append({
            "id": user.id,
            "user_name": user.user_name,
            "groups": group_ids
        })
    return results


def create_group(db: Session, group: schemas.GroupCreate, owner_id: int):
    db_group = models.Group(
        group_name=group.group_name,
        owner_user_id=owner_id,
    )
    db.add(db_group)
    db.commit()
    db.refresh(db_group)
    
    owner_link = models.UserGroup(
        user_id=owner_id,
        group_id=db_group.id,
        is_host=True,
        points=0
    )
    db.add(owner_link)
    db.commit()
    db.refresh(owner_link)
    
    return db_group

def get_groups(db: Session):
    return db.query(models.Group).all()

def add_user_to_group(db: Session, user_id: int, group_id: int):
    user_group = models.UserGroup(user_id=user_id, group_id=group_id)
    db.add(user_group)
    db.commit()
    db.refresh(user_group)
    return user_group

def get_group_detail(db: Session, group_id: int):
    group = db.query(models.Group).filter(models.Group.id == group_id).first()
    if not group:
        return None
    
    user_groups = (
        db.query(models.UserGroup, models.User)
        .join(models.User, models.User.id == models.UserGroup.user_id)
        .filter(models.UserGroup.group_id == group_id)
        .all()
    )
    
    members_list = []
    hosts_list = []
    
    for ug, user in user_groups:
        member_data = {
            "id": user.id,
            "user_name": user.user_name,
            "points": ug.points,
            "is_host": ug.is_host
        }
        members_list.append(member_data)
        
        if ug.is_host:
            host_data = {
                "id": user.id,
                "user_name": user.user_name
            }
            hosts_list.append(host_data)

    return {
        "id": group.id,
        "group_name": group.group_name,
        "owner_user_id": group.owner_user_id,
        "hosts": hosts_list,
        "users": members_list,
        "shops": group.shops,
        "quests": group.quests
    }
    
def create_quest(db: Session, quest: schemas.QuestCreate, group_id: int):
    db_quest = models.Quest(
        quest_name=quest.quest_name,
        description=quest.description,
        start_time=quest.start_time,
        end_time=quest.end_time,
        reward_points=quest.reward_points,
        recurrence=quest.recurrence,
        group_id=group_id
    )
    db.add(db_quest)
    db.commit()
    db.refresh(db_quest)
    return db_quest

def create_shop_item(db: Session, shop_item: schemas.ShopCreate, group_id: int):
    db_item = models.Shop(
        item_name=shop_item.item_name,
        description=shop_item.description,
        cost_points=shop_item.cost_points,
        limit_per_user=shop_item.limit_per_user,
        
        group_id=group_id
    )
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item

def purchase_item(db: Session, user_id: int, item_id: int):
    shop_item = db.query(models.Shop).filter(models.Shop.id == item_id).first()
    if not shop_item:
        return None, "Item not found"

    if shop_item.limit_per_user is not None:
        count = db.query(models.PurchaseHistory).filter(
            models.PurchaseHistory.user_id == user_id,
            models.PurchaseHistory.shop_item_id == item_id
        ).count()
        
        if count >= shop_item.limit_per_user:
            return None, f"Purchase limit reached (Max: {shop_item.limit_per_user})"

    user_group = db.query(models.UserGroup).filter(
        models.UserGroup.user_id == user_id,
        models.UserGroup.group_id == shop_item.group_id
    ).first()
    
    if not user_group:
        return None, "User not in group"

    if user_group.points < shop_item.cost_points:
        return None, "Not enough points"

    user_group.points -= shop_item.cost_points
    
    history = models.PurchaseHistory(
        user_id=user_id,
        group_id=shop_item.group_id,
        shop_item_id=shop_item.id,
        item_name=shop_item.item_name,
        cost=shop_item.cost_points
    )
    db.add(history)
    
    db.commit()
    db.refresh(user_group)
    
    return user_group, "Success"

def get_user_purchases(db: Session, user_id: int):
    return db.query(models.PurchaseHistory).filter(
        models.PurchaseHistory.user_id == user_id
    ).order_by(models.PurchaseHistory.purchased_at.desc()).all()
    
def submit_quest_completion(db: Session, user_id: int, quest_id: int, image_path: str):
    """ユーザーがクエスト完了を報告する（ポイントはまだ入らない）"""
    quest = get_quest(db, quest_id)
    if not quest:
        return None, "Quest not found"
    
    # 既に「承認待ち」または「完了」のものがないかチェック（重複提出防止）
    # (簡易的に、同じクエストを何度も提出できないようにする場合)
    # 運用に合わせて調整してください。今回は「直近のログが承認待ちならエラー」にします
    existing_log = db.query(models.QuestCompletionLog).filter(
        models.QuestCompletionLog.user_id == user_id,
        models.QuestCompletionLog.quest_id == quest_id,
        models.QuestCompletionLog.status == "pending"
    ).first()
    
    if existing_log:
        return None, "現在、承認待ちの提出があります。"

    db_log = models.QuestCompletionLog(
        user_id=user_id,
        quest_id=quest_id,
        group_id=quest.group_id,
        status="pending",
        proof_image_path=image_path
    )
    db.add(db_log)
    db.commit()
    db.refresh(db_log)
    
    return db_log, "クエストを提出しました！ホストの承認をお待ちください。"

def get_pending_submissions(db: Session, group_id: int):
    return db.query(models.QuestCompletionLog).filter(
        models.QuestCompletionLog.group_id == group_id,
        models.QuestCompletionLog.status == "pending"
    ).all()

def review_quest_submission(db: Session, log_id: int, is_approved: bool):
    """ホストが提出を承認または却下する"""
    log = db.query(models.QuestCompletionLog).filter(models.QuestCompletionLog.id == log_id).first()
    if not log:
        return None, "提出データが見つかりません"
    
    if log.status != "pending":
        return None, "このクエストは既に処理されています"

    if is_approved:
        log.status = "approved"
        
        quest = get_quest(db, log.quest_id)
        user_group = db.query(models.UserGroup).filter(
            models.UserGroup.user_id == log.user_id,
            models.UserGroup.group_id == log.group_id
        ).first()
        
        if user_group and quest:
            user_group.points += quest.points
            
        message = f"承認しました！ユーザーに {quest.points} ポイント付与されました。"
    else:
        log.status = "rejected"
        message = "クエストを却下しました。"

    db.commit()
    db.refresh(log)
    return log, message

def get_group_purchase_history(db: Session, group_id: int):
    results = db.query(models.PurchaseHistory, models.User).join(models.User).filter(
        models.PurchaseHistory.group_id == group_id
    ).order_by(models.PurchaseHistory.purchased_at.desc()).all()
    
    logs = []
    for hist, user in results:
        logs.append({
            "id": hist.id,
            "user_name": user.user_name,
            "item_name": hist.item_name,
            "cost": hist.cost,
            "purchased_at": hist.purchased_at
        })
    return logs

def get_group_quest_history(db: Session, group_id: int):
    results = db.query(models.QuestCompletion, models.User, models.Quest).join(models.User).join(models.Quest).filter(
        models.QuestCompletion.group_id == group_id
    ).order_by(models.QuestCompletion.completed_at.desc()).all()
    
    logs = []
    for comp, user, quest in results:
        logs.append({
            "id": comp.id,
            "user_name": user.user_name,
            "quest_name": quest.quest_name,
            "reward_points": quest.reward_points,
            "completed_at": comp.completed_at
        })
    return logs

def create_invite_code(db: Session, group_id: int):
    group = db.query(models.Group).filter(models.Group.id == group_id).first()
    if not group:
        return None
    
    # すでにコードがあるならそれを返す
    if group.invite_code:
        return group.invite_code

    # ランダムなコードを生成（重複したら作り直し）
    while True:
        # 4バイトのHEX文字列（例: A1B2C3D4）を生成して大文字に
        code = secrets.token_hex(4).upper()
        # 他のグループとかぶってないかチェック
        if not db.query(models.Group).filter(models.Group.invite_code == code).first():
            group.invite_code = code
            break
    
    db.commit()
    db.refresh(group)
    return group.invite_code

def join_group_by_code(db: Session, user_id: int, invite_code: str):
    # コードからグループを探す
    group = db.query(models.Group).filter(models.Group.invite_code == invite_code).first()
    
    if not group:
        return None, "無効な招待コードです"
    
    # すでにメンバーかどうかチェック
    existing_member = db.query(models.UserGroup).filter(
        models.UserGroup.user_id == user_id,
        models.UserGroup.group_id == group.id
    ).first()
    
    if existing_member:
        return group, "すでにこのグループに参加しています"
    
    # メンバーに追加
    new_member = models.UserGroup(
        user_id=user_id,
        group_id=group.id,
        points=0,
        is_host=False
    )
    db.add(new_member)
    db.commit()
    
    return group, "成功"

def regenerate_invite_code(db: Session, group_id: int):
    group = db.query(models.Group).filter(models.Group.id == group_id).first()
    if not group:
        return None
    
    # 既存のコードがあっても無視して、新しいコードを探す
    while True:
        new_code = secrets.token_hex(4).upper()
        # 重複チェック（自分自身の今のコードと同じになっても一応作り直す）
        if not db.query(models.Group).filter(models.Group.invite_code == new_code).first():
            group.invite_code = new_code
            break
            
    db.commit()
    db.refresh(group)
    return group.invite_code

def is_group_host(db: Session, user_id: int, group_id: int) -> bool:
    # ユーザーとグループの紐づけデータを取得
    user_group = db.query(models.UserGroup).filter(
        models.UserGroup.user_id == user_id,
        models.UserGroup.group_id == group_id
    ).first()
    
    # データが存在し、かつ is_host が True ならOK
    return user_group.is_host if user_group else False

# --- Delete Helpers ---

def get_quest(db: Session, quest_id: int):
    return db.query(models.Quest).filter(models.Quest.id == quest_id).first()

def delete_quest(db: Session, quest_id: int):
    quest = get_quest(db, quest_id)
    if quest:
        db.delete(quest)
        db.commit()
        return True
    return False

def get_shop_item(db: Session, item_id: int):
    return db.query(models.Shop).filter(models.Shop.id == item_id).first()

def delete_shop_item(db: Session, item_id: int):
    item = get_shop_item(db, item_id)
    if item:
        db.delete(item)
        db.commit()
        return True
    return False

# --- Member Management ---

def is_group_owner(db: Session, user_id: int, group_id: int) -> bool:
    group = db.query(models.Group).filter(models.Group.id == group_id).first()
    return group and group.owner_user_id == user_id

def update_member_host_status(db: Session, group_id: int, user_id: int, is_host: bool):
    member = db.query(models.UserGroup).filter(
        models.UserGroup.group_id == group_id,
        models.UserGroup.user_id == user_id
    ).first()
    
    if member:
        member.is_host = is_host
        db.commit()
        db.refresh(member)
        return member
    return None

def remove_member(db: Session, group_id: int, user_id: int):
    member = db.query(models.UserGroup).filter(
        models.UserGroup.group_id == group_id,
        models.UserGroup.user_id == user_id
    ).first()
    
    if member:
        db.delete(member)
        db.commit()
        return True
    return False

def get_user_joined_groups(db: Session, user_id: int):
    """ユーザーが参加しているグループの一覧を取得する"""
    return (
        db.query(models.Group)
        .join(models.UserGroup, models.Group.id == models.UserGroup.group_id)
        .filter(models.UserGroup.user_id == user_id)
        .all()
    )