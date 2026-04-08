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
    chat_model: str = 'gpt-4o-mini'
    meta_verify_token: str = Field(..., alias='META_VERIFY_TOKEN')
    whatsapp_app_secret: str = Field(..., alias='WHATSAPP_APP_SECRET')
    whatsapp_access_token: str = Field(..., alias='WHATSAPP_ACCESS_TOKEN')
    whatsapp_phone_number_id: str = Field(..., alias='WHATSAPP_PHONE_NUMBER_ID')
    api_key: str = Field(..., alias='API_KEY')

