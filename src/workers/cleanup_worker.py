from __future__ import annotations

import shutil
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from uuid import UUID

from arq import cron
from arq.connections import RedisSettings
from sqlalchemy import select

from src.core.logging import get_logger
from src.dependencies import AsyncSessionLocal, get_settings
from src.modules.chat.models import Conversation, ConversationStatus
from src.modules.knowledge.models import Document

log = get_logger(module='workers.cleanup')
settings = get_settings()


async def cleanup_job(ctx: dict) -> dict:
    try:
        now_utc = datetime.now(timezone.utc)
        cutoff_conversation = now_utc - timedelta(hours=24)
        cutoff_tmp = time.time() - 3600

        conversations_closed = 0
        tmp_dirs_removed = 0

        async with AsyncSessionLocal() as db:
            async with db.begin():
                rows = (
                    await db.execute(
                        select(Conversation).where(
                            Conversation.status == ConversationStatus.ACTIVE,
                            Conversation.last_message_at < cutoff_conversation,
                        )
                    )
                ).scalars().all()
                for conv in rows:
                    conv.status = ConversationStatus.CLOSED
                conversations_closed = len(rows)

                tmp_root = Path("/tmp")
                if tmp_root.exists():
                    for d in tmp_root.iterdir():
                        if not d.is_dir():
                            continue
                        if d.stat().st_mtime >= cutoff_tmp:
                            continue
                        try:
                            doc_id = UUID(d.name)
                        except ValueError:
                            continue
                        doc_exists = await db.scalar(select(Document.id).where(Document.id == doc_id))
                        if doc_exists is None:
                            shutil.rmtree(d, ignore_errors=True)
                            tmp_dirs_removed += 1

        log.info(
            "cleanup_completed",
            metadata={
                "conversations_closed": conversations_closed,
                "tmp_dirs_removed": tmp_dirs_removed,
            },
        )
        return {"conversations_closed": conversations_closed, "tmp_dirs_removed": tmp_dirs_removed}
    except Exception as exc:
        log.error(
            "cleanup_failed",
            error_type=type(exc).__name__,
            error_message=str(exc)[:200],
        )
        raise


class CleanupWorkerSettings:
    cron_jobs = [cron(cleanup_job, hour=set(range(0, 24)), minute=0)]
    redis_settings = RedisSettings.from_dsn(settings.redis_url)
