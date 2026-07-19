import os
import joblib
import pandas as pd
import numpy as np
from datetime import datetime

import utils.db_helper as db
from utils.recommendations import generate_recommendations

# Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODELS_DIR = os.path.join(BASE_DIR, 'models')

def get_grade_and_category(score):
    """Determine the grade and category based on final percentage score."""
    if score >= 90.0:
        return 'A+', 'Excellent'
    elif score >= 80.0:
        return 'A', 'Very Good'
    elif score >= 70.0:
        return 'B', 'Good'
    elif score >= 50.0:
        return 'C', 'Average'
    elif score >= 35.0:
        return 'D', 'Needs Improvement'
    else:
        return 'F', 'At Risk'

def make_prediction(student_data):
    """
    Take student features dictionary, run preprocessing and ML models,
    generate recommendations, save results in DB, and return structured prediction.
    """
    # 1. Verify model files exist
    preprocessor_path = os.path.join(MODELS_DIR, 'preprocessor.pkl')
    regressor_path = os.path.join(MODELS_DIR, 'best_regressor.pkl')
    classifier_path = os.path.join(MODELS_DIR, 'best_classifier.pkl')
    
    if not (os.path.exists(preprocessor_path) and os.path.exists(regressor_path) and os.path.exists(classifier_path)):
        raise FileNotFoundError("Model artifacts are missing. Please train the models before making predictions.")
        
    # 2. Load models
    preprocessor = joblib.load(preprocessor_path)
    regressor = joblib.load(regressor_path)
    classifier = joblib.load(classifier_path)
    
    # 3. Get active model names from DB to show in report
    active_reg_info = db.get_active_model('regression')
    active_clf_info = db.get_active_model('classification')
    reg_name = active_reg_info['model_name'] if active_reg_info else "Best Regressor"
    clf_name = active_clf_info['model_name'] if active_clf_info else "Best Classifier"
    
    # Convert input dict to single row DataFrame
    input_df = pd.DataFrame([student_data])
    
    # 4. Transform data
    X_processed = preprocessor.transform(input_df)
    
    # 5. Predict Score
    predicted_score = float(regressor.predict(X_processed)[0])
    predicted_score = max(0.0, min(100.0, round(predicted_score, 1)))
    
    # Determine grade and category
    grade, category = get_grade_and_category(predicted_score)
    
    # 6. Predict Pass/Fail and Confidence
    predicted_status_num = int(classifier.predict(X_processed)[0])
    predicted_status = "Pass" if predicted_status_num == 1 else "Fail"
    
    # Calculate confidence from probabilities
    confidence = 1.0
    if hasattr(classifier, "predict_proba"):
        probs = classifier.predict_proba(X_processed)[0]
        confidence = float(np.max(probs))
    else:
        # Fallback based on training accuracy or model score
        active_clf = db.get_active_model('classification')
        if active_clf:
            confidence = active_clf['metrics'].get('test_accuracy', 0.85)
            
    confidence_pct = round(confidence * 100, 1)
    
    # 7. Generate recommendations
    suggestions = generate_recommendations(student_data, predicted_score)
    
    # 8. Save to Database
    # Insert Student Details
    student_id = db.insert_student(student_data)
    
    # Insert Prediction
    pred_data = {
        "student_id": student_id,
        "predicted_score": predicted_score,
        "predicted_grade": grade,
        "predicted_status": predicted_status,
        "performance_category": category,
        "model_used": f"{reg_name} (Score), {clf_name} (Pass/Fail)",
        "suggestions": "\n".join([f"[{s['priority']}] {s['category']}: {s['text']}" for s in suggestions])
    }
    
    prediction_id = db.insert_prediction(pred_data)
    
    # Return complete report dictionary
    return {
        "prediction_id": prediction_id,
        "student_id": student_id,
        "student_name": student_data['name'],
        "predicted_score": predicted_score,
        "predicted_grade": grade,
        "predicted_status": predicted_status,
        "performance_category": category,
        "confidence_pct": confidence_pct,
        "model_used": pred_data["model_used"],
        "suggestions": suggestions,
        "prediction_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
