from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8')

    app_name: str = 'Assistente RAG API'
    environment: str = 'development'
    debug: bool = True

    database_url: str = Field(..., alias='DATABASE_URL')
    redis_url: str = Field(..., alias='REDIS_URL')

    openai_api_key: str = Field(..., alias='OPENAI_API_KEY')
    embedding_model: str = 'text-embedding-3-small'
    chat_model: str = 'gpt-4o'

    escalation_threshold: float = 0.70
    clinic_name: str = 'Clinica OdontoVida'

    whatsapp_verify_token: str = Field(..., alias='WHATSAPP_VERIFY_TOKEN')
    whatsapp_app_secret: str = Field(..., alias='WHATSAPP_APP_SECRET')
    whatsapp_access_token: str = Field(..., alias='WHATSAPP_ACCESS_TOKEN')
    whatsapp_phone_number_id: str = Field(..., alias='WHATSAPP_PHONE_NUMBER_ID')
    hash_salt: str = Field(..., alias='HASH_SALT')

    api_key: str = Field(..., alias='API_KEY')
