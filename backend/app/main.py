from fastapi import FastAPI, Depends, HTTPException, status, Security, Request
from fastapi.security import OAuth2PasswordRequestForm, APIKeyHeader
from fastapi.middleware.cors import CORSMiddleware
from database import Base, engine, get_db
import models, schemas, crud, auth, os
from sqlalchemy.orm import Session
from datetime import timedelta

# --- 1. 設定とセキュリティ関数の定義 (appより先に書く！) ---

# 環境変数からAPIキーを取得
API_KEY = os.getenv("APP_API_KEY")
API_KEY_NAME = "X-App-Key"

# auto_error=Falseにすることで、ヘッダーがなくても即エラーにせず、関数内で判定できるようにする
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)

async def get_api_key(
    request: Request,
    api_key_header: str = Security(api_key_header)
):
    """
    全てのアクセスに対してAPIキーをチェックする関数。
    ただし、Swagger UIやルートパスは許可する。
    """
    # ホワイトリスト: APIキーなしでアクセスしていいパス
    # docs: ドキュメントを見るため
    # openapi.json: ドキュメントのデータ
    # /: ヘルスチェック用
    whitelist = ["/docs", "/redoc", "/openapi.json", "/"]
    
    if request.url.path in whitelist:
        return None  # チェック免除

    # キーの検証
    if api_key_header == API_KEY:
        return api_key_header
    else:
        # キーが違う、または無い場合は 403 エラー
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Could not validate credentials (API Key is missing or invalid)"
        )

# データベースのテーブル作成
Base.metadata.create_all(bind=engine)

# --- 2. アプリの初期化 (ここで「全ての操作」にロックをかける) ---
app = FastAPI(dependencies=[Depends(get_api_key)])

# CORS設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- 3. ルーティング定義 (中身はそのまま) ---

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

@app.post("/groups/{group_id}/invite_code")
def generate_invite_code(group_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    if not crud.is_group_host(db, current_user.id, group_id):
        raise HTTPException(status_code=403, detail="権限がありません。ホストのみ実行可能です。")
    code = crud.create_invite_code(db, group_id)
    if not code:
        raise HTTPException(status_code=404, detail="Group not found")
    return {"invite_code": code}

@app.post("/groups/join")
def join_group(request: schemas.JoinGroupRequest, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    group, message = crud.join_group_by_code(db, current_user.id, request.invite_code)
    
    if not group:
        raise HTTPException(status_code=400, detail=message)
        
    return {
        "message": f"グループ「{group.group_name}」に参加しました！",
        "group_id": group.id
    }

@app.post("/groups/{group_id}/reset_invite_code")
def reset_invite_code(group_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    if not crud.is_group_host(db, current_user.id, group_id):
        raise HTTPException(status_code=403, detail="権限がありません。ホストのみ実行可能です。")
    code = crud.regenerate_invite_code(db, group_id)
    if not code:
        raise HTTPException(status_code=404, detail="Group not found")
    return {"new_invite_code": code}

@app.put("/groups/{group_id}/members/{user_id}/role")
def update_member_role(
    group_id: int, 
    user_id: int, 
    role_update: schemas.MemberRoleUpdate, 
    db: Session = Depends(get_db), 
    current_user: models.User = Depends(auth.get_current_user)
):
    if not crud.is_group_owner(db, current_user.id, group_id):
        raise HTTPException(status_code=403, detail="オーナーのみ実行可能です")

    if current_user.id == user_id:
        raise HTTPException(status_code=400, detail="オーナー自身の権限は変更できません")

    member = crud.update_member_host_status(db, group_id, user_id, role_update.is_host)
    if not member:
        raise HTTPException(status_code=404, detail="メンバーが見つかりません")
        
    status_text = "ホストに昇格しました" if role_update.is_host else "ホスト権限を剥奪しました"
    return {"message": f"ユーザーID {user_id} を{status_text}"}


@app.delete("/groups/{group_id}/members/{user_id}")
def remove_member_from_group(
    group_id: int, 
    user_id: int, 
    db: Session = Depends(get_db), 
    current_user: models.User = Depends(auth.get_current_user)
):
    if not crud.is_group_owner(db, current_user.id, group_id):
        raise HTTPException(status_code=403, detail="オーナーのみ実行可能です")

    if current_user.id == user_id:
        raise HTTPException(status_code=400, detail="オーナー自身をグループから削除することはできません")

    success = crud.remove_member(db, group_id, user_id)
    if not success:
        raise HTTPException(status_code=404, detail="メンバーが見つかりません")
        
    return {"message": f"ユーザーID {user_id} をグループから削除しました"}

# --- Shops (Rewards) ---
@app.post("/groups/{group_id}/shops", response_model=schemas.Shop)
def create_shop_item(
    group_id: int, 
    shop_item: schemas.ShopCreate, 
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    if not crud.is_group_host(db, current_user.id, group_id):
        raise HTTPException(status_code=403, detail="権限がありません。商品追加はホストのみ可能です。")
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

@app.delete("/shops/{item_id}")
def delete_shop_item(item_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    item = crud.get_shop_item(db, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    if not crud.is_group_host(db, current_user.id, item.group_id):
        raise HTTPException(status_code=403, detail="権限がありません。商品削除はホストのみ可能です。")

    crud.delete_shop_item(db, item_id)
    return {"message": "Item deleted successfully"}

# --- Quests ---
@app.post("/groups/{group_id}/quests", response_model=schemas.Quest)
def create_quest(
    group_id: int, 
    quest: schemas.QuestCreate, 
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    if not crud.is_group_host(db, current_user.id, group_id):
        raise HTTPException(status_code=403, detail="権限がありません。クエスト作成はホストのみ可能です。")
    return crud.create_quest(db=db, quest=quest, group_id=group_id)

@app.post("/quests/{quest_id}/complete")
def complete_quest(quest_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    result, message = crud.complete_quest(db, current_user.id, quest_id)
    if not result:
        raise HTTPException(status_code=400, detail=message)
    return {"message": "クエスト完了！", "current_points": result.points}

@app.delete("/quests/{quest_id}")
def delete_quest(quest_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    quest = crud.get_quest(db, quest_id)
    if not quest:
        raise HTTPException(status_code=404, detail="Quest not found")
    
    if not crud.is_group_host(db, current_user.id, quest.group_id):
        raise HTTPException(status_code=403, detail="権限がありません。クエスト削除はホストのみ可能です。")
    
    crud.delete_quest(db, quest_id)
    return {"message": "Quest deleted successfully"}

# --- Login Endpoint ---
@app.post("/token", response_model=schemas.Token)
def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(), 
    db: Session = Depends(get_db)
):
    try:
        user_id = int(form_data.username)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User ID must be an integer",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = auth.authenticate_user(db, user_id=user_id, password=form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect user ID or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=auth.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = auth.create_access_token(
        data={"sub": str(user.id)},
        expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

# --- Protected Route Example ---
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