import os
import shutil
import unittest
import pandas as pd
import numpy as np
import sqlite3

from utils.preprocessor import StudentDataPreprocessor
from utils.generate_dataset import generate_student_dataset
import utils.db_helper as db
import model
import predict

class TestStudentPredictionPipeline(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        # Setup temporary directories for tests
        cls.test_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'test_scratch')
        os.makedirs(cls.test_dir, exist_ok=True)
        
        # Override DB path for helper during test run
        db.DATABASE_DIR = cls.test_dir
        db.DATABASE_PATH = os.path.join(cls.test_dir, 'test_history.db')
        
    @classmethod
    def tearDownClass(cls):
        # Cleanup test directories
        if os.path.exists(cls.test_dir):
            shutil.rmtree(cls.test_dir)

    def setUp(self):
        # Clear database and initialize
        db.init_db()

    def test_dataset_generation(self):
        csv_path = os.path.join(self.test_dir, 'test_students.csv')
        # Generate 10 samples
        generate_student_dataset(csv_path, num_samples=10, seed=42)
        
        self.assertTrue(os.path.exists(csv_path))
        df = pd.read_csv(csv_path)
        self.assertEqual(len(df), 10)
        self.assertEqual(len(df.columns), 20)
        self.assertIn('final_score', df.columns)
        self.assertIn('name', df.columns)

    def test_preprocessor(self):
        # Create dummy data
        data = {
            'name': ['Alice', 'Bob', 'Charlie'],
            'age': [17, np.nan, 19],
            'gender': ['Female', 'Male', np.nan],
            'study_hours': [5.0, 7.5, np.nan],
            'attendance': [90.0, np.nan, 60.0],
            'prev_marks': [80.0, 75.0, 50.0],
            'assignments': [8, 10, np.nan],
            'participation': [7.0, np.nan, 4.0],
            'sleep_hours': [8.0, 6.0, np.nan],
            'internet_access': ['Yes', 'No', np.nan],
            'family_support': ['Yes', np.nan, 'No'],
            'parental_education': ['High', 'Medium', np.nan],
            'tuition': ['No', 'Yes', np.nan],
            'extracurricular': ['Yes', 'No', np.nan],
            'discipline_score': [9.0, np.nan, 5.0],
            'internal_marks': [25.0, 20.0, 15.0],
            'practical_marks': [25.0, 20.0, 15.0],
            'quiz_marks': [18.0, 15.0, 10.0],
            'project_marks': [45.0, 38.0, 30.0],
            'final_score': [85.0, 78.0, 55.0]
        }
        
        df = pd.DataFrame(data)
        
        # Fit Preprocessor
        preprocessor = StudentDataPreprocessor()
        preprocessor.fit(df)
        
        # Transform
        X_trans = preprocessor.transform(df)
        
        # Checks
        self.assertEqual(len(X_trans), 3)
        # Check that target final_score and name are not in preprocessed features
        self.assertNotIn('final_score', X_trans.columns)
        self.assertNotIn('name', X_trans.columns)
        # Verify categorical columns are numerical now
        self.assertTrue(np.issubdtype(X_trans['gender'].dtype, np.integer))
        self.assertTrue(np.issubdtype(X_trans['internet_access'].dtype, np.integer))

    def test_database_crud(self):
        # Create dummy student
        student = {
            'name': 'Test Student', 'age': 18, 'gender': 'Male', 'study_hours': 6.0,
            'attendance': 92.0, 'prev_marks': 85.0, 'assignments': 9, 'participation': 8.0,
            'sleep_hours': 7.0, 'internet_access': 'Yes', 'family_support': 'Yes',
            'parental_education': 'High', 'tuition': 'No', 'extracurricular': 'Yes',
            'discipline_score': 9.0, 'internal_marks': 22.0, 'practical_marks': 24.0,
            'quiz_marks': 15.0, 'project_marks': 40.0
        }
        
        student_id = db.insert_student(student)
        self.assertIsNotNone(student_id)
        
        # Create prediction
        pred = {
            'student_id': student_id,
            'predicted_score': 82.5,
            'predicted_grade': 'A',
            'predicted_status': 'Pass',
            'performance_category': 'Very Good',
            'model_used': 'Random Forest Regressor',
            'suggestions': '[LOW] Habits: Maintain attendance.'
        }
        
        prediction_id = db.insert_prediction(pred)
        self.assertIsNotNone(prediction_id)
        
        # Read history
        history = db.get_prediction_history()
        self.assertEqual(len(history), 1)
        self.assertEqual(history[0]['name'], 'Test Student')
        self.assertEqual(history[0]['predicted_score'], 82.5)
        
        # Delete row
        success = db.delete_prediction(prediction_id)
        self.assertTrue(success)
        
        # Read history again
        history_after = db.get_prediction_history()
        self.assertEqual(len(history_after), 0)

    def test_model_definition(self):
        regs = model.get_regression_models()
        clfs = model.get_classification_models()
        
        self.assertIn("Linear Regression", regs)
        self.assertIn("Random Forest Regressor", regs)
        self.assertIn("Logistic Regression", clfs)
        self.assertIn("Random Forest Classifier", clfs)

if __name__ == '__main__':
    unittest.main()
