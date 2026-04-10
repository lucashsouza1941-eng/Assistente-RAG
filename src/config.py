from typing import Any

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8')

    cors_origins: list[str] = Field(default_factory=lambda: ['http://localhost:3000'], alias='CORS_ORIGINS')
    database_url: str = Field(..., alias='DATABASE_URL')
    redis_url: str = Field(..., alias='REDIS_URL')
    openai_api_key: str = Field(..., alias='OPENAI_API_KEY')

    whatsapp_access_token: str = Field(..., alias='WHATSAPP_ACCESS_TOKEN')
    whatsapp_phone_number_id: str = Field(..., alias='WHATSAPP_PHONE_NUMBER_ID')
    whatsapp_verify_token: str = Field(..., alias='WHATSAPP_VERIFY_TOKEN')
    whatsapp_app_secret: str = Field(..., alias='WHATSAPP_APP_SECRET')

    hash_salt: str = Field(..., alias='HASH_SALT')
    api_key: str = Field(..., alias='API_KEY')

    clinic_name: str = Field(default='Clinica OdontoVida', alias='CLINIC_NAME')
    escalation_threshold: float = Field(default=0.70, alias='ESCALATION_THRESHOLD')
    log_level: str = Field(default='INFO', alias='LOG_LEVEL')
    environment: str = Field(default='development', alias='ENVIRONMENT')
    service_name: str = Field(default='odontobot-api', alias='SERVICE_NAME')
    service_version: str = Field(default='0.1.0', alias='SERVICE_VERSION')

    @field_validator('cors_origins', mode='before')
    @classmethod
    def parse_cors_origins(cls, v: Any) -> list[str]:
        if v is None or v == '':
            return ['http://localhost:3000']
        if isinstance(v, str):
            return [s.strip() for s in v.split(',') if s.strip()]
        if isinstance(v, list):
            return [str(x).strip() for x in v if str(x).strip()]
        return ['http://localhost:3000']
