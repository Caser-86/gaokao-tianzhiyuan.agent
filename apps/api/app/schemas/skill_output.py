from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

SkillIntent = Literal[
    "school_recommendation",
    "major_recommendation",
    "volunteer_strategy",
    "comparison",
    "fallback",
]


class SkillAction(BaseModel):
    model_config = ConfigDict(extra="ignore", strict=True)

    type: Literal["open_school", "open_major"]
    label: str = Field(min_length=1, max_length=100)
    target: str = Field(
        pattern=r"^/(?:schools|majors)/[a-z0-9]+(?:-[a-z0-9]+)*$",
        max_length=160,
    )


class SkillOutput(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    intent: SkillIntent
    summary: str = Field(min_length=1, max_length=500)
    entities: dict[str, Any]
    analysis: str = Field(max_length=4000)
    suggestions: list[dict[str, Any]] = Field(max_length=20)
    follow_up_questions: list[str] = Field(max_length=3)
    actions: list[SkillAction] = Field(max_length=20)
    risk_flags: list[str] = Field(max_length=20)
    rendered_reply: str = Field(max_length=6000)
