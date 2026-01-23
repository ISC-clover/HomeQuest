from pydantic import BaseModel

class UserCreate(BaseModel):
    name: str

class User(BaseModel):    
    id: int
    name: str
    
    model_config = {"from_attributes": True}

class GroupCreate(BaseModel):
    name: str
    owner_user_id: int

class Group(BaseModel):
    id: int
    name: str
    owner_user_id: int
    
    model_config = {"from_attributes": True}

class HostUser(BaseModel):
    id: int
    name: str
    
    model_config = {"from_attributes": True}

class UserInGroup(BaseModel):
    id: int
    name: str
    points: int
    is_host: bool
    
    model_config = {"from_attributes": True}

class GroupDetail(BaseModel):
    id: int
    name: str
    owner_user_id: int
    reward_shop: str | None
    hosts: list[HostUser]
    users: list[UserInGroup]
    
    model_config = {"from_attributes": True}

class UserWithGroups(BaseModel):
    id: int
    name: str
    groups: list[int]
    
    model_config = {"from_attributes": True}