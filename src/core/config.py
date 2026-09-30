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
    PROJECT_NAME: str = 'Habits.py'
    PROJECT_VERSION: str = '0.1.0'
    PROJECT_DESCRIPTION: str = 'Track Daily and Weekly Habits from the command line.'
    # Environment
    ENVIRONMENT: Literal['local', 'dev', 'prod'] = 'local'
    DEBUG: bool = False
    # Database
    DATABASE_URL: str = 'sqlite:///local.db'


app_settings = Settings()
