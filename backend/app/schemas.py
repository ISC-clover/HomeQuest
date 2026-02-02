from pydantic import BaseModel
from datetime import datetime

# --- User ---
class UserCreate(BaseModel):
    user_name: str
    password: str

class User(BaseModel):    
    id: int
    user_name: str
    
    model_config = {"from_attributes": True}

# --- Shop (Reward) ---
class ShopCreate(BaseModel):
    item_name: str
    description: str | None = None
    cost_points: int = 100
    limit_per_user: int | None = None 

class Shop(ShopCreate):
    id: int
    group_id: int
    model_config = {"from_attributes": True}    

class PurchaseLog(BaseModel):
    id: int
    user_name: str
    item_name: str
    cost: int
    purchased_at: datetime
    model_config = {"from_attributes": True}

# --- Quest ---
class QuestCreate(BaseModel):
    quest_name: str
    description: str | None = None
    start_time: datetime | None = None
    end_time: datetime | None = None
    reward_points: int = 10
    recurrence: str = "one_off"  # "daily" or "one_off"

class Quest(QuestCreate):
    id: int
    group_id: int
    model_config = {"from_attributes": True}

class QuestCompletionLog(BaseModel):
    id: int
    user_name: str
    quest_name: str
    reward_points: int
    completed_at: datetime
    model_config = {"from_attributes": True}

# --- Group ---
class GroupCreate(BaseModel):
    group_name: str

class Group(BaseModel):
    id: int
    group_name: str
    owner_user_id: int
    shops: list[Shop] = []
    quests: list[Quest] = []
    
    model_config = {"from_attributes": True}

class JoinGroupRequest(BaseModel):
    invite_code: str

# --- Others ---
class HostUser(BaseModel):
    id: int
    user_name: str
    model_config = {"from_attributes": True}

class UserInGroup(BaseModel):
    id: int
    user_name: str
    points: int
    is_host: bool
    model_config = {"from_attributes": True}

class GroupDetail(BaseModel):
    id: int
    group_name: str
    owner_user_id: int
    hosts: list[HostUser]
    users: list[UserInGroup]
    shops: list[Shop]
    quests: list[Quest]
    
    model_config = {"from_attributes": True}

class UserWithGroups(BaseModel):
    id: int
    user_name: str
    groups: list[int]
    
    model_config = {"from_attributes": True}

class MemberRoleUpdate(BaseModel):
    is_host: bool

# --- Auth / Token ---
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: str | None = None