import json
from pathlib import Path
from datetime import datetime

from py_moodle import MoodleSession
from py_moodle.user import list_course_users


class MoodleCourseUserManager:
    def __init__(self, courses_file=Path("courses.json"), courses_dir=Path("./course_users"), debug=False):
        self.__courses_file = courses_file
        self.__courses_dir = courses_dir
        self.__debug = debug
        self.__moodle_session = MoodleSession.get()

    @staticmethod
    def _save_json(file_path: Path, data) -> None:
        """Save data as pretty-printed JSON."""
        file_path.parent.mkdir(parents=True, exist_ok=True)
        with file_path.open("w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    @staticmethod
    def _load_json(file_path: Path):
        """Load JSON from a file."""
        with file_path.open("r", encoding="utf-8") as f:
            return json.load(f)

    @staticmethod
    def _get_file_modification_time(file_path: Path) -> datetime:
        """
        Return the last modification datetime of a file.

        Uses Windows-function -> NO UNIX SUPPORTED!
        """
        return datetime.fromtimestamp(file_path.stat().st_mtime)

    def _debug_print(self, *args, **kwargs):
        if self.__debug:
            print(*args, **kwargs)

    def load_cached_courses(self) -> list[dict]:
        """
        Load courses from local json-file.

        TODO: handling if courses.json is not cached locally
        """
        self._debug_print(
            f"Loading all courses from {self.__courses_file}. "
            f"Last modified: {self._get_file_modification_time(self.__courses_file)}")
        return self._load_json(self.__courses_file)

    def load_cached_course_users(self) -> dict[int, list]:
        """Load all cached course users from local directory."""
        cached_course_users = {}
        if not self.__courses_dir.exists():
            return cached_course_users

        for file in self.__courses_dir.glob("*.json"):
            if file.is_file():
                self._debug_print(
                    f"Loading course from {file.name}. "
                    f"Last modified: {self._get_file_modification_time(file)}")
                cached_course_users[int(file.stem)] = self._load_json(file)
        return cached_course_users

    def _convert_courses_list_to_dict(self, all_courses_list: list[dict]) -> dict[int, dict]:
        """"
        Converts the provided courses-list into a dictionary with the id as key
        """

        return {int(course['id']): course for course in all_courses_list}

    def load_or_download_course_users(self) -> dict[int, list]:
        """
        Load course user data from cache if available,
        otherwise fetch from Moodle and save locally.

        TODO: download courses.json if not cached locally.
        """
        all_courses = self.load_cached_courses()
        cached_course_users = self.load_cached_course_users()

        self._debug_print(f"Number of all courses: {len(all_courses)}")
        self._debug_print(f"Number of cached courses: {len(cached_course_users)}")

        for course in all_courses:
            course_id = course['id']

            if course_id in cached_course_users:
                continue

            self._debug_print(f"Downloading course {course_id}...")
            users = list_course_users(
                session=self.__moodle_session.session,
                base_url=self.__moodle_session.settings.url,
                token=self.__moodle_session.token,
                course_id=course_id,
            )
            cached_course_users[course_id] = users
            self._save_json(self.__courses_dir / f"{course_id}.json", users)

        return cached_course_users
