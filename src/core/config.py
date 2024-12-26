from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    OPENAI_API_KEY: str
    SAMPLE_RATE: int = 16000
    CHANNELS: int = 1
    CHUNK_SIZE: int = 1024
    
    # 이미지 관련 설정 추가
    MAX_IMAGE_SIZE: int = 4096  # OpenAI API 제한
    ALLOWED_IMAGE_FORMATS: list = ["png", "jpg", "jpeg"]
    
    class Config:
        env_file = ".env"

@lru_cache()
def get_settings():
    return Settings() 