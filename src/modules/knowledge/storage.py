from __future__ import annotations

import asyncio
import io

from minio import Minio
from minio.error import S3Error

from src.config import Settings


class MinioStorage:
    def __init__(self, settings: Settings) -> None:
        self.bucket = settings.minio_bucket
        self.client = Minio(
            endpoint=settings.minio_endpoint,
            access_key=settings.minio_access_key,
            secret_key=settings.minio_secret_key,
            secure=False,
        )

    async def ensure_bucket(self) -> None:
        await asyncio.to_thread(self._ensure_bucket_sync)

    def _ensure_bucket_sync(self) -> None:
        if not self.client.bucket_exists(self.bucket):
            self.client.make_bucket(self.bucket)

    async def upload_bytes(self, object_name: str, content: bytes, content_type: str | None = None) -> None:
        await asyncio.to_thread(self._upload_bytes_sync, object_name, content, content_type)

    def _upload_bytes_sync(self, object_name: str, content: bytes, content_type: str | None = None) -> None:
        stream = io.BytesIO(content)
        self.client.put_object(
            bucket_name=self.bucket,
            object_name=object_name,
            data=stream,
            length=len(content),
            content_type=content_type or 'application/octet-stream',
        )

    async def download_bytes(self, object_name: str) -> bytes:
        return await asyncio.to_thread(self._download_bytes_sync, object_name)

    def _download_bytes_sync(self, object_name: str) -> bytes:
        response = self.client.get_object(self.bucket, object_name)
        try:
            return response.read()
        finally:
            response.close()
            response.release_conn()

    async def exists(self, object_name: str) -> bool:
        return await asyncio.to_thread(self._exists_sync, object_name)

    def _exists_sync(self, object_name: str) -> bool:
        try:
            self.client.stat_object(self.bucket, object_name)
            return True
        except S3Error as exc:
            if exc.code in {'NoSuchKey', 'NoSuchObject'}:
                return False
            raise
