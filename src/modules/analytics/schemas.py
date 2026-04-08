from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class KPIResponse(BaseModel):
    total_conversations: int
    resolution_rate: float
    avg_response_time_ms: float
    patients_served: int
    escalation_rate: float


class VolumePoint(BaseModel):
    timestamp: datetime
    count: int


class CategoryPoint(BaseModel):
    category: str
    count: int
    percentage: float


class QuestionCount(BaseModel):
    question_preview: str
    count: int
