from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Text, DateTime, Enum
from sqlalchemy.orm import relationship
from database import Base
from datetime import datetime

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    user_name = Column(String, index=True)
    password = Column(String)
    
    groups = relationship("UserGroup", back_populates="user")
    quest_logs = relationship("QuestCompletionLog", back_populates="user")

class Group(Base):
    __tablename__ = "groups"
    
    id = Column(Integer, primary_key=True, index=True)
    group_name = Column(String, index=True)
    owner_user_id = Column(Integer, ForeignKey("users.id"))
    invite_code = Column(String, unique=True, index=True, nullable=True)
    
    members = relationship("UserGroup", back_populates="group")
    shops = relationship("Shop", back_populates="group")
    quests = relationship("Quest", back_populates="group")
    quest_logs = relationship("QuestCompletionLog", back_populates="group")

class UserGroup(Base):
    __tablename__ = "user_groups"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    group_id = Column(Integer, ForeignKey("groups.id"))  
    points = Column(Integer, default=0)
    is_host = Column(Boolean, default=False)
    
    user = relationship("User", back_populates="groups")
    group = relationship("Group", back_populates="members")

class Shop(Base):
    __tablename__ = "shops"
    
    id = Column(Integer, primary_key=True, index=True)
    group_id = Column(Integer, ForeignKey("groups.id"))
    item_name = Column(String, index=True)
    description = Column(Text, nullable=True)
    cost_points = Column(Integer)
    limit_per_user = Column(Integer, nullable=True)
    
    group = relationship("Group", back_populates="shops")

class PurchaseHistory(Base):
    __tablename__ = "purchase_history"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    group_id = Column(Integer, ForeignKey("groups.id"))
    item_name = Column(String)
    cost = Column(Integer)
    purchased_at = Column(DateTime, default=datetime.now)

class Quest(Base):
    __tablename__ = "quests"
    
    id = Column(Integer, primary_key=True, index=True)
    group_id = Column(Integer, ForeignKey("groups.id"))
    quest_name = Column(String, index=True)
    description = Column(Text, nullable=True)
    start_time = Column(DateTime)
    end_time = Column(DateTime)
    reward_points = Column(Integer, default=10)
    recurrence = Column(String, default="one_off") 
    
    group = relationship("Group", back_populates="quests")
    logs = relationship("QuestCompletionLog", back_populates="quest")

class QuestCompletionLog(Base):
    __tablename__ = "quest_completion_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    quest_id = Column(Integer, ForeignKey("quests.id"))
    group_id = Column(Integer, ForeignKey("groups.id"))
    status = Column(String, default="pending")
    proof_image_path = Column(String, nullable=True)
    completed_at = Column(DateTime, default=datetime.now)
    
    user = relationship("User", back_populates="quest_logs")
    quest = relationship("Quest", back_populates="logs")
    group = relationship("Group", back_populates="quest_logs")