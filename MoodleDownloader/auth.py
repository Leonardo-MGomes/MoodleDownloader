from typing import Optional
import json

class Login:
    def __init__(self, username: str, password: str, login_token: Optional[str] = "", login_cookies: Optional[dict[str, str]] = None):
        self.Username = username
        self.Password = password
        self.LoginToken = login_token
        self.LoginCookies = login_cookies

    def __str__(self):
        return self.Username

    @classmethod
    def session_from_file(cls, filename: str = "session.json") -> "Login": # TODO: Make an encryption or redact password from session
        with open(filename, "r") as file:
            file_session = json.loads(file.read())
            clazz = cls("", "")
            clazz.__dict__ = file_session
            return clazz

    def session_to_file(self, filename: str = "session.json") -> None: # TODO: Make an encryption or redact password from session
        with open(filename, "w") as file:
            file.write(json.dumps(self.__dict__, indent=4))
        return
