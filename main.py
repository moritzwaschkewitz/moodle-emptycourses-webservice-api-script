from MoodleCourseUserManager import MoodleCourseUserManager

import json
from pprint import pprint


def main():
    '''
    courses = list_courses(ms.session, ms.settings.url, token=ms.token)
    with open("courses.json", "w", encoding="utf-8") as courses_file:
        json.dump(courses, courses_file, indent=2)

    pe2_tut_users = list_course_users(ms.session, ms.settings.url, token=ms.token, course_id=PE2_TUT_ID)
    save_course(PE2_TUT_ID, pe2_tut_users)
    '''

    PE2_TUT_ID = 10979

    manager = MoodleCourseUserManager(debug=True)
    course_users = manager.load_or_download_course_users()
    all_courses = manager.load_cached_courses()

    '''
    for course in all_courses:
        print(course["id"], course["fullname"])
    '''

    with open(f"course_users/{PE2_TUT_ID}.json", "r") as users_file:
        pe2_tut_users = json.loads(users_file.read())

    pe2_tut_course = [c for c in all_courses if c['id'] == PE2_TUT_ID][0]

    pprint(pe2_tut_course)

    print(f"Eingeschriebene Nutzer/innen in PE2-TUT: {len(pe2_tut_users)}")


if __name__ == "__main__":
    main()
