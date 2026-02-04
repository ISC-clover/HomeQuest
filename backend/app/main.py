import models, schemas, crud, auth, os, uuid
from fastapi import FastAPI, Depends, HTTPException, status, Security, Request, UploadFile, File
from fastapi.security import OAuth2PasswordRequestForm, APIKeyHeader
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from database import Base, engine, get_db
from sqlalchemy.orm import Session
from datetime import timedelta
from pathlib import Path


API_KEY = os.getenv("APP_API_KEY")
API_KEY_NAME = "X-App-Key"
front_url = os.getenv("FRONT_URL", "http://localhost:8501")
origins = [front_url]
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)

async def get_api_key(
    request: Request,
    api_key_header: str = Security(api_key_header)
):
    whitelist = ["/docs", "/redoc", "/openapi.json", "/"]
    if request.url.path in whitelist:
        return None
    if api_key_header == API_KEY:
        return api_key_header
    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Could not validate credentials (API Key is missing or invalid)"
        )

Base.metadata.create_all(bind=engine)
app = FastAPI(dependencies=[Depends(get_api_key)])
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = Path(__file__).resolve().parent / "uploads"

# ディレクトリ作成 (os.makedirsではなく、Pathオブジェクトのメソッドを使います)
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# 3. 画像配信設定 (app = FastAPI() の後あたり)
# StaticFiles は Path オブジェクトのままでも動きます
app.mount("/static", StaticFiles(directory=UPLOAD_DIR), name="static")

#health check
@app.get("/")
def root():
    return {"message": "HomeQuest backend is running!"}

#create user
@app.post("/users", response_model=schemas.User)
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    return crud.create_user(db, user)

#get users
@app.get("/users", response_model=list[schemas.UserWithGroups])
def read_users(db: Session = Depends(get_db)):
    return crud.get_users(db)

