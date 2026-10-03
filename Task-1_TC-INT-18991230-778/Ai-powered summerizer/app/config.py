import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production")
    MAX_CONTENT_LENGTH = int(os.getenv("MAX_UPLOAD_BYTES", 5 * 1024 * 1024))
    UPLOAD_FOLDER = BASE_DIR / "uploads"
    EXPORT_FOLDER = BASE_DIR / "exports"
    ALLOWED_EXTENSIONS = {"txt", "pdf"}

    MIN_TEXT_LENGTH = 100
    MAX_TEXT_LENGTH = 50_000
    MAX_BATCH_COMBINED_CHARS = int(os.getenv("MAX_BATCH_COMBINED_CHARS", 150_000))
    DEFAULT_SUMMARY_RATIO = 0.3
    MIN_SUMMARY_RATIO = 0.1
    MAX_SUMMARY_RATIO = 0.9

    CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*")
    RATELIMIT_DEFAULT = os.getenv("RATELIMIT_DEFAULT", "200 per day;50 per hour")
    RATELIMIT_STORAGE_URI = os.getenv("RATELIMIT_STORAGE_URI", "memory://")


class DevelopmentConfig(Config):
    DEBUG = True
    TESTING = False


class ProductionConfig(Config):
    DEBUG = False
    TESTING = False

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)

    @classmethod
    def validate(cls):
        if cls.SECRET_KEY == "dev-secret-key-change-in-production":
            raise RuntimeError(
                "SECRET_KEY must be set via environment variable in production."
            )


class TestingConfig(Config):
    TESTING = True
    DEBUG = True


_config_map = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "testing": TestingConfig,
}


def get_config():
    env = os.getenv("FLASK_ENV", "development")
    return _config_map.get(env, DevelopmentConfig)
