import re
from dataclasses import dataclass
from typing import Optional

import requests
from bs4 import BeautifulSoup

from .config import DEFAULT_CONFIG, AppConfig
from .exceptions import MoodleAuthError, MoodleNoCredentialsError


@dataclass(frozen=True)
class MoodleCredentials:
    username: str
    password: str


@dataclass
class MoodleSession:
    login_cookies: dict
    login_token: Optional[str] = None
    sesskey: Optional[str] = None


class MoodleAuth:
    def __init__(self, session: requests.Session, moodle_credentials: Optional[MoodleCredentials] = None,
                 moodle_session: Optional[MoodleSession] = None, app_config: Optional[AppConfig] = DEFAULT_CONFIG):
        self.session = session
        self.base_url = app_config.BASE_URL
        self.user_agent = app_config.USER_AGENT
        self.session.headers["User-Agent"] = self.user_agent
        self.credentials = moodle_credentials
        self.moodle_session = moodle_session
        if self.moodle_session is not None:
            requests.utils.add_dict_to_cookiejar(self.session.cookies, self.moodle_session.login_cookies)

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
                raise MoodleAuthError(f"Site gave a different status code than expected: {index.status_code}")

    def _fetch_login_token(self) -> str:
        login_index_page = self.session.get(f"{self.base_url}/login/index.php")
        if login_index_page.status_code != 200:
            raise MoodleAuthError(f"Failed to fetch login page. Status code: {login_index_page.status_code}")
        login_soup = BeautifulSoup(login_index_page.content, features="html.parser")
        token_input = login_soup.find(name="input", attrs={"name": "logintoken"})
        if token_input is None or "value" not in token_input.attrs:
            raise MoodleAuthError("Failed to find login token in the login page")
        login_token = token_input.attrs["value"]
        return login_token

    def _extract_sesskey(self) -> str:
        response = self.session.get(self.base_url)
        if response.status_code != 200:
            raise MoodleAuthError("Failed to fetch landing page for token extraction.")

        sesskey_match = re.search(r'"sesskey":"([^"]+)"', response.text)
        if not sesskey_match:
            raise MoodleAuthError("Logged in successfully, but failed to find Moodle sesskey in the HTML response.")

        return sesskey_match.group(1)

    def _perform_login(self, token: str) -> dict:
        if not self.credentials:
            raise MoodleNoCredentialsError("No credentials provided")
        data = {
            "anchor": "",
            "logintoken": token,
            "username": self.credentials.username,
            "password": self.credentials.password
        }
        response = self.session.post(f"{self.base_url}/login/index.php", data=data)
        if response.status_code != 200:
            raise MoodleAuthError(f"Failed to perform login. Status code: {response.status_code}")
        login_cookies = self.session.cookies.get_dict()
        return login_cookies

    def login(self) -> MoodleSession:
        login_token = self._fetch_login_token()
        login_cookies = self._perform_login(login_token)
        moodle_sesskey = self._extract_sesskey()
        moodle_session = MoodleSession(login_cookies, login_token, moodle_sesskey)
        self.moodle_session = moodle_session
        if not self.is_session_valid():
            raise MoodleAuthError("Login failed: Invalid credentials or session could not be established")
        return moodle_session