#get purchases log
@app.get("/users/me/purchases", response_model=list[schemas.PurchaseLog])
def read_own_purchases(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    return crud.get_user_purchases(db=db, user_id=current_user.id)

#create group
@app.post("/groups", response_model=schemas.Group)
def create_group(
    group: schemas.GroupCreate, 
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    return crud.create_group(db=db, group=group, owner_id=current_user.id)

#get groups
@app.get("/groups", response_model=list[schemas.Group])
def read_groups(db: Session = Depends(get_db)):
    return crud.get_groups(db)

#get group detail
@app.get("/groups/{group_id}", response_model=schemas.GroupDetail)
def read_group_detail(group_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    group = crud.get_group_detail(db, group_id)
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    return group

#create invite code
@app.post("/groups/{group_id}/invite_code")
def generate_invite_code(group_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    if not crud.is_group_host(db, current_user.id, group_id):
        raise HTTPException(status_code=403, detail="権限がありません。ホストのみ実行可能です。")
    code = crud.create_invite_code(db, group_id)
    if not code:
        raise HTTPException(status_code=404, detail="Group not found")
    return {"invite_code": code}

#join group
@app.post("/groups/join")
def join_group(request: schemas.JoinGroupRequest, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    group, message = crud.join_group_by_code(db, current_user.id, request.invite_code)
    
    if not group:
        raise HTTPException(status_code=400, detail=message)
        
    return {
        "message": f"グループ「{group.group_name}」に参加しました！",
        "group_id": group.id
    }

#regen invite code
@app.post("/groups/{group_id}/reset_invite_code")
def reset_invite_code(group_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    if not crud.is_group_host(db, current_user.id, group_id):
        raise HTTPException(status_code=403, detail="権限がありません。ホストのみ実行可能です。")
    code = crud.regenerate_invite_code(db, group_id)
    if not code:
        raise HTTPException(status_code=404, detail="Group not found")
    return {"new_invite_code": code}

#change member role
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

#kick member
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

#add item
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

#purchase item
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

#delete item
@app.delete("/shops/{item_id}")
def delete_shop_item(item_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    item = crud.get_shop_item(db, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    if not crud.is_group_host(db, current_user.id, item.group_id):
        raise HTTPException(status_code=403, detail="権限がありません。商品削除はホストのみ可能です。")

    crud.delete_shop_item(db, item_id)
    return {"message": "Item deleted successfully"}

#create quest
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

#post quest complete request
@app.post("/quests/{quest_id}/complete")
async def complete_quest(
    quest_id: int, 
    file: UploadFile = File(...),
    db: Session = Depends(get_db), 
    current_user: models.User = Depends(auth.get_current_user)
):
    # 1. 安全なファイル名を生成 (日本語ファイル名対策)
    # 元のファイル名から拡張子 (.png や .jpg) だけ抜き出す
    extension = os.path.splitext(file.filename)[1]
    
    # ファイル名を "ユーザーID_クエストID_ランダムな文字列.拡張子" にする
    # 例: 1_5_a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11.png
    safe_filename = f"{current_user.id}_{quest_id}_{uuid.uuid4()}{extension}"
    
    # 2. 保存パスを作成
    # UPLOAD_DIR が Path("uploads") であれば、 / 演算子で結合できます
    file_path = UPLOAD_DIR / safe_filename
    
    # 3. ファイルを保存
    contents = await file.read()

    with open(file_path, "wb") as buffer:
        buffer.write(contents)
        
    # 4. DB保存処理
    db_path = f"/static/{safe_filename}" # 文字列に変換してDBへ
    result, message = crud.submit_quest_completion(db, current_user.id, quest_id, db_path)
    
    if not result:
        # 失敗時はゴミファイルを残さないように削除しておくと親切ですが、必須ではありません
        if os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(status_code=400, detail=message)
        
    return {"message": message}

#get quest complete
@app.get("/groups/{group_id}/submissions", response_model=list[schemas.QuestCompletionLog])
def get_pending_submissions(
    group_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    if not crud.is_group_host(db, current_user.id, group_id):
        raise HTTPException(status_code=403, detail="ホストのみ閲覧可能です")
    
    return crud.get_pending_submissions(db, group_id)

#quest confirm
@app.post("/submissions/{log_id}/review")
def review_submission(
    log_id: int,
    review: schemas.QuestReview,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    log = db.query(models.QuestCompletionLog).filter(models.QuestCompletionLog.id == log_id).first()
    if not log:
        raise HTTPException(status_code=404, detail="提出が見つかりません")
        
    if not crud.is_group_host(db, current_user.id, log.group_id) and not crud.is_group_owner(db, current_user.id, log.group_id):
        raise HTTPException(status_code=403, detail="権限がありません")
        
    # --- 修正箇所: 戻り値の受け取り方 ---
    success, message = crud.review_quest_submission(db, log_id, review.approved)
    
    if not success:
        raise HTTPException(status_code=400, detail=message)
        
    # bool型の success に .status は無いので、承認状況から文字列を作る
    status_str = "approved" if review.approved else "rejected"
    
    return {"message": message, "status": status_str}

#delete quest
@app.delete("/quests/{quest_id}")
def delete_quest(quest_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    quest = crud.get_quest(db, quest_id)
    if not quest:
        raise HTTPException(status_code=404, detail="Quest not found")
    if not crud.is_group_host(db, current_user.id, quest.group_id):
        raise HTTPException(status_code=403, detail="権限がありません。クエスト削除はホストのみ可能です。")
    crud.delete_quest(db, quest_id)
    return {"message": "Quest deleted successfully"}

#generate token
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

#get user info
@app.get("/users/me", response_model=schemas.User)
async def read_users_me(current_user: models.User = Depends(auth.get_current_user)):
    return current_user

#get purchase log
@app.get("/groups/{group_id}/history/purchases", response_model=list[schemas.PurchaseLog])
def read_group_purchase_history(group_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    return crud.get_group_purchase_history(db, group_id)

#get quest log
@app.get("/groups/{group_id}/history/quests", response_model=list[schemas.QuestCompletionLog])
def read_group_quest_history(group_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    return crud.get_group_quest_history(db, group_id)

#get user in group
@app.get("/users/{user_id}/groups", response_model=list[schemas.Group])
def read_user_joined_groups(
    user_id: int, 
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    return crud.get_user_joined_groups(db, user_id)

#leave group
@app.post("/groups/{group_id}/leave")
def leave_group(
    group_id: int, 
    db: Session = Depends(get_db), 
    current_user: models.User = Depends(auth.get_current_user)
):
    success = crud.leave_group(db, group_id, current_user.id)
    if not success:
        raise HTTPException(status_code=400, detail="Not a member of this group")
    
    return {"message": "Successfully left the group"}

#delete group
@app.delete("/groups/{group_id}")
def delete_group_endpoint(
    group_id: int, 
    db: Session = Depends(get_db), 
    current_user: models.User = Depends(auth.get_current_user)
):
    if not crud.is_group_owner(db, current_user.id, group_id):
        raise HTTPException(status_code=403, detail="オーナーのみ削除可能です")
    
    success = crud.delete_group(db, group_id)
    if not success:
        raise HTTPException(status_code=404, detail="グループが見つかりません")
    return {"message": "グループを削除しました"}

@app.get("/groups/{group_id}/my_submissions", response_model=list[schemas.QuestCompletionLog])
def read_my_submissions(
    group_id: int, 
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    return crud.get_my_quest_logs(db, group_id, current_user.id)