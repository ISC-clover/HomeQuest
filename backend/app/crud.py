from sqlalchemy.orm import Session, joinedload
import models, schemas, auth, secrets, os
from datetime import datetime, timedelta
from pathlib import Path

PASSWORD_PEPPER = os.getenv("PASSWORD_PEPPER", "D3fqv1t_53c2e7_pe9qe2")
UPLOAD_DIR = Path(__file__).resolve().parent / "uploads"

def create_user(db: Session, user: schemas.UserCreate):
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
    # グループを取得
    group = db.query(models.Group).filter(models.Group.id == group_id).first()
    if not group:
        return None

    # メンバー情報の整形（ポイントや役割など）
    # ※ここが複雑なので手動で辞書を作っているはずです
    users_data = []
    hosts_data = []
    
    for member in group.members:
        # UserGroupテーブルの情報などから整形
        u_info = {
            "id": member.user.id,
            "user_name": member.user.user_name,
            "points": member.points, # UserGroupにあるポイント
            "is_host": member.is_host
        }
        users_data.append(u_info)
        
        if member.is_host or member.user.id == group.owner_user_id:
            hosts_data.append({
                "id": member.user.id,
                "user_name": member.user.user_name
            })

    return {
        "id": group.id,
        "group_name": group.group_name,
        "owner_user_id": group.owner_user_id,
        "invite_code": group.invite_code,
        "users": users_data,
        "hosts": hosts_data,
        "shops": group.shops,   # リレーションで自動取得
        "quests": group.quests  # リレーションで自動取得
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
    
def submit_quest_completion(db: Session, user_id: int, quest_id: int, proof_path: str):
    # クエスト情報を取得して group_id を特定
    quest = db.query(models.Quest).filter(models.Quest.id == quest_id).first()
    if not quest:
        return False, "Quest not found"
        
    # 重複チェック
    existing = db.query(models.QuestCompletionLog).filter(
        models.QuestCompletionLog.quest_id == quest_id,
        models.QuestCompletionLog.user_id == user_id,
        models.QuestCompletionLog.status.in_(["pending", "approved"])
    ).first()
    
    if existing:
        return False, "Already submitted or approved"

    db_log = models.QuestCompletionLog(
        user_id=user_id,
        quest_id=quest_id,    # ★ここが重要。Noneにならないように
        group_id=quest.group_id,
        status="pending",
        proof_image_path=proof_path,
        completed_at=datetime.now()
    )
    db.add(db_log)
    db.commit()
    db.refresh(db_log)
    return True, "Submission received"

def get_pending_submissions(db: Session, group_id: int):
    # ユーザー情報とクエスト情報を結合(JOIN)して取得
    logs = db.query(models.QuestCompletionLog).options(
        joinedload(models.QuestCompletionLog.user),
        joinedload(models.QuestCompletionLog.quest)
    ).filter(
        models.QuestCompletionLog.group_id == group_id,
        models.QuestCompletionLog.status == "pending"
    ).all()
    
    # Pydanticモデルに合わせてデータを整形
    results = []
    for log in logs:
        # DBモデルからPydanticスキーマへ変換しつつ、名前フィールドを埋める
        item = schemas.QuestCompletionLog.model_validate(log)
        if log.user:
            item.user_name = log.user.user_name
        if log.quest:
            item.quest_title = log.quest.quest_name
        results.append(item)
        
    return results

def review_quest_submission(db: Session, log_id: int, approved: bool):
    log = (
        db.query(models.QuestCompletionLog)
        .options(joinedload(models.QuestCompletionLog.quest))
        .filter(models.QuestCompletionLog.id == log_id)
        .first()
    )

    if not log:
        return False, "Submission not found"

    # --------------------
    # ステータス更新
    # --------------------
    if approved:
        log.status = "approved"

        user_group = (
            db.query(models.UserGroup)
            .filter(
                models.UserGroup.user_id == log.user_id,
                models.UserGroup.group_id == log.group_id
            )
            .first()
        )

        if user_group and log.quest and hasattr(user_group, "points"):
            user_group.points = (user_group.points or 0) + log.quest.reward_points
    else:
        log.status = "rejected"

    # --------------------
    # 画像削除
    # --------------------
    if log.proof_image_path:
        try:
            # "/static/xxx.jpg" → "xxx.jpg"
            filename = Path(log.proof_image_path).name
            image_path = UPLOAD_DIR / filename

            if image_path.exists():
                image_path.unlink()

            # DB側の参照も消す（任意だけど推奨）
            log.proof_image_path = None

        except Exception as e:
            # 承認処理は止めない
            print(f"[WARN] Failed to delete image: {e}")

    db.commit()
    db.refresh(log)
    return True, "Reviewed successfully"

# ---------------------------------------------------------
# 追加: 自分の提出状況を確認するための関数 (Frontendでボタン隠す用)
# ---------------------------------------------------------
def get_my_quest_logs(db: Session, group_id: int, user_id: int):
    return db.query(models.QuestCompletionLog).filter(
        models.QuestCompletionLog.group_id == group_id,
        models.QuestCompletionLog.user_id == user_id
    ).all()

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
    results = db.query(models.QuestCompletionLog, models.User, models.Quest).join(models.User).join(models.Quest).filter(
        models.QuestCompletionLog.group_id == group_id
    ).order_by(models.QuestCompletionLog.completed_at.desc()).all()
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
    if group.invite_code:
        return group.invite_code
    while True:
        code = secrets.token_hex(4).upper()
        if not db.query(models.Group).filter(models.Group.invite_code == code).first():
            group.invite_code = code
            break
    db.commit()
    db.refresh(group)
    return group.invite_code

def join_group_by_code(db: Session, user_id: int, invite_code: str):
    group = db.query(models.Group).filter(models.Group.invite_code == invite_code).first()
    if not group:
        return None, "無効な招待コードです"
    existing_member = db.query(models.UserGroup).filter(
        models.UserGroup.user_id == user_id,
        models.UserGroup.group_id == group.id
    ).first()
    if existing_member:
        return group, "すでにこのグループに参加しています"
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
    while True:
        new_code = secrets.token_hex(4).upper()
        if not db.query(models.Group).filter(models.Group.invite_code == new_code).first():
            group.invite_code = new_code
            break
    db.commit()
    db.refresh(group)
    return group.invite_code

def is_group_host(db: Session, user_id: int, group_id: int) -> bool:
    user_group = db.query(models.UserGroup).filter(
        models.UserGroup.user_id == user_id,
        models.UserGroup.group_id == group_id
    ).first()
    return user_group.is_host if user_group else False

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
    return (
        db.query(models.Group)
        .join(models.UserGroup, models.Group.id == models.UserGroup.group_id)
        .filter(models.UserGroup.user_id == user_id)
        .all()
    )
    
def leave_group(db: Session, group_id: int, user_id: int) -> bool:
    """
    指定されたユーザーをグループから削除（脱退）させる
    """
    # 紐付けデータを探す
    link = db.query(models.UserGroup).filter(
        models.UserGroup.group_id == group_id,
        models.UserGroup.user_id == user_id
    ).first()
    
    if link:
        db.delete(link)
        db.commit()
        return True
    return False

def delete_group(db: Session, group_id: int) -> bool:
    """グループを削除する"""
    group = db.query(models.Group).filter(models.Group.id == group_id).first()
    if group:
        db.delete(group)
        db.commit()
        return True
    return False