import json
from pathlib import Path
from datetime import datetime

from py_moodle import MoodleSession
from py_moodle.course import list_courses
from py_moodle.user import list_course_users


class MoodleCourseUserManager:
    def __init__(self, courses_file=Path("courses.json"), courses_dir=Path("./course_users"), debug=False):
        self.__moodle_session = MoodleSession.get()
        self.__debug = debug

        self.all_courses = self.__load_or_download_courses(courses_file)
        self.all_course_users = self.__load_or_download_course_users(courses_dir)

    def get_all_courses(self):
        return self.all_courses

    def get_all_course_users(self):
        return self.all_course_users

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

    def __load_or_download_courses(self, file_path: Path) -> dict[str, dict]:
        """
        Load overview of all courses from cache if available,
        otherwise fetch from Moodle and save locally.

        Requires self.__moodle_session and self.__debug = debug
        """
        if not file_path.exists():
            self._debug_print("Downloading overview of all courses...")
            all_courses_list = list_courses(
                session=self.__moodle_session.session,
                base_url=self.__moodle_session.settings.url,
                token=self.__moodle_session.token
            )
            all_courses_dict = {course['id']: course for course in all_courses_list}
            self._save_json(file_path, all_courses_dict)
        else:
            self._debug_print(
                f"Loading all courses from {file_path}. "
                f"Last modified: {self._get_file_modification_time(file_path)}")
            all_courses_dict = self._load_json(file_path)

        return all_courses_dict

    def __load_or_download_course_users(self, directory_path: Path) -> dict[str, list]:
        """
        Load course user data from cache if available,
        otherwise fetch from Moodle and save locally.

        Requires self.all_courses, self.__moodle_session and self.__debug = debug
        """

        """ Reading cached course_users """
        all_course_users = {}
        if not directory_path.exists():
            return all_course_users

        for file in directory_path.glob("*.json"):
            if file.is_file():
                self._debug_print(
                    f"Loading course from {file.name}. "
                    f"Last modified: {self._get_file_modification_time(file)}")
                all_course_users[file.stem] = self._load_json(file)

        self._debug_print(f"Number of all courses: {len(self.all_courses)}")
        self._debug_print(f"Number of cached courses: {len(all_course_users)}")

        """ Download missing course_users """
        for course_id, course in self.all_courses.items():
            if course_id in all_course_users.keys():
                continue

            self._debug_print(f"Downloading course {course_id}...")
            users = list_course_users(
                session=self.__moodle_session.session,
                base_url=self.__moodle_session.settings.url,
                token=self.__moodle_session.token,
                course_id=course_id,
            )
            all_course_users[course_id] = users
            self._save_json(directory_path / f"{course_id}.json", users)

        return all_course_users
