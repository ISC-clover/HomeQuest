import os
import hashlib
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
# tokenUrlは main.py のログイン用URLと同じにする必要があります
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def get_salted_hash(plain_password: str) -> str:
    salted = plain_password + PASSWORD_PEPPER
    return hashlib.sha256(salted.encode("utf-8")).hexdigest()

def verify_password(plain_password, hashed_password):
    safe_password = get_salted_hash(plain_password)
    return pwd_context.verify(safe_password, hashed_password)

def get_password_hash(password):
    safe_password = get_salted_hash(password)
    return pwd_context.hash(safe_password)

# --- 変更点1: 名前ではなく ID でユーザーを探す ---
def get_user_by_id(db: Session, user_id: int):
    return db.query(models.User).filter(models.User.id == user_id).first()

# --- 変更点2: 認証も ID を受け取る ---
def authenticate_user(db: Session, user_id: int, password: str):
    user = get_user_by_id(db, user_id)
    if not user:
        return False
    if not verify_password(password, user.password):
        return False
    return user

def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now() + expires_delta
    else:
        expire = datetime.now() + timedelta(minutes=15)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# --- 変更点3: トークンから ID を取り出してユーザーを特定する ---
async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)], db: Session = Depends(database.get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        # トークンの "sub" (subject) には ID（文字列）が入っている想定
        user_id_str: str = payload.get("sub")
        if user_id_str is None:
            raise credentials_exception
        user_id = int(user_id_str) # 文字列を数字に戻す
    except (JWTError, ValueError):
        raise credentials_exception
        
    user = get_user_by_id(db, user_id=user_id)
    if user is None:
        raise credentials_exception
    return user