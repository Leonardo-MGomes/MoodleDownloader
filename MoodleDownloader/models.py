import enum
from dataclasses import dataclass
from typing import Tuple, Optional


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
    H5P_ACTIVITY = "h5pactivity"
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
    InternalId: Optional[Tuple[int, int]]
    Name: str
    DependencyId: Optional[int]


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
