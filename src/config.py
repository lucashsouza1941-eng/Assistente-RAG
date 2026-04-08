from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8')

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
