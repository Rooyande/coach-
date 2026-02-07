from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import date, datetime


class UserCreate(BaseModel):
    tg_user_id: int
    display_name: str = Field(min_length=1, max_length=120)


class UserOut(BaseModel):
    id: int
    tg_user_id: int
    display_name: str
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class HabitCreate(BaseModel):
    key: str = Field(min_length=1, max_length=64)
    title: str = Field(min_length=1, max_length=120)


class HabitOut(BaseModel):
    id: int
    key: str
    title: str
    is_active: bool

    class Config:
        from_attributes = True


class CheckInHabitItem(BaseModel):
    habit_key: str = Field(min_length=1, max_length=64)
    done: bool = True


class CheckInCreate(BaseModel):
    day: date
    slip: bool = False
    healthy_minutes: int = Field(ge=0, le=24 * 60)
    items: List[CheckInHabitItem] = Field(default_factory=list)


class CheckInOut(BaseModel):
    id: int
    day: date
    slip: bool
    healthy_minutes: int
    items: List[CheckInHabitItem]

    class Config:
        from_attributes = True


class StatsOut(BaseModel):
    user_id: int
    streak: int
    adherence_percent: float
    total_checkins: int
    slips: int
    healthy_minutes_total: int
    score: int


class AchievementOut(BaseModel):
    key: str
    title: str
    description: str
    icon: Optional[str] = None
    occurred_at: datetime
    share_text: Optional[str] = None
