# Student Performance Prediction System (Offline Machine Learning)

This project is a fully local, offline Machine Learning-based system to predict student final grades and pass/fail outcomes. It helps educators, academic advisors, and students identify predictive factors (such as attendance, study habits, parental support, sleep) and optimize student performance using personalized recommendations.

## Core Features
1. **Multi-Model Training & Comparison**: Automatically fits 8 regression models to estimate final marks and 8 classification models to estimate binary Pass/Fail outcomes.
2. **Local Preprocessing Pipeline**: Automatically handles missing value imputation, duplicate removal, Interquartile Range (IQR) outlier capping, category label encoding, and feature scaling.
3. **Actionable Recommendation Engine**: Employs rule-based filters matching specific input variables (attendance, study hours, sleep) to output tailored learning strategies.
4. **Interactive Single Page Application (SPA)**: Sleek Glassmorphism Dark Mode dashboard displaying custom SVG distribution charts, prediction counters, historical tables, and print-ready report sheets.
5. **No Cloud Dependency**: Runs entirely locally on port 5050 with a local SQLite database for prediction log history.

---

## Directory Structure
```
student-performance-prediction/
├── app.py                     # Flask web server and api routers
├── model.py                   # Algorithms loader and evaluation wrappers
├── train_model.py             # Orchestration script to run ML pipelines
├── predict.py                 # Predict engine using saved serialized artifacts
├── test_pipeline.py           # Automated unit testing suite
├── requirements.txt           # Package dependencies
├── README.md                  # Project documentation (this file)
├── dataset/
│   └── student_data.csv       # Training dataset CSV
├── models/
│   ├── best_regressor.pkl     # Saved score regression model
│   ├── best_classifier.pkl    # Saved pass/fail classification model
│   ├── preprocessor.pkl       # Saved fitted scaler & encoders
│   └── training_log.txt       # CLI log of model metrics
├── database/
│   └── prediction_history.db  # SQLite database
├── utils/
│   ├── db_helper.py           # SQLite database connector & CRUD queries
│   ├── preprocessor.py        # Dataset clean & scaler class definition
│   ├── recommendations.py     # Rules engine to generate learning tips
│   └── generate_dataset.py    # Correlated dataset simulation script
├── templates/
│   └── index.html             # Main dashboard frontend template
└── static/
    ├── css/
    │   └── style.css          # Glassmorphism visual stylesheet
    └── js/
        └── app.js             # Form sub, tab switching, and chart render engine
```

---

## Setup & Execution Guide

### 1. Install Dependencies
Run the command below in terminal using your Python environment path to install required libraries offline:
```bash
& "C:\Users\HP\AppData\Local\Programs\Python\Python311\python.exe" -m pip install -r requirements.txt
```

### 2. Generate Dataset & Train Models (CLI Method)
To generate the simulated student dataset and train models directly from the command line:
```bash
& "C:\Users\HP\AppData\Local\Programs\Python\Python311\python.exe" train_model.py
```
This runs the pipeline, reports the best regressor & classifier, and outputs the local metrics log.

