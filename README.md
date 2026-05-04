# Production Data Analysis with Python and SQL

This project analyzes production test data using Python and SQL. It creates a SQLite database, stores sample production measurements, runs SQL queries, detects failed products, calculates pass/fail rates, evaluates test station performance, creates charts, and generates an automated text report.

The project is inspired by industrial production and quality-control use cases, such as production testing, process data evaluation, and technical quality monitoring.

## Technologies Used

- Python
- SQLite
- SQL
- pandas
- matplotlib

## Features

- Creates a SQLite database for production test data
- Stores sample measurements such as temperature, voltage, current, and test duration
- Uses SQL queries to analyze failed products and station performance
- Calculates pass rate, fail rate, average values, and limit violations
- Detects possible failure reasons based on engineering limits
- Creates charts for production test results and pass rate by station
- Generates an automated text report

## Project Structure

```text
production-data-analysis-sql-python/
│
├── main.py
├── README.md
├── requirements.txt
├── .gitignore
├── screenshots/
│   ├── pass_fail_chart.png
│   └── station_pass_rate_chart.png
└── outputs/
    ├── production_report.txt
    ├── pass_fail_chart.png
    └── station_pass_rate_chart.png
How to Run

Clone the repository:

git clone https://github.com/amrshehata23/production-data-analysis-sql-python.git

Open the project folder:

cd production-data-analysis-sql-python

Install the required libraries:

pip install -r requirements.txt

Run the program:

python main.py
Output Files

After running the project, the program creates:

production_data.db
outputs/production_report.txt
outputs/pass_fail_chart.png
outputs/station_pass_rate_chart.png
Example Output
Production Test Results

Pass Rate by Test Station

Example Analysis

The program analyzes production test results and answers questions such as:

How many products passed or failed?

Which test station has the lowest pass rate?

Which products failed the test?

Were there abnormal temperature, voltage, or current values?

What are the average measurement values?

Skills Demonstrated

SQL database creation

SQL querying

Data analysis with pandas

Basic quality-control logic

Data visualization with matplotlib

Automated report generation

Clean Python project structure

Future Improvements

Add more production test data

Import data from CSV files

Add trend analysis over time

Build a dashboard for visualizing production quality

Extend the project with cloud basics such as AWS or Azure

Explore KQL and PySpark for larger datasets
