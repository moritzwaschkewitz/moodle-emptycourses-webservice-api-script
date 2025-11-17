import csv
from pathlib import Path


class CsvExporter:
    def export(self, csv_directory_path: Path, empty_courses_per_supercategory: dict[str, list[dict]]) -> None:
        if not csv_directory_path.exists():
            csv_directory_path.mkdir(parents=True, exist_ok=True)
        for supercategory_name, empty_courses_list in empty_courses_per_supercategory.items():
            if not empty_courses_list:
                continue
            fieldnames = list(empty_courses_list[0].keys())
            file_path = csv_directory_path / f"{supercategory_name}.csv"
            with open(file_path, "w", newline="", encoding="utf-8") as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames, extrasaction="ignore")
                writer.writeheader()
                writer.writerows(empty_courses_list)