### 3. Launch the Web Application
Start the local server:
```bash
& "C:\Users\HP\AppData\Local\Programs\Python\Python311\python.exe" app.py
```
Open your browser and navigate to:
**[http://127.0.0.1:5050](http://127.0.0.1:5050)**

From the web interface, you can:
- Generate the default 1,000-student dataset or upload your own CSV file.
- View records, inspect missing counts, and review duplicates.
- Run the ML Training pipeline using split-ratio configurations.
- View comparative regression/classification score sheets.
- Submit new student details to obtain immediate grade estimates and printable reports.

### 4. Run Automated Tests
Execute the unit test suite:
```bash
& "C:\Users\HP\AppData\Local\Programs\Python\Python311\python.exe" -m unittest test_pipeline.py
```

---

## Supported Input Features

| Feature Name | Type | Value Range / Description |
| :--- | :--- | :--- |
| **Name** | Text | Student full name |
| **Age** | Integer | 15 - 25 years |
| **Gender** | Category | Male, Female |
| **Study Hours** | Decimal | 1.0 - 10.0 hours per day |
| **Attendance** | Decimal | 50% - 100% attendance rate |
| **Previous Marks** | Decimal | 40% - 100% prior average |
| **Assignments** | Integer | 0 - 10 assignments completed |
| **Participation** | Decimal | 1.0 - 10.0 class engagement rating |
| **Sleep Hours** | Decimal | 4.0 - 10.0 hours per night |
| **Internet Access** | Category | Yes, No |
| **Family Support** | Category | Yes, No |
| **Parental Education**| Category | Low, Medium, High |
| **Tuition** | Category | Yes, No (extra classroom support) |
| **Extracurricular** | Category | Yes, No |
| **Discipline Score** | Decimal | 1.0 - 10.0 conduct score |
| **Internal Marks** | Decimal | 0.0 - 30.0 exam score |
| **Practical Marks** | Decimal | 0.0 - 30.0 exam score |
| **Quiz Marks** | Decimal | 0.0 - 20.0 exam score |
| **Project Marks** | Decimal | 0.0 - 50.0 exam score |

---

## Machine Learning Pipeline
1. **Load**: Read dataset files (CSV upload or simulated).
2. **Clean**: Impute numerical missing values using feature medians, categorical values using modes, and drop identical duplicate rows.
3. **Outlier Cap**: Clip numerical features beyond IQR bounds `[Q1 - 1.5*IQR, Q3 + 1.5*IQR]` to stabilize scaling parameters.
4. **Encode**: Map categorical variables to discrete integers (e.g. Male/Female -> 0/1).
5. **Scale**: Normalize numerical features to Z-scores using fitted train-set means and standard deviations.
6. **Split**: Split dataset (80% Train, 20% Test).
7. **Train & Tune**: Train 8 regression algorithms and 8 classification algorithms.
8. **Select**: Identify best models (based on highest Test R² and highest Test F1 Score).
9. **Save**: Save best estimators (`.pkl` models) and preprocessor mapping state.

---

## SQLite Database Schemas

### `Students`
Tracks student profiles submitted during predictions:
`id` (INTEGER PRIMARY KEY), `name` (TEXT), `age` (INTEGER), `gender` (TEXT), `study_hours` (REAL), `attendance` (REAL), `prev_marks` (REAL), `assignments` (INTEGER), `participation` (REAL), `sleep_hours` (REAL), `internet_access` (TEXT), `family_support` (TEXT), `parental_education` (TEXT), `tuition` (TEXT), `extracurricular` (TEXT), `discipline_score` (REAL), `internal_marks` (REAL), `practical_marks` (REAL), `quiz_marks` (REAL), `project_marks` (REAL), `created_at` (TIMESTAMP)

### `Predictions`
Logs historical prediction results:
`id` (INTEGER PRIMARY KEY), `student_id` (INTEGER REFERENCES Students), `predicted_score` (REAL), `predicted_grade` (TEXT), `predicted_status` (TEXT), `performance_category` (TEXT), `model_used` (TEXT), `suggestions` (TEXT), `prediction_date` (TIMESTAMP)

### `Models`
Logs active metrics:
`id` (INTEGER PRIMARY KEY), `model_name` (TEXT), `model_type` (TEXT), `metrics` (TEXT - JSON serialized), `file_path` (TEXT), `is_active` (INTEGER), `trained_at` (TIMESTAMP)

### `TrainingLogs`
Tracks historical trainer logs:
`id` (INTEGER PRIMARY KEY), `timestamp` (TIMESTAMP), `dataset_name` (TEXT), `num_samples` (INTEGER), `regression_best_model` (TEXT), `regression_best_r2` (REAL), `classification_best_model` (TEXT), `classification_best_accuracy` (REAL), `log_message` (TEXT)
