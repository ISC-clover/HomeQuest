from pydantic import BaseModel

class UserCreate(BaseModel):
    name: str

class User(BaseModel):    
    id: int
    name: str
    
    class Config:
        from_attributes = True

class GroupCreate(BaseModel):
    name: str

class Group(BaseModel):
    id: int
    name: str
    
    class Config:
        from_attributes = True