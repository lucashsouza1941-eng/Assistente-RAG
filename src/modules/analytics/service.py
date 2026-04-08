from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.chat.models import Conversation, ConversationStatus


class AnalyticsService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def kpis(self) -> dict:
        total = int(await self.db.scalar(select(func.count(Conversation.id))) or 0)
        escalated = int(await self.db.scalar(select(func.count(Conversation.id)).where(Conversation.status == ConversationStatus.ESCALATED)) or 0)
        return {'total_conversations': total, 'resolution_rate': (total - escalated) / total if total else 0.0, 'avg_response_time_ms': 0.0, 'patients_served': total, 'escalation_rate': escalated / total if total else 0.0}
