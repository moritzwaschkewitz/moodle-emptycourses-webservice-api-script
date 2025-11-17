import csv
import logging
import os
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional

from exporters import CsvExporter
from moodle_client import MoodleClient


class CourseAnalyzer:
    """
    Analyzes Moodle courses and exports empty ones grouped by supercategory.
    """
    def __init__(self, client: Optional[MoodleClient] = None, logger: Optional[logging.Logger] = None):
        self.__client = client or MoodleClient()
        if logger:
            self.__logger = logger
        else:
            self.__logger = logging.getLogger(self.__class__.__name__)
            logging.basicConfig(level=logging.INFO)

    def __extract_supercategory(self, path: str) -> int | None:
        """
        :param path: The category path string, expected in the format
                        "supercategory_id/subcategory_id/...".
        :return: The integer ID of the supercategory if successfully
                    extracted; otherwise, None.
        """
        if not isinstance(path, str):
            self.__logger.warning(f"Path is not a string: {path}")
            return None
        parts = path.split("/")
        if len(parts) < 2 or not parts[1].isdigit():
            self.__logger.warning(f"Supercategory could not be extracted: {path}")
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
        all_categories = self.__client.categories()
        category_lookup: dict[int, dict] = {}

        for category in all_categories:
            category_id = category['id']
            category_lookup[category_id] = {'name': category['name']}
            if category['parent'] == 0:
                category_lookup[category_id]['supercategory'] = category_id
            else:
                supercategory_id = self.__extract_supercategory(category['path'])
                if supercategory_id is None:
                    raise RuntimeError(f"Supercategory could not be found: {category['path']}")
                category_lookup[category_id]['supercategory'] = supercategory_id

        return category_lookup

    def __fetch_courses_overview(self) -> dict[int, dict]:
        """
            Retrieve an overview of all available Moodle courses and prepare
            relevant metadata.

            This method controls which metadata is kept from the webservice request.

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
        all_courses_list = self.__client.courses()
        courses_overview: dict[int, dict] = {}
        for course in all_courses_list:
            timestamp_keys_to_check = ['timecreated', 'timemodified', 'startdate']
            filtered_timestamp_dict = {k: course[k] for k in timestamp_keys_to_check}
            latest_category, latest_timestamp = max(filtered_timestamp_dict.items(), key=lambda x: x[1])
            courses_overview[course['id']] = {
                'fullname': course['fullname'],
                'shortname': course['shortname'],
                'categoryid': course['categoryid'],
                'latest_timestamp_unix': latest_timestamp,
                'latest_timestamp_human': datetime.fromtimestamp(latest_timestamp).strftime('%Y-%m-%d %H:%M:%S')
            }

        return courses_overview

    def __collect_empty_courses_by_supercategory(
            self,
            category_lookup: dict[int, dict],
            courses_overview: dict[int, dict],
            excluded_supercategory_ids: list[int],
            min_users: int = 0,
            show_progress: bool = True,
            ) -> dict[str, list[dict]]:
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
            :param min_users: minimum number of users to include a course as "empty". Default is 0.
            :param show_progress: show progress bar during execution. Default is True.
        """
        number_of_all_courses = len(courses_overview)
        empty_courses_per_supercategory = {}
        empty_courses_counter = 0

        for i, (course_id, course_dict) in enumerate(courses_overview.items(), 1):
            category_id = course_dict['categoryid']
            name = course_dict['fullname']

            # TODO: progress bar only gets updated once an empty course is found, since the loop is continued beforehand

            if course_id == 1:
                self.__logger.debug(f"Skipping front page id={course_id}: {name}")
                continue
            supercategory_id = category_lookup[category_id]['supercategory']
            if supercategory_id in excluded_supercategory_ids:
                continue

            course_users = self.__client.course_users(course_id)
            if len(course_users) > min_users:
                continue

            empty_courses_counter += 1
            supercategory_name = category_lookup[supercategory_id]['name']

            if supercategory_name not in empty_courses_per_supercategory:
                empty_courses_per_supercategory[supercategory_name] = []

            empty_courses_per_supercategory[supercategory_name].append({
                'id': course_id,
                'category': category_lookup[category_id]['name'],
                'url': f"{os.environ['MOODLE_LOCAL_URL']}/course/view.php?id={course_id}",
                **course_dict
            })

            if show_progress:
                bar_length = 50
                filled_length = int(bar_length * i / number_of_all_courses)
                bar = '█' * filled_length + '-' * (bar_length - filled_length)
                sys.stdout.write(f"\rProgress: |{bar}| {i}/{number_of_all_courses}"
                                 f"\tFound empty courses: {empty_courses_counter}")
                sys.stdout.flush()

        for empty_courses_list in empty_courses_per_supercategory.values():
            empty_courses_list.sort(key=lambda x: x['latest_timestamp_unix'])

        self.__logger.info(f"Finished processing {number_of_all_courses} courses.\n"
                           f"Found {empty_courses_counter} empty courses in {len(empty_courses_per_supercategory)} supercategories.")

        return empty_courses_per_supercategory

    def find_and_export_empty_courses(
        self,
        excluded_supercategory_ids: Optional[list[int]] = None,
        csv_directory_path: Path = Path.cwd(),
        exporter: Optional[CsvExporter] = CsvExporter(),
        min_users: int = 0,
        show_progress: bool = True
    ) -> None:
        excluded_supercategory_ids = excluded_supercategory_ids or []

        self.__logger.info("Fetching categories...")
        category_lookup = self.__fetch_supercategory_lookup()

        self.__logger.info("Fetching courses...")
        courses_overview = self.__fetch_courses_overview()

        empty_courses_per_supercategory = self.__collect_empty_courses_by_supercategory(
            category_lookup,
            courses_overview,
            excluded_supercategory_ids,
            min_users,
            show_progress,
        )

        exporter.export(csv_directory_path, empty_courses_per_supercategory)

    @staticmethod
    def __export_empty_courses_to_csv(csv_directory_path: Path, empty_courses_per_supercategory: dict[str, list[dict]]) -> None:
        if not csv_directory_path.exists():
            csv_directory_path.mkdir(parents=True, exist_ok=True)
        for supercategory_name, empty_courses_list in empty_courses_per_supercategory.items():
            fieldnames = list(empty_courses_list[0].keys())
            file_path = csv_directory_path / f"{supercategory_name}.csv"
            with open(file_path, 'w', newline='', encoding="utf-8") as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames, extrasaction='ignore')
                writer.writeheader()
                writer.writerows(empty_courses_list)

    def find_and_export_empty_courses_to_csv(self,
                                             excluded_supercategory_ids=None,
                                             csv_directory_path: Path = Path.cwd() / 'csv_exports') -> None:
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
