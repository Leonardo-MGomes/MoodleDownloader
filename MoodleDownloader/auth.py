from dataclasses import dataclass
from typing import Optional

import requests
from bs4 import BeautifulSoup

from .config import DEFAULT_CONFIG, AppConfig


@dataclass(frozen=True)
class MoodleCredentials:
    username: str
    password: str


@dataclass
class MoodleSession:
    login_cookies: dict
    login_token: Optional[str] = None


class MoodleAuth:
    def __init__(self, session: requests.Session, moodle_credentials: MoodleCredentials, app_config: Optional[AppConfig] = DEFAULT_CONFIG):
        self.session = session
        self.credentials = moodle_credentials
        self.base_url = app_config.BASE_URL

    @classmethod
    def from_credentials(cls, session: requests.Session, username: str, password: str, **kwargs) -> "MoodleAuth":
        credentials = MoodleCredentials(username, password)
        return cls(session=session, moodle_credentials=credentials, **kwargs)

    def is_session_valid(self) -> bool:
        index = self.session.head(self.base_url, allow_redirects=False)
        match index.status_code:
            case 303:
                return False
            case 200:
                return True
            case _:
                raise Exception("Site gave a different status code than expected")

    def _fetch_login_token(self) -> str:
        login_index_page = self.session.get(f"{self.base_url}/login/index.php")
        login_soup = BeautifulSoup(login_index_page.content, features="html.parser")
        login_token = login_soup.find(name="input", attrs={"name": "logintoken"}).attrs["value"]
        return login_token

    def _perform_login(self, token: str) -> dict:
        data = {
            "anchor": "",
            "logintoken": token,
            "username": self.credentials.username,
            "password": self.credentials.password
        }
        self.session.post(f"{self.base_url}/login/index.php", data=data)
        login_cookies = self.session.cookies.get_dict()
        return login_cookies

    def login(self) -> MoodleSession:
        login_token = self._fetch_login_token()
        login_cookies = self._perform_login(login_token)
        moodle_session = MoodleSession(login_cookies, login_token)
        return moodle_session
