from fastapi import FastAPI, Depends, HTTPException
from database import Base, engine, get_db
import models, schemas, crud
from sqlalchemy.orm import Session

app = FastAPI()

Base.metadata.create_all(bind=engine)

@app.get("/")
def root():
    return {"message": "HomeQuest backend is running!"}

@app.post("/users", response_model=schemas.User)
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    return crud.create_user(db, user)

@app.get("/users", response_model=list[schemas.UserWithGroups])
def read_users(db: Session = Depends(get_db)):
    return crud.get_users(db)

@app.post("/groups", response_model=schemas.Group)
def create_group(group: schemas.GroupCreate, db: Session = Depends(get_db)):
    owner = db.query(models.User).filter(models.User.id == group.owner_user_id).first()
    if not owner:
        raise HTTPException(status_code=404, detail="Owner user not found")
    return crud.create_group(db, group)

@app.get("/groups", response_model=list[schemas.Group])
def read_groups(db: Session = Depends(get_db)):
    return crud.get_groups(db)

@app.post("/groups/{group_id}/users/{user_id}")
def add_user_to_group(group_id: int, user_id: int, db: Session = Depends(get_db)):
    return crud.add_user_to_group(db, user_id, group_id)

@app.get("/groups/{group_id}", response_model=schemas.GroupDetail)
def read_group_detail(group_id: int, db: Session = Depends(get_db)):
    group = crud.get_group_detail(db, group_id)
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    return group