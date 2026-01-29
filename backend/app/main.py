from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from database import Base, engine, get_db
import models, schemas, crud, auth
from sqlalchemy.orm import Session

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

# --- Groups ---
@app.post("/groups", response_model=schemas.Group)
def create_group(group: schemas.GroupCreate, db: Session = Depends(get_db)):
    owner = db.query(models.User).filter(models.User.id == group.owner_user_id).first()
    if not owner:
        raise HTTPException(status_code=404, detail="Owner user not found")
    return crud.create_group(db, group)

@app.get("/groups", response_model=list[schemas.Group])
def read_groups(db: Session = Depends(get_db)):
    return crud.get_groups(db)

@app.get("/groups/{group_id}", response_model=schemas.GroupDetail)
def read_group_detail(group_id: int, db: Session = Depends(get_db)):
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
def create_shop_item(group_id: int, item: schemas.ShopCreate, db: Session = Depends(get_db)):
    return crud.create_shop_item(db, item, group_id)

# --- Quests ---
@app.post("/groups/{group_id}/quests", response_model=schemas.Quest)
def create_quest(group_id: int, quest: schemas.QuestCreate, db: Session = Depends(get_db)):
    return crud.create_quest(db, quest, group_id)

# --- Login Endpoint (NEW) ---
@app.post("/token", response_model=schemas.Token)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(), 
    db: Session = Depends(get_db)
):
    # ユーザー認証
    user = auth.authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # トークン発行
    access_token_expires = auth.timedelta(minutes=auth.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = auth.create_access_token(
        data={"sub": user.user_name}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

# --- Protected Route Example (NEW) ---
# このAPIはログインしているユーザーしか叩けません
@app.get("/users/me", response_model=schemas.User)
async def read_users_me(current_user: models.User = Depends(auth.get_current_user)):
    return current_user