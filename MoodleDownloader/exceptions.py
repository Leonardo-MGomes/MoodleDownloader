class MoodleException(Exception):
    pass


class MoodleAuthError(MoodleException):
    pass


class MoodleNoCredentialsError(MoodleAuthError):
    pass


class MoodleNotFoundError(MoodleException):
    pass


class MoodleCourseNotFound(MoodleNotFoundError):
    pass


class MoodleResourceNotFound(MoodleNotFoundError):
    pass


class MoodleFileNotFound(MoodleNotFoundError):
    pass

