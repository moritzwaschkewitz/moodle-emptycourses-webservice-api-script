import csv
import logging
import sys
from pathlib import Path
from datetime import datetime

from py_moodle import MoodleSession
from py_moodle.category import list_categories
from py_moodle.course import list_courses
from py_moodle.user import list_course_users


class CourseAnalyzer:
    """

    """
    def __init__(self, courses_file=Path("courses.json"), courses_dir=Path("./course_users"), logging_level=logging.INFO):
        self.__moodle_session = MoodleSession.get()
        self.__logger = logging.getLogger(self.__class__.__name__)
        logging.basicConfig(level=logging_level)

    def find_and_export_empty_courses_to_csv(self,
                                             excluded_supercategory_ids=None,
                                             csv_directory_path: Path = Path.cwd()) -> None:
        """

        :param excluded_supercategory_ids: List of supercatergory IDs which should be excluded
        :param csv_directory_path: Path to the directory where CSV files should be saved
        :return:
        """
        if excluded_supercategory_ids is None:
            excluded_supercategory_ids = []

        self.__logger.info(f"Fetching category_lookup...")
        category_lookup = self.__fetch_supercategory_lookup()

        self.__logger.info(f"Fetching courses_overview...")
        courses_overview = self.__fetch_courses_overview()

        empty_courses_per_supercategory = self.__collect_empty_courses_by_supercategory(category_lookup, courses_overview, excluded_supercategory_ids)
        self.__export_empty_courses_to_csv(csv_directory_path, empty_courses_per_supercategory)

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

    def __fetch_supercategory_lookup(self) -> dict[int, dict]:
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

    def __fetch_courses_overview(self) -> dict[int, dict]:
        """
            Retrieve an overview of all available Moodle courses and prepare
            relevant metadata.

            Each course is stored with its course-ID as the key and relevant metadata in an inner dictionary

            Details of the inner dictionaries:

            - **fullname** (str): Full name of the course.
            - **shortname** (str): Short name of the course.
            - **categoryid** (int): ID of the associated category.
            - **latest_key** (str): Key of the most recent timestamp.
            - **latest_timestamp_unix** (int): Most recent timestamp in Unix time.
            - **latest_timestamp_human** (str): Most recent timestamp in YYYY-MM-DD HH:MM:SS.

            :returns: Dictionary mapping course IDs to metadata.
            """
        all_courses_list = list_courses(
            session=self.__moodle_session.session,
            base_url=self.__moodle_session.settings.url,
            token=self.__moodle_session.token
        )
        courses_overview = {}
        for course in all_courses_list:
            timestamp_keys_to_check = ['timecreated', 'timemodified', 'startdate']
            filtered_timestamp_dict = {k: course[k] for k in timestamp_keys_to_check}
            latest_category, latest_timestamp = max(filtered_timestamp_dict.items(), key=lambda x: x[1])
            courses_overview[course['id']] = {
                'fullname': course['fullname'],
                'shortname': course['shortname'],
                'categoryid': course['categoryid'],
                'latest_key': latest_category,  # TODO: may be removed
                'latest_timestamp_unix': latest_timestamp,
                'latest_timestamp_human': datetime.fromtimestamp(latest_timestamp).strftime('%Y-%m-%d %H:%M:%S')
            }

        return courses_overview

    def __collect_empty_courses_by_supercategory(self,
                                                 category_lookup: dict[int, dict],
                                                 courses_overview: dict[int, dict],
                                                 excluded_supercategory_ids: list[int]) \
            -> dict[str, list[dict]]:
        """
            Collects all courses with no enrolled users, grouped by their faculty/supercategory.

            Iterates through the provided course overview, skips excluded courses or categories,
            queries the user list for each course, and builds a dictionary of empty courses organized
            by faculty. Progress is printed to stdout during execution.

            Each faculty name provides the string key for the outer dictionary with a list of empty courses as the value.
            The list of empty courses gets sorted by the last timestamp and contains the following course-metadate in a dictionary:

            - **id** (int): course-ID.
            - **fullname** (str): Full name of the course.
            - **shortname** (str): Short name of the course.
            - **categoryid** (int): ID of the associated category.
            - **latest_key** (str): Key of the most recent timestamp.
            - **latest_timestamp_unix** (int): Most recent timestamp in Unix time.
            - **latest_timestamp_human** (str): Most recent timestamp in YYYY-MM-DD HH:MM:SS.
            - **category** (str): name of the direct parent category.
            - **url** (str): moodle-URL.

            :returns: Dictionary mapping faculty names to a list of empty courses.
            :param category_lookup: result of self.__fetch_supercategory_lookup.
            :param courses_overview: result of self.__fetch_courses_overview.
            :param excluded_supercategory_ids: list of supercategory IDs to exclude.
        """
        number_of_all_courses = len(courses_overview)
        empty_courses_per_supercategory = {}
        empty_courses_counter = 0

        for i, (course_id, course_dict) in enumerate(courses_overview.items(), 1):
            category_id = course_dict['categoryid']
            name = course_dict['fullname']
            if course_id == 1:
                self.__logger.info(f"Skipping {course_id}: {name}")
                continue
            supercategory_id = category_lookup[category_id]['supercategory']
            if supercategory_id in excluded_supercategory_ids:
                continue

            course_users = list_course_users(
                session=self.__moodle_session.session,
                base_url=self.__moodle_session.settings.url,
                token=self.__moodle_session.token,
                course_id=course_id,
            )
            if len(course_users) > 0:
                continue

            supercategory_name = category_lookup[supercategory_id]['name']

            if supercategory_name not in empty_courses_per_supercategory:
                empty_courses_per_supercategory[supercategory_name] = []

            empty_courses_per_supercategory[supercategory_name].append({
                'id': course_id,
                'category': category_lookup[category_id]['name'],
                'url': f"https://moodle.hsnr.de/course/view.php?id={course_id}",
                **course_dict
            })

            '''Progress Bar'''
            bar_length = 50
            filled_length = int(bar_length * i / number_of_all_courses)
            bar = '█' * filled_length + '-' * (bar_length - filled_length)
            sys.stdout.write(f"\rProgress: |{bar}| {i}/{number_of_all_courses}"
                             f"\tFound empty courses: {empty_courses_counter}")
            sys.stdout.flush()

        self.__logger.info(f"Finished {number_of_all_courses} courses.")  # TODO better description

        for empty_courses_list in empty_courses_per_supercategory.values():
            empty_courses_list.sort(key=lambda x: x['latest_timestamp_unix'])

        return empty_courses_per_supercategory

    @staticmethod
    def __export_empty_courses_to_csv(csv_directory_path: Path, empty_courses_per_supercategory: dict[str, list[dict]]) -> None:
        for supercategory_name, empty_courses_list in empty_courses_per_supercategory.items():
            fieldnames = list(empty_courses_list[0].keys())
            file_path = csv_directory_path / f"{supercategory_name}.csv"
            with open(file_path, 'w', newline='', encoding="utf-8") as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames, extrasaction='ignore')
                writer.writeheader()
                writer.writerows(empty_courses_list)
