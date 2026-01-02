from dataclasses import dataclass


@dataclass(frozen=True)
class AppConfig:
    BASE_URL: str = "https://moodle.bbbaden.ch"
    USER_AGENT: str = ("MoodleDownloader/0.1-dev (l.mirandagomes.inf25@stud.bbbaden.ch)")


DEFAULT_CONFIG = AppConfig()
