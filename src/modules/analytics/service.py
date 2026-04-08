from __future__ import annotations

from datetime import datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.chat.models import Conversation, ConversationStatus, Message, MessageRole


class AnalyticsService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_kpis(self, period: str) -> dict:
        since = self._period_start(period)
        total = int(await self.db.scalar(select(func.count(Conversation.id)).where(Conversation.started_at >= since)) or 0)
        escalated = int(await self.db.scalar(select(func.count(Conversation.id)).where(Conversation.started_at >= since, Conversation.status == ConversationStatus.ESCALATED)) or 0)
        resolved = max(total - escalated, 0)
        avg_response = float(await self.db.scalar(select(func.avg(Message.response_time_ms)).where(Message.created_at >= since, Message.role == MessageRole.ASSISTANT)) or 0.0)
        return {'total_conversations': total, 'resolution_rate': (resolved / total) if total else 0.0, 'avg_response_time_ms': avg_response, 'patients_served': total, 'escalation_rate': (escalated / total) if total else 0.0}

    async def get_volume(self, granularity: str) -> list[dict]:
        bucket = func.date_trunc('hour' if granularity == 'hour' else 'day', Message.created_at)
        result = await self.db.execute(select(bucket.label('timestamp'), func.count(Message.id).label('count')).group_by(bucket).order_by(bucket.asc()))
        return [{'timestamp': row.timestamp, 'count': int(row.count)} for row in result]

    async def get_categories(self) -> list[dict]:
        categories = ['agendamento', 'procedimento', 'preco', 'convenio', 'emergencia', 'outros']
        total = int(await self.db.scalar(select(func.count(Message.id)).where(Message.role == MessageRole.USER)) or 0)
        if total == 0:
            return [{'category': c, 'count': 0, 'percentage': 0.0} for c in categories]
        out: list[dict] = []
        for c in categories:
            count = int(await self.db.scalar(select(func.count(Message.id)).where(Message.role == MessageRole.USER, func.lower(Message.content).like(f'%{c}%'))) or 0)
            out.append({'category': c, 'count': count, 'percentage': count / total})
        return out

    async def get_top_questions(self, limit: int) -> list[dict]:
        preview = func.left(Message.content, 120)
        rows = await self.db.execute(select(preview.label('question_preview'), func.count(Message.id).label('count')).where(Message.role == MessageRole.USER).group_by(preview).order_by(func.count(Message.id).desc()).limit(limit))
        return [{'question_preview': row.question_preview, 'count': int(row.count)} for row in rows]

    @staticmethod
    def _period_start(period: str) -> datetime:
        now = datetime.utcnow()
        if period == 'today':
            return datetime(now.year, now.month, now.day)
        if period == '7d':
            return now - timedelta(days=7)
        return now - timedelta(days=30)
