import typer
import logging
from pathlib import Path
from typing import List, Optional
from dotenv import load_dotenv

from course_analyzer import CourseAnalyzer
from exporters import CsvExporter

app = typer.Typer(help="Moodle Course Analyzer CLI")
load_dotenv()


def _configure_logging(level: str) -> None:
    numeric = getattr(logging, level.upper(), None)
    if not isinstance(numeric, int):
        raise typer.BadParameter(f"Invalid log level: {level}")
    logging.basicConfig(level=numeric)


@app.command("scan")
def scan(
    exclude: Optional[List[int]] = typer.Option(
        None, "--exclude", "-e", help="Supercategory IDs to exclude. Repeat for multiple."
    ),
    csv_path: Path = typer.Option(
        Path.cwd() / 'csv_exports', "--csv-path", "-o", help="Directory to save CSV files."
    ),
    log_level: str = typer.Option("INFO", "--log-level", "-l", help="Logging level (DEBUG/INFO/...)."),
    min_users: int = typer.Option(0, "--min-users", help="Consider course empty if users <= this."),
    no_progress: bool = typer.Option(False, "--no-progress", help="Hide progress bar."),
):
    """
    Scan Moodle courses and export empty ones grouped by supercategory.
    """
    _configure_logging(log_level)
    analyzer = CourseAnalyzer()
    analyzer.find_and_export_empty_courses(
        excluded_supercategory_ids=exclude or [],
        csv_directory_path=csv_path,
        exporter=CsvExporter(),
        min_users=min_users,
        show_progress=not no_progress
    )


def main():
    app()


if __name__ == "__main__":
    main()
