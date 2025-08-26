from CourseAnalyzer import CourseAnalyzer


def main():
    manager = CourseAnalyzer()
    manager.find_and_export_empty_courses_to_csv()


if __name__ == "__main__":
    main()
