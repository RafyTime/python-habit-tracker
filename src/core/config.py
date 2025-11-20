from typing import Literal

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    PROJECT_NAME: str = 'Project Name'
    PROJECT_VERSION: str = '0.0.0'
    PROJECT_DESCRIPTION: str = 'Add your description here'
    ENVIRONMENT: Literal['dev', 'prod'] = 'dev'
    DEBUG: bool = False


app_settings = Settings()
