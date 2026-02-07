from fastapi import FastAPI, Depends, HTTPException, Header
from sqlalchemy.orm import Session

from .config import settings
from .db import Base, engine, get_db
from . import models, schemas, services

app = FastAPI(title="Dopamine Coach API", version="1.0.0")


# ---------- Startup ----------
@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)


# ---------- Auth ----------
def require_api_key(x_api_key: str | None = Header(default=None)) -> None:
    if not x_api_key or x_api_key != settings.api_key:
        raise HTTPException(status_code=401, detail="Unauthorized")


# ---------- Routes ----------
@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/users", response_model=schemas.UserOut, dependencies=[Depends(require_api_key)])
def create_user(payload: schemas.UserCreate, db: Session = Depends(get_db)):
    existing = db.query(models.User).filter(models.User.tg_user_id == payload.tg_user_id).first()
    if existing:
        return existing
    user = models.User(tg_user_id=payload.tg_user_id, display_name=payload.display_name, is_active=True)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@app.get("/users/{tg_user_id}", response_model=schemas.UserOut, dependencies=[Depends(require_api_key)])
def get_user(tg_user_id: int, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.tg_user_id == tg_user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@app.post("/users/{user_id}/habits", response_model=list[schemas.HabitOut], dependencies=[Depends(require_api_key)])
def upsert_habits(user_id: int, payload: list[schemas.HabitCreate], db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.id == user_id, models.User.is_active == True).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    out = []
    for h in payload:
        row = db.query(models.Habit).filter(models.Habit.user_id == user_id, models.Habit.key == h.key).first()
        if row:
            row.title = h.title
            row.is_active = True
        else:
            row = models.Habit(user_id=user_id, key=h.key, title=h.title, is_active=True)
            db.add(row)
        out.append(row)

    db.commit()
    for r in out:
        db.refresh(r)
    return out


@app.get("/users/{user_id}/habits", response_model=list[schemas.HabitOut], dependencies=[Depends(require_api_key)])
def list_habits(user_id: int, db: Session = Depends(get_db)):
    return db.query(models.Habit).filter(models.Habit.user_id == user_id, models.Habit.is_active == True).all()


@app.post("/users/{user_id}/checkins", dependencies=[Depends(require_api_key)])
def create_checkin(user_id: int, payload: schemas.CheckInCreate, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.id == user_id, models.User.is_active == True).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    existing = db.query(models.CheckIn).filter(models.CheckIn.user_id == user_id, models.CheckIn.day == payload.day).first()
    if existing:
        raise HTTPException(status_code=409, detail="Check-in already exists for this day")

    checkin = models.CheckIn(
        user_id=user_id,
        day=payload.day,
        slip=payload.slip,
        healthy_minutes=payload.healthy_minutes,
    )
    db.add(checkin)
    db.flush()

    for item in payload.items:
        db.add(models.CheckInItem(checkin_id=checkin.id, habit_key=item.habit_key, done=item.done))

    db.commit()

    services.award_event_achievements(db, user_id=user_id, checkin_day=payload.day)

    return {"saved": True}


@app.get("/users/{user_id}/stats", response_model=schemas.StatsOut, dependencies=[Depends(require_api_key)])
def get_stats(user_id: int, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.id == user_id, models.User.is_active == True).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return services.compute_stats(db, user_id=user_id)


@app.get("/users/{user_id}/achievements", response_model=list[schemas.AchievementOut], dependencies=[Depends(require_api_key)])
def get_achievements(user_id: int, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.id == user_id, models.User.is_active == True).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return services.list_achievements(db, user_id=user_id)
