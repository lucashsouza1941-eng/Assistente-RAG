from fastapi import Depends, Header, HTTPException, status

from src.config import Settings
from src.dependencies import get_settings


async def require_api_key(
    x_api_key: str | None = Header(default=None, alias='X-API-Key'),
    settings: Settings = Depends(get_settings),
) -> None:
    if not x_api_key:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='X-API-Key header is required')
    if x_api_key != settings.api_key:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='Invalid API key provided')
