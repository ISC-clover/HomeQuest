from sqlalchemy.orm import Session
from passlib.context import CryptContext
import os
import models, schemas

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

PASSWORD_PEPPER = os.getenv("PASSWORD_PEPPER", "D3fqv1t_53c2e7_pe9qe2")

# --- User ---
def create_user(db: Session, user: schemas.UserCreate):
    # パスワードにペッパーを結合してからハッシュ化
    # 例: "mypassword" + "secret_pepper" -> "mypasswordsecret_pepper" をハッシュ化
    salted_password = user.password + PASSWORD_PEPPER
    hashed_password = pwd_context.hash(salted_password)
    
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


def create_group(db: Session, group: schemas.GroupCreate):
    db_group = models.Group(
        name=group.name,
        owner_user_id=group.owner_user_id,
        reward_shop=None
    )
    db.add(db_group)
    db.commit()
    db.refresh(db_group)
    
    owner_link = models.UserGroup(
        user_id=group.owner_user_id,
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
    
    users = []
    hosts = []
    
    for ug, user in user_groups:
        users.append({
            "id":user.id,
            "name":user.name,
            "points":ug.points,
            "is_host":ug.is_host
        })
        if ug.is_host:
            hosts.append({
                "id":user.id,
                "name":user.name
            })
    
    return{
        "id":group.id,
        "name":group.name,
        "owner_user_id":group.owner_user_id,
        "reward_shop":group.reward_shop,
        "hosts":hosts,
        "users":users
    }