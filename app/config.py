from pydantic_settings import BaseSettings
import os

class Settings(BaseSettings):
    PROJECT_NAME: str = "VTuber Song Database"
    API_V1_STR: str = "/api/v1"
    DATABASE_URL: str = "sqlite:///./vtuber_songs.db"

    class Config:
        case_sensitive = True

settings = Settings()
