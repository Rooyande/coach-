from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel
from typing import List
from datetime import date

app = FastAPI(title="Dopamine Coach API", version="1.0.0")


# --------- Models ---------
class User(BaseModel):
    id: int
    name: str
    is_active: bool = True


class CheckIn(BaseModel):
    user_id: int
    day: date
    habits_done: List[str]
    slip: bool = False
    healthy_minutes: int = 0


# --------- In-Memory Store (later DB) ---------
USERS: dict[int, User] = {}
CHECKINS: list[CheckIn] = []


# --------- Dependencies ---------
def get_user(user_id: int) -> User:
    user = USERS.get(user_id)
    if not user or not user.is_active:
        raise HTTPException(status_code=404, detail="User not found")
    return user


# --------- Routes ---------
@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/users", response_model=User)
def add_user(user: User):
    USERS[user.id] = user
    return user


@app.post("/checkin")
def daily_checkin(checkin: CheckIn, user: User = Depends(get_user)):
    CHECKINS.append(checkin)
    return {"saved": True}


@app.get("/stats/{user_id}")
def stats(user_id: int):
    user_checkins = [c for c in CHECKINS if c.user_id == user_id]
    if not user_checkins:
        return {"streak": 0, "score": 0}

    streak = len(user_checkins)
    score = sum(1 for c in user_checkins if not c.slip)

    return {
        "streak": streak,
        "score": score,
        "checkins": len(user_checkins),
    }
