from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from io import BytesIO
from typing import Iterable, List, Tuple

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402


@dataclass(frozen=True)
class StatsCard:
    user_display_name: str
    period_label: str
    streak: int
    adherence_percent: float
    score: int
    total_checkins: int
    slips: int
    healthy_minutes_total: int


def render_stats_card_png(card: StatsCard) -> bytes:
    fig = plt.figure(figsize=(9, 5), dpi=160)
    ax = fig.add_subplot(111)
    ax.axis("off")

    title = f"{card.user_display_name} — {card.period_label}"
    lines = [
        f"Streak: {card.streak}",
        f"Adherence: {card.adherence_percent:.2f}%",
        f"Score: {card.score}",
        f"Check-ins: {card.total_checkins}",
        f"Slips: {card.slips}",
        f"Healthy minutes: {card.healthy_minutes_total}",
    ]

    ax.text(0.03, 0.92, title, fontsize=18, fontweight="bold", va="top")
    y = 0.80
    for ln in lines:
        ax.text(0.05, y, ln, fontsize=14, va="top")
        y -= 0.10

    buf = BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight", pad_inches=0.3)
    plt.close(fig)
    return buf.getvalue()


def render_trend_png(points: List[Tuple[date, int]], title: str = "Score Trend") -> bytes:
    fig = plt.figure(figsize=(9, 4.5), dpi=160)
    ax = fig.add_subplot(111)

    xs = [p[0] for p in points]
    ys = [p[1] for p in points]

    ax.plot(xs, ys)
    ax.set_title(title)
    ax.set_xlabel("Day")
    ax.set_ylabel("Score")

    fig.autofmt_xdate()

    buf = BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight", pad_inches=0.2)
    plt.close(fig)
    return buf.getvalue()
