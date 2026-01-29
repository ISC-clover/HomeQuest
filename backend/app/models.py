from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Text, DateTime
from sqlalchemy.orm import relationship
from database import Base

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    user_name = Column(String, index=True)
    password = Column(String)
    
    groups = relationship("UserGroup", back_populates="user")

class Group(Base):
    __tablename__ = "groups"
    
    id = Column(Integer, primary_key=True, index=True)
    group_name = Column(String, index=True)
    owner_user_id = Column(Integer, ForeignKey("users.id"))
    
    members = relationship("UserGroup", back_populates="group")
    
    shops = relationship("Shop", back_populates="group")
    quests = relationship("Quest", back_populates="group")

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
    reward_name = Column(String)
    cost = Column(Integer)
    description = Column(Text, nullable=True)
    
    group = relationship("Group", back_populates="shops")

class Quest(Base):
    __tablename__ = "quests"
    
    id = Column(Integer, primary_key=True, index=True)
    group_id = Column(Integer, ForeignKey("groups.id"))
    quest_name = Column(String)
    description = Column(Text, nullable=True)
    start_time = Column(DateTime, nullable=True)
    end_time = Column(DateTime, nullable=True)
    
    group = relationship("Group", back_populates="quests")