from fastapi import FastAPI
from database import Base, engine
import models

app = FastAPI()

Base.metadata.create_all(bind=engine)

@app.get("/")
def root():
    return {"message": "HomeQuest backend is running!"}

@app.get("/health")
def health():
    return {"status":"ok"}

@app.post("/users")
def create_user(name: str):
    return {"user_id":1, "name":name}

@app.post("/groups")
def create_group(name: str):
    return {"group_id":1, "name":name}