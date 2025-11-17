# 📚 Course Analyzer – Moodle Empty Course Scanner (CLI Tool)

This CLI application analyzes courses in a Moodle instance using the py_moodle library. 
It operates entirely from outside the Moodle server, communicating through Moodle’s official web service API. 
Because the API requires one request per course, a full analysis of a moderately sized Moodle installation can take 30–45 minutes (or more, depending on the number of courses). 
The tool identifies courses with no enrolled users, groups them by supercategory, and exports the results to CSV files for further analysis.

- **Typer** for a clean and ergonomic CLI interface
- **Seperation of concerns** (`CourseAnalyzer`, `MoodleClient`, `CSVExporter`)
- **Dependency injection** for testability
- **Extensible export system**

-------------------------------------

## Table of contents

<!-- TOC -->
* [📚 Course Analyzer – Moodle Empty Course Scanner (CLI Tool)](#-course-analyzer--moodle-empty-course-scanner-cli-tool)
  * [Table of contents](#table-of-contents)
  * [🚀 Features](#-features)
  * [🛠️ Installation](#-installation)
  * [🔐 Configuration – Moodle Credentials](#-configuration--moodle-credentials)
    * [📌 Option 1: Temporary Environment Variables (Recommended)](#-option-1-temporary-environment-variables-recommended)
      * [🐧 Linux & macOS (bash/zsh)](#-linux--macos-bashzsh)
      * [🪟 Windows PowerShell](#-windows-powershell)
      * [🪟 Windows CMD](#-windows-cmd)
    * [📌 Option 2: Use a `.env` File](#-option-2-use-a-env-file)
  * [▶️ Usage](#-usage)
  * [📁 Output](#-output)
  * [📄 License](#-license)
<!-- TOC -->

-------------------------------------

## 🚀 Features
- Scan all Moodle courses
- Identify courses without enrolled students
- Group empty courses by supercategory
- Export results as CSV files, one per supercategory
- Show progress with a console progress bar
- Flexible CLI interface via Typer
- Configurable logging levels
- Optional inclusion/exclusion of categories

-------------------------------------

## 🛠️ Installation
Requires **Python 3-10+**.

```bash
git clone https://github.com/moritzwaschkewitz/moodle-emptycourses-webservice-api-script.git course-analyzer
cd course-analyzer
pip install -r requirements.txt
```


-------------------------------------

## 🔐 Configuration – Moodle Credentials

> [!important]
> Requires a functional MoodleSession (via `py_moodle`): [see python-moodle-GitHub](https://github.com/erseco/python-moodle?tab=readme-ov-file#configure-your-environment)

To authenticate against your Moodle instance, the CLI tool requires **three environment variables**:

| Variable              | Description                                                                  |
|-----------------------|------------------------------------------------------------------------------|
| MOODLE_LOCAL_URL      | Base domain of your Moodle installation (e.g., `https://moodle.example.edu`) |
| MOODLE_LOCAL_USERNAME | Moodle username used for API login                                           |
| MOODLE_LOCAL_PASSWORD | Moodle password for the user                                                 |

These environment variables must be set in your current shell session or loaded from a `.env` file before running the CLI.

-------------------------------------

### 📌 Option 1: Temporary Environment Variables (Recommended)

#### 🐧 Linux & macOS (bash/zsh)
```bash
export MOODLE_DOMAIN="https://moodle.example.edu"
export MOODLE_USERNAME="your-username"
export MOODLE_PASSWORD="your-password"
```

#### 🪟 Windows PowerShell
```powershell
$env:MOODLE_PROD_URL = "https://moodle.example.edu"
$env:MOODLE_PROD_USERNAME = "your-username"
$env:MOODLE_PROD_PASSWORD = "your-password"
```

#### 🪟 Windows CMD
```cmd
set MOODLE_DOMAIN=https://moodle.example.edu
set MOODLE_USERNAME=your-username
set MOODLE_PASSWORD=your-password
```

-------------------------------------

### 📌 Option 2: Use a `.env` File

[see python-moodle-GitHub](https://github.com/erseco/python-moodle?tab=readme-ov-file#configure-your-environment)

> [!note]  
> This implementation of python-moodle uses the default LOCAL variants fo the environment variables.
> [See 🔐 Configuration – Moodle Credentials](#-configuration--moodle-credentials)

-------------------------------------

## ▶️ Usage

Run the CLI command

```bash
python cli.py
```

Or with optional parameters

```bash
python cli.py [OPTIONS]
```

**Examples**
- Display help
```bash
python cli.py --help
```

- Export empty courses to a specific folder:
```bash
python cli.py --csv-dir ./exports
```

- Exclude multiple supercategories:
```bash
python cli.py --exclude-supercategory 10 --exclude-supercategory 42
```

- Consider courses with (at most) 2 users as empty
```bash
python cli.py --min-users 2
```

-------------------------------------

## 📁 Output
```
exports/
 ├── Mathematics.csv
 ├── ComputerScience.csv
 ├── Humanities.csv
```

Each CSV contains:

| Column                 | Description                           |
|------------------------|---------------------------------------|
| id                     | Course ID                             |
| fullname               | Full course name                      |
| shortname              | Short course name                     |
| category               | Name of the parent category           |
| categoryid             | Category ID                           |
| latest_timestamp_unix  | Most recent activity (UNIX timestamp) |
| latest_timestamp_human | Most recent activity (human readable) |
| url                    | Direct link to the Moodle course      |

-------------------------------------

## 📄 License

MIT License – free to use, modify, and distribute.
