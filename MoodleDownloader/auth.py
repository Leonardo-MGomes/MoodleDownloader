import json
from dataclasses import dataclass
from typing import Optional

import requests
from bs4 import BeautifulSoup

from .config import DEFAULT_CONFIG, AppConfig


@dataclass
class MoodleLogin:
    Username: str
    Password: str
    LoginToken: Optional[str] = None
    LoginCookies: Optional[dict] = None


class MoodleAuth:
    def __init__(self, session: requests.Session, login: Optional[MoodleLogin] = None, app_config: Optional[AppConfig] = DEFAULT_CONFIG):
        self.session = session
        self.login = login or MoodleLogin("", "") # TODO: Check/Ask for login creds instead of using empty MoodleLogin
        if self.login.LoginCookies is not None:
            self.session.cookies.update(self.login.LoginCookies)
        self.base_url = app_config.BASE_URL

    def _is_login_valid(self) -> bool:
        index = self.session.head(self.base_url, allow_redirects=False)
        match index.status_code:
            case 303:
                return False
            case 200:
                return True
            case _:
                raise Exception("Site gave a different status code than expected")

    def _get_login_token(self) -> str:
        login_index_page = self.session.get(f"{self.base_url}/login/index.php")
        login_soup = BeautifulSoup(login_index_page.content, features="html.parser")
        login_token = login_soup.find(name="input", attrs={"name": "logintoken"}).attrs["value"]
        return login_token

    def _get_login_cookies(self) -> None:
        self.login.LoginToken = self._get_login_token()
        data = {
            "anchor": "",
            "logintoken": self.login.LoginToken,
            "username": self.login.Username,
            "password": self.login.Password
        }
        self.session.post(f"{self.base_url}/login/index.php", data=data)
        self.login.LoginCookies = self.session.cookies.get_dict()
        return

    def get_login(self) -> MoodleLogin:
        if not self._is_login_valid():
            self._get_login_cookies()
        return self.login

    def session_from_file(self, filename: str = "session.json") -> None: # TODO: Make an encryption or redact password from session
        with open(filename, "r") as file:
            file_session = json.loads(file.read())
            self.login.__dict__ = file_session
        return

    def session_to_file(self, filename: str = "session.json") -> None: # TODO: Make an encryption or redact password from session
        with open(filename, "w") as file:
            file.write(json.dumps(self.login.__dict__, indent=4))
        return
