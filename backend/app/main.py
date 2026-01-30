from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from database import Base, engine, get_db
import models, schemas, crud, auth
from sqlalchemy.orm import Session
from datetime import timedelta

app = FastAPI()

# データベースのテーブル作成（更新があった場合は一度DBをリセットするか、alembic等でマイグレーションが必要ですが、開発中はDBファイルを削除して再起動が手っ取り早いです）
Base.metadata.create_all(bind=engine)

@app.get("/")
def root():
    return {"message": "HomeQuest backend is running!"}

# --- Users ---
@app.post("/users", response_model=schemas.User)
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    return crud.create_user(db, user)

@app.get("/users", response_model=list[schemas.UserWithGroups])
def read_users(db: Session = Depends(get_db)):
    return crud.get_users(db)

@app.get("/users/me/purchases", response_model=list[schemas.PurchaseLog])
def read_own_purchases(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    return crud.get_user_purchases(db=db, user_id=current_user.id)

# --- Groups ---
@app.post("/groups", response_model=schemas.Group)
def create_group(
    group: schemas.GroupCreate, 
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    return crud.create_group(db=db, group=group, owner_id=current_user.id)

@app.get("/groups", response_model=list[schemas.Group])
def read_groups(db: Session = Depends(get_db)):
    return crud.get_groups(db)

@app.get("/groups/{group_id}", response_model=schemas.GroupDetail)
def read_group_detail(group_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    group = crud.get_group_detail(db, group_id)
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    return group

# グループへのユーザー参加
@app.post("/groups/{group_id}/users/{user_id}")
def add_user_to_group(group_id: int, user_id: int, db: Session = Depends(get_db)):
    # 実際はここで「ユーザーが存在するか」「グループが存在するか」のチェックを入れるとより安全です
    return crud.add_user_to_group(db, user_id, group_id)

# --- Shops (Rewards) ---
@app.post("/groups/{group_id}/shops", response_model=schemas.Shop)
def create_shop_item(
    group_id: int, 
    shop_item: schemas.ShopCreate, 
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    return crud.create_shop_item(db=db, shop_item=shop_item, group_id=group_id)

@app.post("/shops/{item_id}/purchase")
def purchase_item(
    item_id: int, 
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    user_group, message = crud.purchase_item(db=db, user_id=current_user.id, item_id=item_id)
    
    if not user_group:
        raise HTTPException(status_code=400, detail=message)
    
    return {
        "message": f"Purchase successful! Remaining points: {user_group.points}",
        "current_points": user_group.points
    }

# --- Quests ---
@app.post("/groups/{group_id}/quests", response_model=schemas.Quest)
def create_quest(
    group_id: int, 
    quest: schemas.QuestCreate, 
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    return crud.create_quest(db=db, quest=quest, group_id=group_id)

@app.post("/quests/{quest_id}/complete")
def complete_quest(
    quest_id: int, 
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    result = crud.complete_quest(db=db, user_id=current_user.id, quest_id=quest_id)
    
    if not result:
        raise HTTPException(
            status_code=400, 
            detail="Quest not found, not in group, or already completed today."
        )
    
    return {"message": "Quest completed!", "current_points": result.points}
# --- Login Endpoint (NEW) ---
@app.post("/token", response_model=schemas.Token)
def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(), 
    db: Session = Depends(get_db)
):
    # Swagger UIのフォームは仕様上 "username" という名前で送ってきますが、
    # 中身は ID (数字) として扱います。
    try:
        user_id = int(form_data.username)
    except ValueError:
        # 数字じゃないものが入力されたらエラー
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User ID must be an integer",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # IDを使って認証
    user = auth.authenticate_user(db, user_id=user_id, password=form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect user ID or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # トークンの sub (subject) に ID を文字列として埋め込む
    access_token_expires = timedelta(minutes=auth.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = auth.create_access_token(
        data={"sub": str(user.id)}, # ここでIDを保存
        expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

# --- Protected Route Example (NEW) ---
# このAPIはログインしているユーザーしか叩けません
@app.get("/users/me", response_model=schemas.User)
async def read_users_me(current_user: models.User = Depends(auth.get_current_user)):
    return current_user

# --- history ---
@app.get("/groups/{group_id}/history/purchases", response_model=list[schemas.PurchaseLog])
def read_group_purchase_history(group_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    return crud.get_group_purchase_history(db, group_id)

@app.get("/groups/{group_id}/history/quests", response_model=list[schemas.QuestCompletionLog])
def read_group_quest_history(group_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    return crud.get_group_quest_history(db, group_id)