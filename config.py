from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    aws_access_key: str
    aws_secret_key: str
    bucket_name: str

    def __init__(self, **data):
        super().__init__(**data)

settings = Settings()