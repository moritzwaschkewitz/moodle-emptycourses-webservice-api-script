import csv

from MoodleCourseUserManager import MoodleCourseUserManager

from datetime import datetime
from pprint import pprint
from pathlib import Path


def find_empty_courses(course_users: dict[str, list], all_courses: dict[str, dict]) -> dict[str, dict]:
    return {
        course_id: all_courses[course_id]
        for course_id, users in course_users.items()
        if len(users) == 0 and course_id in all_courses
    }


#for empty courses, since these are the only timestamps available
def sort_courses_by_timemodified(courses: dict[str, dict]) -> list[dict]:
    return sorted(courses.values(), key=lambda course: course['timemodified'])


# TODO: sort all (non_empty) courses by last user access

def add_readable_dates_to_courses(courses: list[dict]) -> None:
    """ adds human-readable timestamps to list of courses """

    for course in courses:
        for key in ('timemodified', 'timecreated', 'startdate'):
            value = course.get(key)
            if isinstance(value, int):
                course[f"{key}_human"] = datetime.fromtimestamp(course[key]).strftime('%Y-%m-%d %H:%M:%S')


def add_url_to_courses(courses: list[dict], base_url: str = "https://moodle.hsnr.de/course/view.php?id=") -> None:
    for course in courses:
        course["url"] = f"{base_url}{course['id']}"


def export_courses_to_csv(courses: list[dict], file_path: Path, fieldnames: list[str]) -> None:
    with open(file_path, 'w', newline='', encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames, extrasaction='ignore')
        writer.writeheader()
        writer.writerows(courses)


# TODO exclude certain categories (Sprachenzentrum & Weiterbildung)
def collect_categoryids(courses: dict[str, dict]) -> set:
    category_ids = set()
    for course in courses.values():
        category_ids.add(course['categoryid'])
    return category_ids


def main():
    manager = MoodleCourseUserManager(debug=True)
    course_users = manager.all_course_users
    all_courses = manager.all_courses

    """
    PE2_TUT_ID = '10979'
    pe2_tut_course = all_courses[PE2_TUT_ID]
    add_readable_dates_to_courses([pe2_tut_course])
    pprint(pe2_tut_course)
    print(f"Eingeschriebene Nutzer/innen in PE2-TUT: {len(course_users[PE2_TUT_ID])}")
    """

    empty_courses = find_empty_courses(course_users, all_courses)
    # pprint(empty_courses)

    sorted_empty_courses = sort_courses_by_timemodified(empty_courses)
    add_readable_dates_to_courses(sorted_empty_courses)
    add_url_to_courses(sorted_empty_courses)
    pprint(sorted_empty_courses[-1])

    export_courses_to_csv(sorted_empty_courses, 'empty.csv', fieldnames=[
        'id', 'fullname', 'shortname',
        'startdate', 'startdate_human',
        'timecreated', 'timecreated_human',
        'timemodified', 'timemodified_human',
        'url'])

    print(f"Anzahl leerer Kurse: {len(sorted_empty_courses)}")


if __name__ == "__main__":
    main()
