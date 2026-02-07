from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from datetime import date, timedelta

from . import models


def calc_streak(days: list[date]) -> int:
    if not days:
        return 0
    s = set(days)
    d = max(days)
    streak = 0
    while d in s:
        streak += 1
        d = d - timedelta(days=1)
    return streak


def compute_stats(db: Session, user_id: int):
    rows = db.query(models.CheckIn.day, models.CheckIn.slip, models.CheckIn.healthy_minutes).filter(
        models.CheckIn.user_id == user_id
    ).all()

    if not rows:
        return dict(
            user_id=user_id,
            streak=0,
            adherence_percent=0.0,
            total_checkins=0,
            slips=0,
            healthy_minutes_total=0,
            score=0,
        )

    days = [r[0] for r in rows]
    total = len(rows)
    slips = sum(1 for _, slip, _ in rows if slip)
    adherence = ((total - slips) / total) * 100.0
    healthy_total = sum(int(m or 0) for _, _, m in rows)
    streak = calc_streak(days)

    # Score: پایبندی (هر روز 10) - لغزش (هر لغزش 15) + هر 30 دقیقه سالم 1
    score = (total * 10) - (slips * 15) + (healthy_total // 30)

    return dict(
        user_id=user_id,
        streak=streak,
        adherence_percent=round(adherence, 2),
        total_checkins=total,
        slips=slips,
        healthy_minutes_total=healthy_total,
        score=score,
    )


def ensure_achievement_definitions(db: Session):
    defs = [
        ("first_checkin", "اولین چک‌این", "اولین ثبت روزانه انجام شد.", "🏁",
         "من اولین چک‌این چالش دوپامین رو ثبت کردم 🏁"),
        ("streak_3", "۳ روز پشت‌سرهم", "۳ روز متوالی پایبند بودی.", "🔥",
         "۳ روز پشت‌سرهم تو چالش دوپامین پایبند بودم 🔥"),
        ("streak_7", "۷ روز پشت‌سرهم", "۷ روز متوالی پایبند بودی.", "💪",
         "۷ روز پشت‌سرهم پایبند بودم 💪"),
        ("no_slip_7", "یک هفته بدون لغزش", "۷ روز بدون لغزش ثبت شد.", "🛡️",
         "یک هفته بدون لغزش پیش رفتم 🛡️"),
    ]
    existing = {k for (k,) in db.query(models.AchievementDefinition.key).all()}
    for key, title, descp, icon, share in defs:
        if key in existing:
            continue
        db.add(models.AchievementDefinition(
            key=key, title=title, description=descp, icon=icon, share_text=share, is_active=True
        ))
    db.commit()


def award_event_achievements(db: Session, user_id: int, checkin_day: date):
    ensure_achievement_definitions(db)

    # helper: insert if not exists
    def grant(key: str):
        exists = db.query(models.AchievementEvent).filter(
            models.AchievementEvent.user_id == user_id,
            models.AchievementEvent.achievement_key == key,
        ).first()
        if exists:
            return
        db.add(models.AchievementEvent(user_id=user_id, achievement_key=key))
        db.commit()

    # first checkin
    total = db.query(func.count(models.CheckIn.id)).filter(models.CheckIn.user_id == user_id).scalar() or 0
    if total == 1:
        grant("first_checkin")

    # streak milestones
    days = [d for (d,) in db.query(models.CheckIn.day).filter(models.CheckIn.user_id == user_id).all()]
    streak = calc_streak(days)
    if streak >= 3:
        grant("streak_3")
    if streak >= 7:
        grant("streak_7")

    # no slip 7 days (last 7 days all slip=false and all days present)
    last7 = [checkin_day - timedelta(days=i) for i in range(7)]
    rows = db.query(models.CheckIn.day, models.CheckIn.slip).filter(
        models.CheckIn.user_id == user_id,
        models.CheckIn.day.in_(last7),
    ).all()
    if len(rows) == 7 and all(not slip for _, slip in rows):
        grant("no_slip_7")


def list_achievements(db: Session, user_id: int):
    q = db.query(
        models.AchievementEvent.achievement_key,
        models.AchievementEvent.occurred_at,
        models.AchievementDefinition.title,
        models.AchievementDefinition.description,
        models.AchievementDefinition.icon,
        models.AchievementDefinition.share_text,
    ).join(
        models.AchievementDefinition,
        models.AchievementDefinition.key == models.AchievementEvent.achievement_key
    ).filter(
        models.AchievementEvent.user_id == user_id
    ).order_by(desc(models.AchievementEvent.occurred_at))

    return [
        dict(
            key=k,
            occurred_at=ts,
            title=title,
            description=desc_,
            icon=icon,
            share_text=share_text,
        )
        for (k, ts, title, desc_, icon, share_text) in q.all()
    ]
