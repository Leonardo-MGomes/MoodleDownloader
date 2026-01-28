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
        topics_db: List[tuple] = self.cursor.execute("SELECT * FROM Topic ORDER BY id").fetchall()
        resources_db: List[tuple] = self.cursor.execute("SELECT * FROM Resource ORDER BY topic_id").fetchall()
        courses_db: List[tuple] = self.cursor.execute("SELECT * FROM Course").fetchall()

        last_id = 1
        resources = []
        courses_and_topics = {}
        courses = []
        for resource in resources_db:
            if last_id != resource[1]:
                courses_and_topics.setdefault(topics_db[last_id][1], []).append(Topic(topics_db[last_id][2], topics_db[last_id][3], resources.copy()))
                resources.clear()
                last_id = resource[1]

            resources.append(Resource(resource[0], resource[3], None, resource[2], resource[4]))

        for course_moodle_id, topics in courses_and_topics.items():
            current_course = None
            for idx, course in enumerate(courses_db):
                if course[0] == course_moodle_id:
                    current_course = courses_db.pop(idx)
            courses.append(Course(course_moodle_id, current_course[1], current_course[2], topics))
        return courses
