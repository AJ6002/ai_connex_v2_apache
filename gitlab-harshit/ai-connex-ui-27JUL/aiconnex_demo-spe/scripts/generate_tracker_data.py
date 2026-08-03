import pandas as pd
import sqlite3
import datetime
import os

# Define the project start date for offset calculations
proj_start = datetime.date(2026, 7, 16)

# Define the detailed dataset with task dates
data = [
    {
        "Task_ID": "T001",
        "Timeline_Phase": "Yesterday",
        "Category": "Preprocessing & Evaluation",
        "Task_Description": "Verified data preprocessing and model evaluation workflow.",
        "Status": "Completed",
        "Type": "Completed Task",
        "Start_Date": "2026-07-16",
        "End_Date": "2026-07-16",
        "Notes_Context": "Baseline data prep and model validation verified."
    },
    {
        "Task_ID": "T002",
        "Timeline_Phase": "Yesterday",
        "Category": "SageMaker Pipeline",
        "Task_Description": "Explored SageMaker training instance requirements and pipeline feasibility.",
        "Status": "Completed",
        "Type": "Completed Task",
        "Start_Date": "2026-07-16",
        "End_Date": "2026-07-16",
        "Notes_Context": "Identified instance needs for production pipeline."
    },
    {
        "Task_ID": "T003",
        "Timeline_Phase": "Yesterday",
        "Category": "AWS Quota",
        "Task_Description": "SageMaker training jobs blocked due to 0 quota for ml.m5.large.",
        "Status": "Blocked",
        "Type": "Blocked Task",
        "Start_Date": "2026-07-16",
        "End_Date": "2026-07-17",
        "Notes_Context": "Quota is 0. Prevents running any training jobs."
    },
    {
        "Task_ID": "T004",
        "Timeline_Phase": "Yesterday",
        "Category": "AWS Administration",
        "Task_Description": "Created a new AWS account.",
        "Status": "Completed",
        "Type": "Action Taken",
        "Start_Date": "2026-07-16",
        "End_Date": "2026-07-16",
        "Notes_Context": "Fresh AWS account to isolate development."
    },
    {
        "Task_ID": "T005",
        "Timeline_Phase": "Yesterday",
        "Category": "AWS Quota",
        "Task_Description": "Submitted SageMaker service quota increase requests.",
        "Status": "Completed",
        "Type": "Action Taken",
        "Start_Date": "2026-07-16",
        "End_Date": "2026-07-16",
        "Notes_Context": "Submitted request; awaiting AWS approval for ml.m5.large."
    },
    {
        "Task_ID": "T006",
        "Timeline_Phase": "Yesterday",
        "Category": "AWS Administration",
        "Task_Description": "Verified AWS access.",
        "Status": "Completed",
        "Type": "Action Taken",
        "Start_Date": "2026-07-16",
        "End_Date": "2026-07-16",
        "Notes_Context": "Checked credentials; verified CLI/SDK access."
    },
    {
        "Task_ID": "T007",
        "Timeline_Phase": "Yesterday",
        "Category": "AWS IAM",
        "Task_Description": "Created the required IAM execution role.",
        "Status": "Completed",
        "Type": "Action Taken",
        "Start_Date": "2026-07-16",
        "End_Date": "2026-07-16",
        "Notes_Context": "Configured with necessary S3, SageMaker, & CloudWatch permissions."
    },
    {
        "Task_ID": "T008",
        "Timeline_Phase": "Today",
        "Category": "Airflow Integration",
        "Task_Description": "Verified that SageMaker SDK pipelines can be imported into Apache Airflow (Unified Studio) as a visual DAG.",
        "Status": "Completed",
        "Type": "Completed Task",
        "Start_Date": "2026-07-17",
        "End_Date": "2026-07-17",
        "Notes_Context": "Successfully verified the visual DAG import mechanism."
    },
    {
        "Task_ID": "T009",
        "Timeline_Phase": "Today",
        "Category": "Pipeline Design",
        "Task_Description": "Completed the design of the 12-node production ML pipeline (Data Cleaning → Model Registry).",
        "Status": "Completed",
        "Type": "Completed Task",
        "Start_Date": "2026-07-17",
        "End_Date": "2026-07-17",
        "Notes_Context": "Layout and connections of all 12 stages finalized."
    },
    {
        "Task_ID": "T010",
        "Timeline_Phase": "Today",
        "Category": "Pipeline Design",
        "Task_Description": "Designed a dynamic manifest.json metadata contract to support multiple algorithms (Regression / Anomaly Detection) using a single pipeline.",
        "Status": "Completed",
        "Type": "Completed Task",
        "Start_Date": "2026-07-17",
        "End_Date": "2026-07-17",
        "Notes_Context": "Contract allows single-pipeline multi-algorithm support."
    },
    {
        "Task_ID": "T011",
        "Timeline_Phase": "Today",
        "Category": "Sorba AI Integration",
        "Task_Description": "Reviewed the Sorba AI Trainer Toolkit architecture and capabilities for potential integration.",
        "Status": "Completed",
        "Type": "Completed Task",
        "Start_Date": "2026-07-17",
        "End_Date": "2026-07-17",
        "Notes_Context": "Evaluated architecture for compatibility."
    },
    {
        "Task_ID": "T012",
        "Timeline_Phase": "Today",
        "Category": "Script Development",
        "Task_Description": "Begin developing modular Python scripts for: Data Cleaning, Data Validation, Data Splitting.",
        "Status": "In Progress",
        "Type": "In Progress",
        "Start_Date": "2026-07-17",
        "End_Date": "2026-07-18",
        "Notes_Context": "Scripts currently being written and tested locally."
    },
    {
        "Task_ID": "T013",
        "Timeline_Phase": "Today",
        "Category": "SageMaker Pipeline",
        "Task_Description": "Package modular Python scripts as SageMaker Processing Jobs.",
        "Status": "In Progress",
        "Type": "In Progress",
        "Start_Date": "2026-07-17",
        "End_Date": "2026-07-18",
        "Notes_Context": "Packaging scripts into containerized processing steps."
    },
    {
        "Task_ID": "T014",
        "Timeline_Phase": "Tomorrow / Next Steps",
        "Category": "SageMaker Pipeline",
        "Task_Description": "Implement the complete SageMaker SDK pipeline by connecting all 12 pipeline stages.",
        "Status": "Planned",
        "Type": "Planned Task",
        "Start_Date": "2026-07-18",
        "End_Date": "2026-07-19",
        "Notes_Context": "Connecting all stages end-to-end."
    },
    {
        "Task_ID": "T015",
        "Timeline_Phase": "Tomorrow / Next Steps",
        "Category": "Pipeline Validation",
        "Task_Description": "Execute end-to-end pipeline validation using the C-MAPSS dataset (Regression XGBoost & Anomaly Detection Isolation Forest).",
        "Status": "Planned",
        "Type": "Planned Task",
        "Start_Date": "2026-07-19",
        "End_Date": "2026-07-20",
        "Notes_Context": "Validation with target datasets."
    },
    {
        "Task_ID": "T016",
        "Timeline_Phase": "Tomorrow / Next Steps",
        "Category": "Pipeline Validation",
        "Task_Description": "Test external pipeline execution through the AWS CLI with runtime parameters.",
        "Status": "Planned",
        "Type": "Planned Task",
        "Start_Date": "2026-07-20",
        "End_Date": "2026-07-20",
        "Notes_Context": "Command line validation."
    },
    {
        "Task_ID": "T017",
        "Timeline_Phase": "Tomorrow / Next Steps",
        "Category": "Agentic Monitoring",
        "Task_Description": "Design an Agentic Monitoring architecture (e.g., Bedrock Agents) for model drift detection, automated retraining, and future pipeline optimization.",
        "Status": "Planned",
        "Type": "Planned Task",
        "Start_Date": "2026-07-20",
        "End_Date": "2026-07-22",
        "Notes_Context": "Future architectural work for continuous operations."
    }
]

