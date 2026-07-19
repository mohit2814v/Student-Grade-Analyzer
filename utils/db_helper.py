import os
import sqlite3
import json
from datetime import datetime

DATABASE_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'database')
DATABASE_PATH = os.path.join(DATABASE_DIR, 'prediction_history.db')

def get_db_connection():
    os.makedirs(DATABASE_DIR, exist_ok=True)
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initialize database and create tables if they do not exist."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 1. Students Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            age INTEGER,
            gender TEXT,
            study_hours REAL,
            attendance REAL,
            prev_marks REAL,
            assignments INTEGER,
            participation REAL,
            sleep_hours REAL,
            internet_access TEXT,
            family_support TEXT,
            parental_education TEXT,
            tuition TEXT,
            extracurricular TEXT,
            discipline_score REAL,
            internal_marks REAL,
            practical_marks REAL,
            quiz_marks REAL,
            project_marks REAL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # 2. Predictions Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Predictions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER,
            predicted_score REAL,
            predicted_grade TEXT,
            predicted_status TEXT,
            performance_category TEXT,
            model_used TEXT,
            suggestions TEXT,
            prediction_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (student_id) REFERENCES Students(id) ON DELETE CASCADE
        )
    ''')
    
    # 3. Models Table (trained model registry)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Models (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            model_name TEXT NOT NULL,
            model_type TEXT NOT NULL, -- 'regression' or 'classification'
            metrics TEXT,            -- JSON formatted metrics
            file_path TEXT,          -- path to model pkl
            is_active INTEGER DEFAULT 0,
            trained_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # 4. TrainingLogs Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS TrainingLogs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            dataset_name TEXT,
            num_samples INTEGER,
            regression_best_model TEXT,
            regression_best_r2 REAL,
            classification_best_model TEXT,
            classification_best_accuracy REAL,
            log_message TEXT
        )
    ''')
    
    conn.commit()
    conn.close()
    print("Database initialized successfully.")

def insert_student(data):
    """Insert a student and return their auto-generated ID."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO Students (
            name, age, gender, study_hours, attendance, prev_marks,
            assignments, participation, sleep_hours, internet_access,
            family_support, parental_education, tuition, extracurricular,
            discipline_score, internal_marks, practical_marks, quiz_marks, project_marks
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        data['name'], data.get('age'), data.get('gender'), data.get('study_hours'),
        data.get('attendance'), data.get('prev_marks'), data.get('assignments'),
        data.get('participation'), data.get('sleep_hours'), data.get('internet_access'),
        data.get('family_support'), data.get('parental_education'), data.get('tuition'),
        data.get('extracurricular'), data.get('discipline_score'), data.get('internal_marks'),
        data.get('practical_marks'), data.get('quiz_marks'), data.get('project_marks')
    ))
    
    student_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return student_id

def insert_prediction(data):
    """Insert a prediction record."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO Predictions (
            student_id, predicted_score, predicted_grade, predicted_status,
            performance_category, model_used, suggestions
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (
        data['student_id'], data['predicted_score'], data['predicted_grade'],
        data['predicted_status'], data['performance_category'],
        data['model_used'], data['suggestions']
    ))
    
    prediction_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return prediction_id

def get_prediction_history():
    """Retrieve all predictions with student details."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT p.id as prediction_id, p.predicted_score, p.predicted_grade,
               p.predicted_status, p.performance_category, p.model_used, p.suggestions, p.prediction_date,
               s.id as student_id, s.name, s.age, s.gender, s.study_hours, s.attendance, s.prev_marks,
               s.assignments, s.participation, s.sleep_hours, s.internet_access, s.family_support,
               s.parental_education, s.tuition, s.extracurricular, s.discipline_score,
               s.internal_marks, s.practical_marks, s.quiz_marks, s.project_marks
        FROM Predictions p
        JOIN Students s ON p.student_id = s.id
        ORDER BY p.prediction_date DESC
    ''')
    
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def delete_prediction(prediction_id):
    """Delete a prediction by ID (will cascade delete student if configured, but let's handle cleanup)."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get student_id first to delete from both tables
    cursor.execute('SELECT student_id FROM Predictions WHERE id = ?', (prediction_id,))
    row = cursor.fetchone()
    if row:
        student_id = row['student_id']
        cursor.execute('DELETE FROM Predictions WHERE id = ?', (prediction_id,))
        cursor.execute('DELETE FROM Students WHERE id = ?', (student_id,))
        conn.commit()
        success = True
    else:
        success = False
        
    conn.close()
    return success

def clear_prediction_history():
    """Clear all records in Predictions and Students tables."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM Predictions')
    cursor.execute('DELETE FROM Students')
    conn.commit()
    conn.close()

def save_trained_model(model_name, model_type, metrics, file_path, is_active=1):
    """Save model registration details. Set as active if specified, and deactivate others of same type."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    if is_active == 1:
        # Deactivate old active models of the same type
        cursor.execute('UPDATE Models SET is_active = 0 WHERE model_type = ?', (model_type,))
        
    cursor.execute('''
        INSERT INTO Models (model_name, model_type, metrics, file_path, is_active)
        VALUES (?, ?, ?, ?, ?)
    ''', (model_name, model_type, json.dumps(metrics), file_path, is_active))
    
    conn.commit()
    conn.close()

def get_active_model(model_type):
    """Get the active model details for a specific type (regression or classification)."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT * FROM Models 
        WHERE model_type = ? AND is_active = 1 
        ORDER BY trained_at DESC LIMIT 1
    ''', (model_type,))
    
    row = cursor.fetchone()
    conn.close()
    if row:
        res = dict(row)
        res['metrics'] = json.loads(res['metrics'])
        return res
    return None

def get_all_models():
    """Get all registered models and their performance metrics."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM Models ORDER BY trained_at DESC')
    rows = cursor.fetchall()
    conn.close()
    
    result = []
    for row in rows:
        d = dict(row)
        d['metrics'] = json.loads(d['metrics'])
        result.append(d)
    return result

def log_training_run(dataset_name, num_samples, regression_best_model, regression_best_r2,
                     classification_best_model, classification_best_accuracy, log_message):
    """Insert a log record for a model training session."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO TrainingLogs (
            dataset_name, num_samples, regression_best_model, regression_best_r2,
            classification_best_model, classification_best_accuracy, log_message
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (
        dataset_name, num_samples, regression_best_model, regression_best_r2,
        classification_best_model, classification_best_accuracy, log_message
    ))
    
    conn.commit()
    conn.close()

def get_training_logs():
    """Retrieve all training runs."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM TrainingLogs ORDER BY timestamp DESC')
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]
