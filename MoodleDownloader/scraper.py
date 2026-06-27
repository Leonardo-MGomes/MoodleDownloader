from typing import Optional

import requests
from bs4 import BeautifulSoup

from .auth import MoodleAuth
from .config import DEFAULT_CONFIG, AppConfig
from .exceptions import MoodleCourseNotFound, MoodleException
from .models import Course, Topic, Resource, ResourceType


class Scraper:
    # auth is optional and only here for automatic logins
    def __init__(self, session: requests.Session, auth: Optional[MoodleAuth] = None, config: Optional[AppConfig] = DEFAULT_CONFIG):
        self.session = session
        self.config = config
        self.auth = auth
        self.base_url = self.config.BASE_URL

    def _get_course(self, course_id: int) -> BeautifulSoup:
        course_page = self.session.get(f"{self.base_url}/course/view.php?id={course_id}", allow_redirects=False)
        if course_page.status_code == 404:
            raise MoodleCourseNotFound(f"Course with the id {course_id} was not found")
        course_soup = BeautifulSoup(course_page.content, "html.parser")
        return course_soup

    @staticmethod
    def _detect_resource_type(li) -> ResourceType:
        for cls in li.get("class", []):
            if cls.startswith("modtype_"):
                try:
                    return ResourceType(cls.replace("modtype_", ""))
                except ValueError:
                    # INFO: This needs to be made into a logger.warning or something
                    #print(f"Type {cls.replace("modtype_", "")} not recognized")
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
        topic_id = topic_element.get("data-id")
        try:
            topic_description = topic_element.find("div", class_="summarytext").get_text(" ", strip=True)
        except AttributeError:
            # INFO: This needs to be made into a logger.warning or something
            #print(f"Topic {topic_title}/{topic_element.attrs["id"]} seems to not have a description, skipping.")
            return None
        current_topic = Topic(topic_id, topic_title, topic_description, [])
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
        try:
            header_div = course_soup.find("div", class_="page-header-headings")
            if not header_div or not header_div.h1:
                err_msg = course_soup.find("div", class_="errormessage") or course_soup.find("div", class_="errorbox")
                if err_msg:
                    raise MoodleException(f"Moodle error: {err_msg.get_text(strip=True)}")
                raise MoodleCourseNotFound(f"Course with the id {course_id} could not be found or page layout is unexpected")
            full_course_title = header_div.h1.get_text()
            split_course_title = full_course_title.split(":")
            course_number = int(split_course_title[0].split(" ")[1])
            course_title = split_course_title[1][1:]
        except (AttributeError, IndexError, ValueError) as e:
            err_msg = course_soup.find("div", class_="errormessage") or course_soup.find("div", class_="errorbox")
            if err_msg:
                raise MoodleException(f"Moodle error: {err_msg.get_text(strip=True)}") from e
            raise MoodleCourseNotFound(f"Course with the id {course_id} could not be parsed: {e}") from e

        course_data = Course(course_id, course_number, course_title, [])

        for topic in course_soup.find_all("li", class_="section"):
            current_topic = self._get_topic(topic)
            course_data.Topics.append(current_topic)
        return course_data
