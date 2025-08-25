import json
import logging
from pathlib import Path
from datetime import datetime

from py_moodle import MoodleSession
from py_moodle.category import list_categories
from py_moodle.course import list_courses
from py_moodle.user import list_course_users


class CourseAnalyzer:
    """
    Manages moodle courses and enlisted user for each course.

    ATTENTION: stores sensitive data locally in JSON files!
    """
    def __init__(self, courses_file=Path("courses.json"), courses_dir=Path("./course_users"), debug=False):
        self.__moodle_session = MoodleSession.get()
        self.__logger = logging.getLogger(self.__class__.__name__)
        logging.basicConfig(level=logging.DEBUG if debug else logging.INFO)

        self.all_courses = self.__fetch_courses_with_cache(courses_file)
        self.all_course_users = self.__fetch_course_users_with_cache(courses_dir)

    def get_all_courses(self) -> dict[str, dict]:
        return self.all_courses

    def get_all_course_users(self) -> dict[str, list]:
        return self.all_course_users

    @staticmethod
    def _save_json(file_path: Path, data) -> None:
        file_path.parent.mkdir(parents=True, exist_ok=True)
        with file_path.open("w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    @staticmethod
    def _load_json(file_path: Path):
        with file_path.open("r", encoding="utf-8") as f:
            return json.load(f)

    @staticmethod
    def _get_file_modification_time(file_path: Path) -> datetime:
        return datetime.fromtimestamp(file_path.stat().st_mtime)

    def __fetch_courses_with_cache(self, file_path: Path) -> dict[str, dict]:
        """
        Load overview of all courses from cache if available,
        otherwise fetch from Moodle and save locally.

        Requires self.__moodle_session and self.__debug
        """
        if not file_path.exists():
            self.__logger.info("Downloading overview of all courses...")
            all_courses_list = list_courses(
                session=self.__moodle_session.session,
                base_url=self.__moodle_session.settings.url,
                token=self.__moodle_session.token
            )
            all_courses_dict = {course['id']: course for course in all_courses_list}
            self._save_json(file_path, all_courses_dict)
        else:
            self.__logger.info(
                f"Loading all courses from {file_path}. "
                f"Last modified: {self._get_file_modification_time(file_path)}")
            all_courses_dict = self._load_json(file_path)

        return all_courses_dict

    def __fetch_course_users_with_cache(self, directory_path: Path) -> dict[str, list]:
        """
        Load course user data from cache if available,
        otherwise fetch from Moodle and save locally.

        Requires self.all_courses, self.__moodle_session and self.__debug
        """

        all_course_users = {}
        if directory_path.exists():
            for file in directory_path.glob("*.json"):
                if file.is_file():
                    self.__logger.debug(
                        f"Loading course from {file.name}. "
                        f"Last modified: {self._get_file_modification_time(file)}")
                    all_course_users[file.stem] = self._load_json(file)

        self.__logger.info(f"Number of all courses: {len(self.all_courses)}")
        self.__logger.info(f"Number of cached courses: {len(all_course_users)}")

        """ Download missing course_users """
        for course_id, course in self.all_courses.items():
            if course_id in all_course_users:
                continue

            self.__logger.debug(f"Downloading course {course_id}...")
            users = list_course_users(
                session=self.__moodle_session.session,
                base_url=self.__moodle_session.settings.url,
                token=self.__moodle_session.token,
                course_id=course_id,
            )
            all_course_users[course_id] = users
            self._save_json(directory_path / f"{course_id}.json", users)

        return all_course_users

    @staticmethod
    def __extract_supercategory(path: str) -> int | None:
        """
        :param path: The category path string, expected in the format
                        "supercategory_id/subcategory_id/...".
        :return: The integer ID of the supercategory if successfully
                    extracted; otherwise, None.
        """
        if not isinstance(path, str):
            logging.warning(f"Path is not a string: {path}")
            return None
        parts = path.split("/")
        if not parts:
            logging.warning(f"Path could not be split: {path}")
            return None
        if not parts[1].isdigit():
            logging.warning(f"Supercategory is not a number: {path}")
            return None
        return int(parts[1])

    def __fetch_supercategory_lookup(self) -> dict[str, dict]:
        """
        Build a lookup dictionary of all Moodle categories with their names
        and supercategory IDs.

        This method retrieves all categories via the `py_moodle.category.list_categories` function
        and constructs a dictionary

        :return:    Dictionary where each key is a category ID,
                    and the value is another dictionary containing the `name` and `supercategory` ID.
        :raises RuntimeError: If a supercategory cannot be determined from the path string
        """
        all_categories = list_categories(
            session=self.__moodle_session.session,
            base_url=self.__moodle_session.settings.url,
            token=self.__moodle_session.token
        )

        category_lookup = {}

        for category in all_categories:
            category_id = category['id']
            category_lookup[category_id] = {'name': category['name']}
            if category['parent'] == 0:
                category_lookup[category_id]['supercategory'] = category_id
            else:
                supercategory_id = CourseAnalyzer.__extract_supercategory(category['path'])
                if supercategory_id is None:
                    raise RuntimeError(f"Supercategory could not be found: {category['path']}")
                category_lookup[category_id]['supercategory'] = supercategory_id

        return category_lookup
