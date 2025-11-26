from typing import Literal

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
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
