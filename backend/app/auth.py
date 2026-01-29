import os
import hashlib # 追加
from datetime import datetime, timedelta
from typing import Annotated
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session
import models, schemas, database

SECRET_KEY = os.getenv("SECRET_KEY", "your_secret_key_needs_to_be_very_long_and_random")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
PASSWORD_PEPPER = os.getenv("PASSWORD_PEPPER", "D3fqv1t_53c2e7_pe9qe2")

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# --- 重要な追加関数: どんな長さでも安全な形に変換する ---
def get_salted_hash(plain_password: str) -> str:
    # 1. パスワードとペッパーを結合
    salted = plain_password + PASSWORD_PEPPER
    # 2. SHA256でハッシュ化（これで長さが必ず64文字の英数字になり、bcryptの72文字制限に収まる）
    return hashlib.sha256(salted.encode("utf-8")).hexdigest()

# --- パスワード関連 ---
def verify_password(plain_password, hashed_password):
    # 検証時も同じように変換してからチェック
    safe_password = get_salted_hash(plain_password)
    return pwd_context.verify(safe_password, hashed_password)

def get_password_hash(password):
    # 登録時も変換してからハッシュ化
    safe_password = get_salted_hash(password)
    return pwd_context.hash(safe_password)

# ... (ここから下は変更ありません。以前のコードのままにしてください) ...
# get_user_by_username, authenticate_user, create_access_token, get_current_user
# はそのまま使ってください。
# ただし、authenticate_user の中身は verify_password を使っていることを確認してください。

def get_user_by_username(db: Session, username: str):
    return db.query(models.User).filter(models.User.user_name == username).first()

def authenticate_user(db: Session, username: str, password: str):
    user = get_user_by_username(db, username)
    if not user:
        return False
    if not verify_password(password, user.password):
        return False
    return user

def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)], db: Session = Depends(database.get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = schemas.TokenData(username=username)
    except JWTError:
        raise credentials_exception
        
    user = get_user_by_username(db, username=token_data.username)
    if user is None:
        raise credentials_exception
    return user