df = pd.DataFrame(data)

# Calculate Start Offset and Duration
df['Start_Date_Dt'] = pd.to_datetime(df['Start_Date']).dt.date
df['End_Date_Dt'] = pd.to_datetime(df['End_Date']).dt.date

df['Start_Offset_Days'] = df['Start_Date_Dt'].apply(lambda x: (x - proj_start).days)
df['Duration_Days'] = df.apply(lambda r: max((r['End_Date_Dt'] - r['Start_Date_Dt']).days, 1), axis=1)

# Drop date objects
df_excel = df.drop(columns=['Start_Date_Dt', 'End_Date_Dt'])

# Ensure output directory paths are absolute or in workspace root
workspace_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 1. Save as CSV
csv_path = os.path.join(workspace_root, "project_tracker.csv")
df_excel.to_csv(csv_path, index=False)
print(f"Saved CSV: {csv_path}")

# 2. Save as Excel with Gantt Chart
xlsx_path = os.path.join(workspace_root, "project_tracker.xlsx")
try:
    writer = pd.ExcelWriter(xlsx_path, engine="xlsxwriter")
    df_excel.to_excel(writer, sheet_name="Sheet1", index=False)

    workbook = writer.book
    worksheet = writer.sheets["Sheet1"]

    # Format the header and sheet cells
    worksheet.set_column("A:A", 10)  # Task_ID
    worksheet.set_column("B:B", 15)  # Timeline_Phase
    worksheet.set_column("C:C", 25)  # Category
    worksheet.set_column("D:D", 50)  # Task_Description
    worksheet.set_column("E:E", 15)  # Status
    worksheet.set_column("F:F", 12)  # Type
    worksheet.set_column("G:G", 12)  # Start_Date
    worksheet.set_column("H:H", 12)  # End_Date
    worksheet.set_column("I:I", 40)  # Notes_Context
    worksheet.set_column("J:J", 18)  # Start_Offset_Days
    worksheet.set_column("K:K", 15)  # Duration_Days

    # Create the Gantt stacked bar chart
    chart = workbook.add_chart({'type': 'bar', 'subtype': 'stacked'})

    # Series 1 (Start Offset) - invisible
    # Data range: Row 1 to Row len(data), Col 9 (J = 9 in 0-based indexing)
    # Categories: Col 3 (D = 3 in 0-based indexing)
    chart.add_series({
        'categories': ['Sheet1', 1, 3, len(df_excel), 3],
        'values':     ['Sheet1', 1, 9, len(df_excel), 9],
        'fill':       {'none': True},
        'border':     {'none': True},
        'name':       'Start Offset',
    })

    # Series 2 (Duration) - visible
    # Data range: Col 10 (K = 10 in 0-based indexing)
    chart.add_series({
        'categories': ['Sheet1', 1, 3, len(df_excel), 3],
        'values':     ['Sheet1', 1, 10, len(df_excel), 10],
        'fill':       {'color': '#4F81BD'},
        'border':     {'color': '#385D8A'},
        'name':       'Duration (Days)',
    })

    # Set chart titles and properties
    chart.set_title({'name': 'Project Timeline (Gantt Chart)'})
    chart.set_x_axis({
        'name': 'Days from Project Start (July 16, 2026)',
        'min': 0,
        'max': 10,
    })
    chart.set_y_axis({
        'reverse': True,  # Keep tasks reading top-to-bottom
    })

    # Set chart size to fit all tasks beautifully
    chart.set_size({'width': 850, 'height': 600})

    # Insert chart to the right of the table
    worksheet.insert_chart('M2', chart)

    writer.close()
    print(f"Saved Excel with Gantt Chart: {xlsx_path}")
except Exception as e:
    print(f"Failed to generate Excel with Gantt chart: {e}")
    # Fallback to standard save if writer fails
    try:
        df_excel.to_excel(xlsx_path, index=False)
        print(f"Saved fallback Excel (no chart): {xlsx_path}")
    except Exception as ex:
        print(f"Excel generation failed completely: {ex}")

# 3. Save as SQLite DB
db_path = os.path.join(workspace_root, "project_tracker.db")
try:
    conn = sqlite3.connect(db_path)
    df_excel.to_sql("tracker", conn, if_exists="replace", index=False)
    conn.close()
    print(f"Saved SQLite DB: {db_path}")
except Exception as e:
    print(f"Failed to save SQLite DB: {e}")
