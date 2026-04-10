from __future__ import annotations

from typing import Literal

from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.analytics.schemas import CategoryPoint, QuestionCount, VolumePoint
from src.modules.chat.models import Conversation, ConversationStatus


class AnalyticsService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def kpis(self) -> dict[str, float | int]:
        total = int(await self.db.scalar(select(func.count(Conversation.id))) or 0)
        escalated = int(await self.db.scalar(select(func.count(Conversation.id)).where(Conversation.status == ConversationStatus.ESCALATED)) or 0)
        return {'total_conversations': total, 'resolution_rate': (total - escalated) / total if total else 0.0, 'avg_response_time_ms': 0.0, 'patients_served': total, 'escalation_rate': escalated / total if total else 0.0}

    async def volume(self, granularity: Literal['hour', 'day']) -> list[VolumePoint]:
        if granularity == 'hour':
            q = text("""
                SELECT EXTRACT(HOUR FROM created_at)::int AS bucket, COUNT(*)::int AS cnt
                FROM messages
                WHERE created_at >= NOW() - INTERVAL '7 days'
                GROUP BY EXTRACT(HOUR FROM created_at)
                ORDER BY bucket
            """)
        else:
            q = text("""
                SELECT DATE(created_at)::text AS bucket, COUNT(*)::int AS cnt
                FROM messages
                WHERE created_at >= NOW() - INTERVAL '30 days'
                GROUP BY DATE(created_at)
                ORDER BY bucket
            """)
        rows = (await self.db.execute(q)).mappings().all()
        if granularity == 'hour':
            counts: dict[int, int] = {}
            for row in rows:
                counts[int(row['bucket'])] = int(row['cnt'])
            return [
                VolumePoint(timestamp=f'{h:02d}:00', count=counts.get(h, 0)) for h in range(24)
            ]
        out: list[VolumePoint] = []
        for row in rows:
            b = row['bucket']
            cnt = row['cnt']
            ts = str(b)
            out.append(VolumePoint(timestamp=ts, count=cnt))
        return out

    async def categories(self) -> list[CategoryPoint]:
        q = text("""
            SELECT cat AS category, COUNT(*)::int AS cnt
            FROM (
                SELECT CASE
                    WHEN (
                        content ILIKE '%agendar%' OR content ILIKE '%horário%' OR content ILIKE '%consulta%'
                        OR content ILIKE '%marcar%' OR content ILIKE '%disponível%'
                    ) THEN 'agendamento'
                    WHEN (
                        content ILIKE '%implante%' OR content ILIKE '%canal%' OR content ILIKE '%extração%'
                        OR content ILIKE '%clareamento%' OR content ILIKE '%limpeza%' OR content ILIKE '%siso%'
                    ) THEN 'procedimento'
                    WHEN (
                        content ILIKE '%preço%' OR content ILIKE '%valor%' OR content ILIKE '%quanto%'
                        OR content ILIKE '%custa%' OR content ILIKE '%custo%' OR content ILIKE '%tabela%'
                    ) THEN 'preco'
                    WHEN (
                        content ILIKE '%convênio%' OR content ILIKE '%plano%' OR content ILIKE '%unimed%'
                        OR content ILIKE '%amil%' OR content ILIKE '%bradesco%' OR content ILIKE '%sulamerica%'
                    ) THEN 'convenio'
                    WHEN (
                        content ILIKE '%dor%' OR content ILIKE '%urgente%' OR content ILIKE '%urgência%'
                        OR content ILIKE '%emergência%' OR content ILIKE '%quebraram%' OR content ILIKE '%caiu%'
                    ) THEN 'emergencia'
                    ELSE 'outros'
                END AS cat
                FROM messages
                WHERE role::text = 'USER'
            ) sub
            GROUP BY cat
        """)
        rows = (await self.db.execute(q)).mappings().all()
        total = sum(int(r['cnt']) for r in rows)
        if total == 0:
            return []
        out: list[CategoryPoint] = []
        for row in rows:
            cnt = int(row['cnt'])
            pct = round(cnt / total * 100, 1)
            out.append(CategoryPoint(category=str(row['category']), count=cnt, percentage=pct))
        return out

    async def top_questions(self, limit: int) -> list[QuestionCount]:
        q = text("""
            SELECT SUBSTRING(content, 1, 80) AS question_preview, COUNT(*)::int AS cnt
            FROM messages
            WHERE role::text = 'USER'
            GROUP BY SUBSTRING(content, 1, 80)
            ORDER BY cnt DESC
            LIMIT :lim
        """)
        rows = (await self.db.execute(q, {'lim': limit})).mappings().all()
        return [QuestionCount(question_preview=str(r['question_preview']), count=int(r['cnt'])) for r in rows]
