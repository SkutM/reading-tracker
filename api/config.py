from pydantic_settings import BaseSettings

# load env vars from the .env file automatically
class Settings(BaseSettings):
    # must match the key in .env file
    JWT_SECRET_KEY: str = "your-default-secret-key"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

settings = Settings()