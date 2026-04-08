from fastapi import Depends, Header, HTTPException, status

from src.dependencies import get_settings


async def require_api_key(x_api_key: str | None = Header(default=None, alias='X-API-Key'), settings=Depends(get_settings)) -> None:
    if not x_api_key or x_api_key != settings.api_key:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Invalid API key')

