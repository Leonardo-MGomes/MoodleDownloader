from dataclasses import dataclass

from .user_agent import build_user_agent


@dataclass(frozen=True)
class AppConfig:
    BASE_URL: str = "https://moodle.bbbaden.ch"
    USER_AGENT: str = build_user_agent("moodle-downloader")


DEFAULT_CONFIG = AppConfig()
