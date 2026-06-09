from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    MONGODB_URI: str = "mongodb://localhost:27017"
    DB_NAME: str = "invenzo_db"
    CHUNK_SIZE: int = 10
    
    NOTIFY_EMAIL: str
    SMTP_HOST: str
    SMTP_PORT: int = 587
    SMTP_USER: str
    SMTP_PASSWORD: str

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()