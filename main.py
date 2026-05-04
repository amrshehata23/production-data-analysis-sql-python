from pathlib import Path
import sqlite3

import matplotlib.pyplot as plt
import pandas as pd


DATABASE_FILE = Path("production_data.db")
INPUT_FILE = Path("sample_production_data.csv")
OUTPUT_DIR = Path("outputs")
REPORT_FILE = OUTPUT_DIR / "production_report.txt"
CHART_FILE = OUTPUT_DIR / "pass_fail_chart.png"
STATION_CHART_FILE = OUTPUT_DIR / "station_pass_rate_chart.png"

HIGH_TEMPERATURE_LIMIT = 90.0
LOW_VOLTAGE_LIMIT = 11.8
HIGH_CURRENT_LIMIT = 2.4


def create_database() -> None:
    """Create a SQLite database and production test table."""
    with sqlite3.connect(DATABASE_FILE) as connection:
        connection.execute("""
            CREATE TABLE IF NOT EXISTS production_tests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_id TEXT NOT NULL,
                test_station TEXT NOT NULL,
                temperature_c REAL NOT NULL CHECK (temperature_c >= 0),
                voltage_v REAL NOT NULL CHECK (voltage_v >= 0),
                current_a REAL NOT NULL CHECK (current_a >= 0),
                test_duration_s REAL NOT NULL CHECK (test_duration_s >= 0),
                test_result TEXT NOT NULL CHECK (test_result IN ('PASS', 'FAIL'))
            )
        """)


def load_input_data() -> pd.DataFrame:
    """Load production test data from a CSV input file."""
    if not INPUT_FILE.exists():
        raise FileNotFoundError(f"Input file not found: {INPUT_FILE}")

    dataframe = pd.read_csv(INPUT_FILE)

    required_columns = [
        "product_id",
        "test_station",
        "temperature_c",
        "voltage_v",
        "current_a",
        "test_duration_s",
        "test_result",
    ]

    missing_columns = [column for column in required_columns if column not in dataframe.columns]

    if missing_columns:
        raise ValueError(f"Missing required columns in CSV file: {missing_columns}")

    return dataframe


def insert_data_from_csv() -> None:
    """Insert production test data from the CSV file into the SQLite database."""
    dataframe = load_input_data()

    with sqlite3.connect(DATABASE_FILE) as connection:
        connection.execute("DELETE FROM production_tests")

        dataframe.to_sql(
            "production_tests",
            connection,
            if_exists="append",
            index=False,
        )


def load_data() -> pd.DataFrame:
    """Load production data into a pandas DataFrame."""
    with sqlite3.connect(DATABASE_FILE) as connection:
        dataframe = pd.read_sql_query(
            """
            SELECT *
            FROM production_tests
            ORDER BY id
            """,
            connection,
        )

    if dataframe.empty:
        raise ValueError("No production test data found.")

    return dataframe


def add_failure_reason(dataframe: pd.DataFrame) -> pd.DataFrame:
    """Add a simple failure reason column based on engineering limits."""
    dataframe = dataframe.copy()

    def classify_failure(row: pd.Series) -> str:
        reasons = []

        if row["temperature_c"] > HIGH_TEMPERATURE_LIMIT:
            reasons.append("High temperature")

        if row["voltage_v"] < LOW_VOLTAGE_LIMIT:
            reasons.append("Low voltage")

        if row["current_a"] > HIGH_CURRENT_LIMIT:
            reasons.append("High current")

        if row["test_result"] == "PASS":
            return "None"

        return ", ".join(reasons) if reasons else "Manual/unknown failure"

    dataframe["failure_reason"] = dataframe.apply(classify_failure, axis=1)

    return dataframe


def analyze_data(dataframe: pd.DataFrame) -> dict:
    """Calculate important production statistics."""
    total_tests = len(dataframe)
    passed_tests = int((dataframe["test_result"] == "PASS").sum())
    failed_tests = int((dataframe["test_result"] == "FAIL").sum())

    return {
        "total_tests": total_tests,
        "passed_tests": passed_tests,
        "failed_tests": failed_tests,
        "pass_rate": passed_tests / total_tests * 100,
        "fail_rate": failed_tests / total_tests * 100,
        "average_temperature": dataframe["temperature_c"].mean(),
        "maximum_temperature": dataframe["temperature_c"].max(),
        "average_voltage": dataframe["voltage_v"].mean(),
        "minimum_voltage": dataframe["voltage_v"].min(),
        "average_current": dataframe["current_a"].mean(),
        "maximum_current": dataframe["current_a"].max(),
        "average_duration": dataframe["test_duration_s"].mean(),
    }


