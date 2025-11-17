from pathlib import Path
from datetime import datetime

from course_analyzer import CourseAnalyzer


def main():
    print(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    manager = CourseAnalyzer()
    manager.find_and_export_empty_courses_to_csv([], Path.cwd() / 'csv_exports')
    print(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))


if __name__ == "__main__":
    main()
