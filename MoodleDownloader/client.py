import re
from typing import Optional

import requests

from .auth import MoodleApiSession
from .config import AppConfig, DEFAULT_CONFIG
from .models import Course, Topic, Resource, ResourceType


class MoodleClient:
    def __init__(self, session: requests.Session, moodle_session: MoodleApiSession, app_config: Optional[AppConfig] = DEFAULT_CONFIG):
        self.session = session
        self.app_config = app_config
        self.session.headers["User-Agent"] = self.app_config.USER_AGENT
        self.moodle_session = moodle_session
        self.base_url = self.app_config.BASE_URL

    def _call(self, function: str, extra_params: Optional[dict] = None) -> dict:
        params = {
            "wstoken": self.moodle_session.token,
            "wsfunction": function,
            "moodlewsrestformat": "json"
        }
        if extra_params:
            params.update(extra_params)
        return self.session.get(f"{self.base_url}/webservice/rest/server.php", params=params).json()

    def get_course(self, course_id: int):
        course = self._call("core_course_get_courses_by_field", extra_params={"field":"id","value":course_id})["courses"][0]
        course_content = self._call("core_course_get_contents", extra_params={"courseid":course_id})

        course_name = re.search(r"\d{3}:? (.+)", course["fullname"]).group(1)
        course_number = re.search(r"(\d{3})", course["fullname"]).group(1)

        topic_obj_list = []

        for topic in course_content:
            topic_obj = Topic(topic["id"], topic["name"], topic["summary"], [])
            for resource in topic["modules"]:
                resource_type = ResourceType(resource["modname"])
                resource_obj = Resource(resource["id"], resource_type, resource["contextid"], resource["name"], None) # TODO: Dependencies can't be gotten from here, wasn't used much anyways so it's probably fine
                topic_obj.Resources.append(resource_obj)
            topic_obj_list.append(topic_obj)

        course_obj = Course(course["id"], int(course_number), course_name, topic_obj_list)
        return course_obj