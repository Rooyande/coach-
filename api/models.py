from sqlalchemy import Column, Integer, String, Boolean, Date, DateTime, ForeignKey, UniqueConstraint, Index
from sqlalchemy.orm import relationship
from datetime import datetime
from .db import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    tg_user_id = Column(Integer, unique=True, index=True, nullable=False)
    display_name = Column(String(120), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    habits = relationship("Habit", back_populates="user", cascade="all, delete-orphan")
    checkins = relationship("CheckIn", back_populates="user", cascade="all, delete-orphan")
    achievement_events = relationship("AchievementEvent", back_populates="user", cascade="all, delete-orphan")


class Habit(Base):
    __tablename__ = "habits"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    key = Column(String(64), nullable=False)          # e.g. "no_social", "no_porn"
    title = Column(String(120), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    user = relationship("User", back_populates="habits")

    __table_args__ = (
        UniqueConstraint("user_id", "key", name="uq_habits_user_key"),
        Index("ix_habits_user_active", "user_id", "is_active"),
    )


class CheckIn(Base):
    __tablename__ = "checkins"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    day = Column(Date, nullable=False)
    slip = Column(Boolean, default=False, nullable=False)
    healthy_minutes = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    user = relationship("User", back_populates="checkins")
    items = relationship("CheckInItem", back_populates="checkin", cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint("user_id", "day", name="uq_checkins_user_day"),
        Index("ix_checkins_user_day", "user_id", "day"),
    )


class CheckInItem(Base):
    __tablename__ = "checkin_items"

    id = Column(Integer, primary_key=True)
    checkin_id = Column(Integer, ForeignKey("checkins.id", ondelete="CASCADE"), nullable=False)
    habit_key = Column(String(64), nullable=False)
    done = Column(Boolean, default=True, nullable=False)

    checkin = relationship("CheckIn", back_populates="items")

    __table_args__ = (
        Index("ix_checkin_items_checkin", "checkin_id"),
    )


class AchievementDefinition(Base):
    __tablename__ = "achievement_definitions"

    id = Column(Integer, primary_key=True)
    key = Column(String(64), unique=True, nullable=False)  # e.g. "first_checkin"
    title = Column(String(120), nullable=False)
    description = Column(String(240), nullable=False)
    icon = Column(String(64), nullable=True)               # emoji name / icon key
    share_text = Column(String(300), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)


class AchievementEvent(Base):
    __tablename__ = "achievement_events"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    achievement_key = Column(String(64), nullable=False)
    occurred_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    user = relationship("User", back_populates="achievement_events")

    __table_args__ = (
        UniqueConstraint("user_id", "achievement_key", name="uq_ach_user_key"),
        Index("ix_ach_user_time", "user_id", "occurred_at"),
    )
