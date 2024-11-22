from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    openai_base_url: str
    gpt_model: str
    sqlalchemy_db_uri: str
    rabbitmq_host: str
    rabbitmq_port: int
    rabbitmq_user: str
    rabbitmq_password: str
    port: int = 8234
    default_page_size: int = 100



@lru_cache()
def get_settings():
    return Settings()