from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file='.env',
        env_file_encoding='utf-8',
        case_sensitive=True,
        env_ignore_empty=True,
        extra='ignore',
    )

    # Project Details
    PROJECT_NAME: str = 'Project Name'
    PROJECT_VERSION: str = '0.0.0'
    PROJECT_DESCRIPTION: str = 'Add your description here'
    # Environment
    ENVIRONMENT: Literal['dev', 'prod'] = 'dev'
    DEBUG: bool = False
    # Database
    DATABASE_URL: str = 'sqlite:///db.sqlite'


app_settings = Settings()
