from py_moodle import MoodleSession
from py_moodle.category import list_categories
from py_moodle.course import list_courses
from py_moodle.user import list_course_users


class MoodleClient:
    def __init__(self):
        self.session = MoodleSession.get()

    def categories(self) -> list[dict]:
        return list_categories(
            session=self.session.session,
            base_url=self.session.settings.url,
            token=self.session.token,
        )

    def courses(self) -> list[dict]:
        return list_courses(
            session=self.session.session,
            base_url=self.session.settings.url,
            token=self.session.token,
        )

    def course_users(self, course_id: int) -> list[dict]:
        return list_course_users(
            session=self.session.session,
            base_url=self.session.settings.url,
            token=self.session.token,
            course_id=course_id,
        )
