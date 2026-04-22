from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file='.env',
        env_file_encoding='utf-8',
        extra='ignore',
    )

    allowed_origins: list[str] = Field(
        default_factory=lambda: ['http://localhost:3000'],
        alias='ALLOWED_ORIGINS',
    )
    database_url: str = Field(..., alias='DATABASE_URL')
    redis_url: str = Field(..., alias='REDIS_URL')
    openai_api_key: str = Field(..., alias='OPENAI_API_KEY')
    minio_endpoint: str = Field(default='minio:9000', alias='MINIO_ENDPOINT')
    minio_access_key: str = Field(default='minioadmin', alias='MINIO_ACCESS_KEY')
    minio_secret_key: str = Field(default='minioadmin', alias='MINIO_SECRET_KEY')
    minio_bucket: str = Field(default='documents', alias='MINIO_BUCKET')

    whatsapp_access_token: str = Field(..., alias='WHATSAPP_ACCESS_TOKEN')
    whatsapp_phone_number_id: str = Field(..., alias='WHATSAPP_PHONE_NUMBER_ID')
    whatsapp_verify_token: str = Field(..., alias='WHATSAPP_VERIFY_TOKEN')
    whatsapp_app_secret: str = Field(..., alias='WHATSAPP_APP_SECRET')

    hash_salt: str = Field(..., alias='HASH_SALT')
    api_key: str = Field(..., alias='API_KEY')
    settings_encryption_key: str = Field(..., alias='SETTINGS_ENCRYPTION_KEY')

    clinic_name: str = Field(default='Clinica OdontoVida', alias='CLINIC_NAME')
    escalation_threshold: float = Field(default=0.70, alias='ESCALATION_THRESHOLD')
    trust_proxy: bool = Field(default=False, alias='TRUST_PROXY')
    rate_limit_global_per_minute: int = Field(default=100, alias='RATE_LIMIT_GLOBAL_PER_MINUTE')
    rate_limit_admin_per_minute: int = Field(default=30, alias='RATE_LIMIT_ADMIN_PER_MINUTE')
    rate_limit_webhook_per_minute: int = Field(default=120, alias='RATE_LIMIT_WEBHOOK_PER_MINUTE')
    log_level: str = Field(default='INFO', alias='LOG_LEVEL')
    environment: str = Field(default='development', alias='ENVIRONMENT')
    service_name: str = Field(default='odontobot-api', alias='SERVICE_NAME')
    service_version: str = Field(default='0.1.0', alias='SERVICE_VERSION')
    # URL pública da API (ex.: https://api.exemplo.com) para montar o callback do webhook no painel
    public_api_base_url: str | None = Field(default=None, alias='PUBLIC_API_BASE_URL')

    @field_validator('allowed_origins', mode='before')
    @classmethod
    def parse_cors_origins(cls, v: object) -> list[str]:
        if v is None or v == '':
            return ['http://localhost:3000']
        if isinstance(v, str):
            return [s.strip() for s in v.split(',') if s.strip()]
        if isinstance(v, list):
            return [str(x).strip() for x in v if str(x).strip()]
        return ['http://localhost:3000']

    @field_validator('allowed_origins')
    @classmethod
    def validate_allowed_origins(cls, v: list[str], info: object) -> list[str]:
        # Em produção, não permitir wildcard para evitar exposição CORS ampla.
        data = getattr(info, "data", {}) if info is not None else {}
        environment = str(data.get("environment", "development")).lower()
        if environment in {"production", "prod"} and "*" in v:
            raise ValueError("ALLOWED_ORIGINS não pode conter '*' em produção.")
        return v
