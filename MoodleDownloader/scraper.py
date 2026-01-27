from typing import Optional

import requests
from bs4 import BeautifulSoup

from .auth import MoodleAuth
from .config import DEFAULT_CONFIG, AppConfig
from .models import Course, Topic, Resource, ResourceType


class Scraper:
    # auth is optional and only here for automatic logins
    def __init__(self, session: requests.Session, auth: Optional[MoodleAuth] = None, config: Optional[AppConfig] = DEFAULT_CONFIG):
        self.session = session
        self.config = config
        self.auth = auth
        self.base_url = self.config.BASE_URL

    def _get_course(self, course_id: int) -> BeautifulSoup:
        course_page = self.session.get(f"{self.base_url}/course/view.php?id={course_id}")  # TODO: Check for 404
        course_soup = BeautifulSoup(course_page.content, "html.parser")
        return course_soup

    @staticmethod
    def _detect_resource_type(li) -> ResourceType:
        for cls in li.get("class", []):
            if cls.startswith("modtype_"):
                try:
                    return ResourceType(cls.replace("modtype_", ""))
                except ValueError:
                    print(f"Type {cls.replace("modtype_", "")} not recognized")
                    return ResourceType.UNKNOWN
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
            match resource.Type.name:  # PLACEHOLDER
                case _:
                    pass
            current_topic.Resources.append(resource)
        return current_topic

    def create_dataclass(self, course_id) -> Course:
        if not self.auth.is_session_valid() and not self.auth.credentials is None:
            self.auth.login()
        course_soup = self._get_course(course_id)
        full_course_title = course_soup.find("div", class_="page-header-headings").h1.get_text()
        split_course_title = full_course_title.split(":")
        course_data = Course(course_id, int(split_course_title[0].split(" ")[1]), split_course_title[1][1:], [])

        for topic in course_soup.find_all("li", class_="section"):
            current_topic = self._get_topic(topic)
            course_data.Topics.append(current_topic)
        return course_data
