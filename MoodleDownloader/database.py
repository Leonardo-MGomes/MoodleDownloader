import sqlite3
from typing import List

from .models import Course, Topic, Resource, ResourceType


class MoodleDatabase:
    def __init__(self, filename: str = "MoodleData.sqlite") -> None:
        self.filename = filename
        self.connection = sqlite3.connect(self.filename)
        # https://stackoverflow.com/questions/29420910/how-do-i-enforce-foreign-keys
        self.connection.execute("PRAGMA foreign_keys = 1")
        self.cursor = self.connection.cursor()
        self._create_table_if_not_exist()

    def _create_table_if_not_exist(self) -> None:
        self.cursor.executescript( # TODO: Resource(type) into it's own table
            """
            CREATE TABLE IF NOT EXISTS Course (
            moodle_id INTEGER NOT NULL PRIMARY KEY UNIQUE,
            course_number INTEGER NOT NULL,
            title TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS Topic (
            id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE,
            course_id INTEGER NOT NULL REFERENCES Course(moodle_id),
            title TEXT NOT NULL,
            description TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS Resource (
            moodle_id INTEGER NOT NULL PRIMARY KEY UNIQUE,
            topic_id INTEGER NOT NULL REFERENCES Topic(id),
            name TEXT NOT NUlL,
            type TEXT NOT NULL, 
            dependency_id INTEGER REFERENCES Resource(moodle_id)
            );
            """
        )
        return

    def add_course(self, course: Course) -> None:
        course_data = (course.Id, course.CourseNumber, course.Title)
        self.cursor.execute("INSERT OR IGNORE INTO Course VALUES (?, ?, ?)", course_data)
        self.connection.commit()

        topic_data = []
        for topic in course.Topics:
            if topic is None: continue
            topic_data.append((None, course.Id, topic.Title, topic.Description))
        self.cursor.executemany("INSERT OR IGNORE INTO Topic VALUES (?, ?, ?, ?)", topic_data)
        self.connection.commit()

        resource_data = []
        for topic in course.Topics:
            if topic is None: continue
            topic_id = self.cursor.execute("SELECT id FROM Topic WHERE title = ? AND description = ?", (topic.Title, topic.Description)).fetchone()[0]
            for resource in topic.Resources:
                if resource is None: continue
                resource_data.append((resource.Id, topic_id, resource.Name, resource.Type.value, resource.DependencyId))
        self.cursor.executemany("INSERT OR IGNORE INTO Resource VALUES (?, ?, ?, ?, ?)", resource_data)
        self.connection.commit()
        return

    def from_database_to_object(self) -> List[Course]:
        courses_db: List[tuple] = self.cursor.execute("SELECT * FROM Course").fetchall()

        courses = []

        for course in courses_db:
            topics_db: List[tuple] = self.cursor.execute("SELECT * FROM Topic WHERE course_id = ?", (str(course[0]),)).fetchall()
            topics = []
            for topic in topics_db:
                resources_db: List[tuple] = self.cursor.execute("SELECT * FROM Resource WHERE topic_id = ?", (str(topic[0]),)).fetchall()
                resources = []
                for resource in resources_db:
                    resources.append(Resource(resource[0], resource[3], None, resource[2], resource[4]))
                topics.append(Topic(topic[2], topic[3], resources.copy()))
            courses.append(Course(course[0], course[1], course[2], topics.copy()))

        return courses
