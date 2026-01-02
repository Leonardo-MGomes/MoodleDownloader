import json

from env import USERNAME, PASSWORD

import enum
from dataclasses import dataclass
from typing import Tuple, Optional

import requests as rq
from bs4 import BeautifulSoup

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

class ResourceType(enum.Enum):
    ASSIGNMENT = "assign"
    RESOURCE = "resource"
    FOLDER = "folder"
    PAGE = "page"
    URL = "url"
    QUIZ = "quiz"
    FORUM = "forum"
    LABEL = "label"
    FEEDBACK = "feedback"
    JOURNAL = "journal"
    UNKNOWN = "unknown"

    # TODO: Resource (as an example) is both for learning and for assignments
    def is_learning(self):
        return self in {
            ResourceType.RESOURCE,
            ResourceType.FOLDER,
            ResourceType.PAGE,
            ResourceType.URL
        }

    def is_assignment(self):
        return self in {
            ResourceType.ASSIGNMENT,
            ResourceType.QUIZ
        }

@dataclass
class Resource:
    Id: int
    Type: ResourceType
    InternalId: Tuple[int, int] or None
    Name: str
    DependencyId: int or None


@dataclass
class Topic:
    Title: str
    Description: str
    Resources: list[Resource]

@dataclass
class Course:
    Id: int
    CourseNumber: int
    Title: str
    Topics: list[Topic]


class Scraper:
    base_url: str = "https://moodle.bbbaden.ch"
    user_agent: str = "MoodleDownloader/0.1-dev (l.mirandagomes.inf25@stud.bbbaden.ch)"

    def __init__(self, login: Login, session: rq.Session):
        self.session = session
        self.session.headers["User-Agent"] = self.user_agent
        self.login = login
        if self.login.LoginCookies is not None:
            self.session.cookies.update(self.login.LoginCookies)

    def get_login(self) -> None:
        login_index_page = self.session.get(f"{self.base_url}/login/index.php")
        login_soup = BeautifulSoup(login_index_page.content, "html.parser")
        login_token = login_soup.find("input", attrs={"name": "logintoken"}).attrs["value"]
        self.session.post(f"{self.base_url}/login/index.php",
                          data={"anchor": "", "logintoken": login_token, "username": self.login.Username,
                                          "password": self.login.Password})
        self.login.LoginToken = login_token
        self.login.LoginCookies = self.session.cookies.get_dict()
        return

    def _get_course(self, course_id: int) -> BeautifulSoup:
        course_page = self.session.get(f"{self.base_url}/course/view.php?id={course_id}") # TODO: Check for 404
        course_soup = BeautifulSoup(course_page.content, "html.parser")
        return course_soup

    @staticmethod
    def _detect_resource_type(li) -> ResourceType:
        for cls in li.get("class", []):
            if cls.startswith("modtype_"):
                return ResourceType(cls.replace("modtype_", "")) or ResourceType.UNKNOWN
        return ResourceType.UNKNOWN

    def _get_resource(self, resource_item) -> Resource:
        resource_id = int(resource_item.attrs["data-id"])
        resource_type = self._detect_resource_type(resource_item)
        resource_name = resource_item.div.attrs["data-activityname"]
        resource_dependency = None
        if resource_item.find("div", class_="availabilityinfo") is not None:
            resource_dependency = int(resource_item.find(attrs={"data-cm-name-for": True})["data-cm-name-for"])
        return Resource(resource_id, resource_type, None, resource_name, resource_dependency)

    def _get_topic(self, topic_element) -> Topic | None:
        topic_title = topic_element.find("h3", attrs={"data-for": "section_title"}).get_text(" ", strip=True)
        try:
            topic_description = topic_element.find("div", class_="summarytext").get_text(" ", strip=True)
        except AttributeError:
            print(f"Topic {topic_title}/{topic_element.attrs["id"]} seems to not have a description, skipping.")
            return None
        current_topic = Topic(topic_title, topic_description, [])
        for resource_item in topic_element.find("ul").find_all("li"):
            resource = self._get_resource(resource_item)
            match resource.Type.name: # PLACEHOLDER
                case _:
                    pass
            current_topic.Resources.append(resource)
        return current_topic


    def create_dataclass(self, course_id) -> Course:
        course_soup = self._get_course(course_id)
        full_course_title = course_soup.find("div", class_="page-header-headings").h1.get_text()
        split_course_title = full_course_title.split(":")
        course_data = Course(course_id, int(split_course_title[0].split(" ")[1]), split_course_title[1][1:], [])

        for topic in course_soup.find_all("li", class_="section"):
            current_topic = self._get_topic(topic)
            course_data.Topics.append(current_topic)
        return course_data