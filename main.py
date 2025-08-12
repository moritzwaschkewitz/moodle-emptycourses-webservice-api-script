from MoodleCourseUserManager import MoodleCourseUserManager

from datetime import datetime
from pprint import pprint


def find_empty_courses(course_users: dict[str, list], all_courses: dict[str, dict]) -> dict[str, dict]:
    return {
        course_id: all_courses[course_id]
        for course_id, users in course_users.items()
        if len(users) == 0 and course_id in all_courses
    }


# TODO: sort by last user access?
def sort_courses_by_timemodified(courses: dict[str, dict]) -> list[dict]:
    return sorted(courses.values(), key=lambda course: course['timemodified'])


def add_readable_dates_to_courses(courses: list[dict]) -> None:
    """ adds human-readable timestamps to list of courses """

    for course in courses:
        for key in ('timemodified', 'timecreated', 'startdate'):
            value = course.get(key)
            if isinstance(value, int):
                course[f"{key}_human"] = datetime.fromtimestamp(course[key]).strftime('%Y-%m-%d %H:%M:%S')


def main():
    PE2_TUT_ID = '10979'

    manager = MoodleCourseUserManager(debug=True)
    course_users = manager.all_course_users
    all_courses = manager.all_courses

    '''
    for course in all_courses:
        print(course["id"], course["fullname"])
    '''

    pe2_tut_course = all_courses[PE2_TUT_ID]

    pprint(pe2_tut_course)

    print(f"Eingeschriebene Nutzer/innen in PE2-TUT: {len(course_users[PE2_TUT_ID])}")

    empty_courses = find_empty_courses(course_users, all_courses)
    # pprint(empty_courses)

    sorted_empty_courses = sort_courses_by_timemodified(empty_courses)
    add_readable_dates_to_courses(sorted_empty_courses)
    pprint(sorted_empty_courses[-1])

    pprint(f"Anzahl leerer Kurse: {len(sorted_empty_courses)}")


if __name__ == "__main__":
    main()