def run_sql_queries() -> tuple[pd.DataFrame, pd.DataFrame]:
    """Run useful SQL queries directly on the database."""
    with sqlite3.connect(DATABASE_FILE) as connection:
        failed_tests = pd.read_sql_query(
            """
            SELECT
                product_id,
                test_station,
                temperature_c,
                voltage_v,
                current_a,
                test_duration_s,
                test_result
            FROM production_tests
            WHERE test_result = 'FAIL'
            ORDER BY temperature_c DESC
            """,
            connection,
        )

        station_summary = pd.read_sql_query(
            """
            SELECT
                test_station,
                COUNT(*) AS total_tests,
                SUM(CASE WHEN test_result = 'PASS' THEN 1 ELSE 0 END) AS passed_tests,
                SUM(CASE WHEN test_result = 'FAIL' THEN 1 ELSE 0 END) AS failed_tests,
                ROUND(
                    100.0 * SUM(CASE WHEN test_result = 'PASS' THEN 1 ELSE 0 END) / COUNT(*),
                    2
                ) AS pass_rate_percent,
                ROUND(AVG(temperature_c), 2) AS average_temperature,
                ROUND(AVG(voltage_v), 2) AS average_voltage,
                ROUND(AVG(current_a), 2) AS average_current
            FROM production_tests
            GROUP BY test_station
            ORDER BY pass_rate_percent ASC
            """,
            connection,
        )

    return failed_tests, station_summary


def create_charts(dataframe: pd.DataFrame, station_summary: pd.DataFrame) -> None:
    """Create production analysis charts."""
    OUTPUT_DIR.mkdir(exist_ok=True)

    result_counts = dataframe["test_result"].value_counts().reindex(["PASS", "FAIL"], fill_value=0)

    plt.figure(figsize=(7, 5))
    result_counts.plot(kind="bar")
    plt.title("Production Test Results")
    plt.xlabel("Test Result")
    plt.ylabel("Number of Tests")
    plt.xticks(rotation=0)
    plt.grid(axis="y", alpha=0.3)
    plt.tight_layout()
    plt.savefig(CHART_FILE, dpi=300)
    plt.close()

    plt.figure(figsize=(8, 5))
    plt.bar(
    station_summary["test_station"],
    station_summary["pass_rate_percent"],
)

    plt.title("Pass Rate by Test Station")
    plt.xlabel("Test Station")
    plt.ylabel("Pass Rate [%]")
    plt.ylim(0, 100)
    plt.grid(axis="y", alpha=0.3)
    plt.tight_layout()
    plt.savefig(STATION_CHART_FILE, dpi=300)
    plt.close()


def generate_report(
    dataframe: pd.DataFrame,
    analysis: dict,
    failed_tests: pd.DataFrame,
    station_summary: pd.DataFrame,
) -> None:
    """Generate a text report with production analysis results."""
    OUTPUT_DIR.mkdir(exist_ok=True)

    failed_tests = add_failure_reason(failed_tests)

    report_text = f"""
Production Data Analysis Report
========================================

Overall Results
----------------------------------------
Total tests: {analysis["total_tests"]}
Passed tests: {analysis["passed_tests"]}
Failed tests: {analysis["failed_tests"]}
Pass rate: {analysis["pass_rate"]:.2f}%
Fail rate: {analysis["fail_rate"]:.2f}%

Measurement Summary
----------------------------------------
Average temperature: {analysis["average_temperature"]:.2f} C
Maximum temperature: {analysis["maximum_temperature"]:.2f} C
Average voltage: {analysis["average_voltage"]:.2f} V
Minimum voltage: {analysis["minimum_voltage"]:.2f} V
Average current: {analysis["average_current"]:.2f} A
Maximum current: {analysis["maximum_current"]:.2f} A
Average test duration: {analysis["average_duration"]:.2f} s

Engineering Limits
----------------------------------------
High temperature limit: {HIGH_TEMPERATURE_LIMIT:.2f} C
Low voltage limit: {LOW_VOLTAGE_LIMIT:.2f} V
High current limit: {HIGH_CURRENT_LIMIT:.2f} A

Failed Products
----------------------------------------
{failed_tests.to_string(index=False)}

Station Summary
----------------------------------------
{station_summary.to_string(index=False)}

Generated Files
----------------------------------------
{CHART_FILE}
{STATION_CHART_FILE}

Project Note
----------------------------------------
This project demonstrates SQL database creation, production data analysis,
quality warning detection, station-level performance evaluation, chart
generation, and automated reporting with Python.
"""

    REPORT_FILE.write_text(report_text.strip() + "\n", encoding="utf-8")


def main() -> None:
    create_database()
    insert_data_from_csv()

    dataframe = load_data()

    analysis = analyze_data(dataframe)
    failed_tests, station_summary = run_sql_queries()

    create_charts(dataframe, station_summary)
    generate_report(dataframe, analysis, failed_tests, station_summary)

    print("Project finished successfully.")
    print(f"Database created: {DATABASE_FILE}")
    print(f"Report created: {REPORT_FILE}")
    print(f"Charts created in: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
