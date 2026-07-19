import os
import shutil
import pandas as pd
from flask import Flask, request, jsonify, render_template
from werkzeug.utils import secure_filename

import utils.db_helper as db
from utils.generate_dataset import generate_student_dataset
from train_model import run_training_pipeline
from predict import make_prediction

app = Flask(__name__)

# Config
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
DATASET_FOLDER = os.path.join(BASE_DIR, 'dataset')
ACTIVE_DATASET_PATH = os.path.join(DATASET_FOLDER, 'student_data.csv')
MODELS_DIR = os.path.join(BASE_DIR, 'models')

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16 MB limit

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(DATASET_FOLDER, exist_ok=True)

# Required features for training/predicting (except student name and final_score)
REQUIRED_FEATURES = [
    'age', 'gender', 'study_hours', 'attendance', 'prev_marks', 
    'assignments', 'participation', 'sleep_hours', 'internet_access', 
    'family_support', 'parental_education', 'tuition', 'extracurricular', 
    'discipline_score', 'internal_marks', 'practical_marks', 'quiz_marks', 'project_marks'
]

# Ensure DB is initialized on startup
db.init_db()

@app.route('/')
def home():
    """Render the SPA dashboard."""
    return render_template('index.html')

# --- DATASET MANAGEMENT ENDPOINTS ---

@app.route('/api/dataset/info', methods=['GET'])
def get_dataset_info():
    """Get metadata and statistics of the loaded dataset."""
    if not os.path.exists(ACTIVE_DATASET_PATH):
        return jsonify({"loaded": False, "message": "No dataset loaded."})
        
    try:
        df = pd.read_csv(ACTIVE_DATASET_PATH)
        
        # Summary details
        num_samples = len(df)
        num_cols = len(df.columns)
        columns = list(df.columns)
        
        # Missing values
        missing_counts = df.isnull().sum().to_dict()
        total_missing = sum(missing_counts.values())
        
        # Duplicates
        num_duplicates = int(df.duplicated().sum())
        
        # Check compatibility (required columns list)
        missing_features = [col for col in REQUIRED_FEATURES if col not in columns]
        has_target = 'final_score' in columns
        is_compatible = len(missing_features) == 0 and has_target
        
        # Descriptive statistics for primary numerical columns
        numerical_summary = {}
        target_summary = {}
        
        num_cols_to_summarize = ['study_hours', 'attendance', 'prev_marks', 'sleep_hours']
        for col in num_cols_to_summarize:
            if col in df.columns:
                numerical_summary[col] = {
                    "mean": round(float(df[col].mean()), 2),
                    "min": round(float(df[col].min()), 2),
                    "max": round(float(df[col].max()), 2)
                }
                
        if has_target:
            target_summary = {
                "mean": round(float(df['final_score'].mean()), 2),
                "min": round(float(df['final_score'].min()), 2),
                "max": round(float(df['final_score'].max()), 2),
                "pass_rate": round(float((df['final_score'] >= 50.0).mean() * 100), 1)
            }

        return jsonify({
            "loaded": True,
            "filename": "student_data.csv",
            "num_samples": num_samples,
            "num_columns": num_cols,
            "columns": columns,
            "total_missing": total_missing,
            "missing_counts": missing_counts,
            "num_duplicates": num_duplicates,
            "is_compatible": is_compatible,
            "missing_features": missing_features,
            "numerical_summary": numerical_summary,
            "target_summary": target_summary
        })
    except Exception as e:
        return jsonify({"loaded": False, "error": str(e), "message": "Failed to read dataset."}), 500

@app.route('/api/dataset/upload', methods=['POST'])
def upload_dataset():
    """Upload a custom CSV dataset."""
    if 'file' not in request.files:
        return jsonify({"error": "No file part in the request."}), 400
        
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file."}), 400
        
    if not file.filename.endswith('.csv'):
        return jsonify({"error": "Only CSV files are supported."}), 400
        
    filename = secure_filename(file.filename)
    upload_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(upload_path)
    
    try:
        # Validate CSV format by loading it
        df = pd.read_csv(upload_path)
        
        # Verify required headers
        missing_features = [col for col in REQUIRED_FEATURES if col not in df.columns]
        if missing_features:
            os.remove(upload_path)
            return jsonify({
                "error": "Incompatible CSV schema.",
                "missing_columns": missing_features,
                "message": f"CSV is missing columns: {', '.join(missing_features)}. Please check template requirements."
            }), 400
            
        if 'final_score' not in df.columns:
            os.remove(upload_path)
            return jsonify({
                "error": "Missing target column.",
                "message": "CSV must contain a 'final_score' column for model training."
            }), 400
            
        # Copy to active dataset path
        shutil.copy(upload_path, ACTIVE_DATASET_PATH)
        os.remove(upload_path)  # cleanup upload folder
        
        return jsonify({
            "success": True,
            "message": "Dataset uploaded successfully and loaded as the active dataset.",
            "rows": len(df)
        })
    except Exception as e:
        if os.path.exists(upload_path):
            os.remove(upload_path)
        return jsonify({"error": f"Failed to parse CSV file: {str(e)}"}), 500

@app.route('/api/dataset/generate', methods=['POST'])
def generate_dataset_api():
    """Trigger the creation of the default synthetic dataset."""
    try:
        generate_student_dataset(ACTIVE_DATASET_PATH, num_samples=1000, seed=42)
        return jsonify({
            "success": True,
            "message": "Synthetic dataset of 1,000 students generated successfully."
        })
    except Exception as e:
        return jsonify({"error": f"Failed to generate dataset: {str(e)}"}), 500

@app.route('/api/dataset/view', methods=['GET'])
def view_dataset_api():
    """View dataset rows in a paginated format."""
    if not os.path.exists(ACTIVE_DATASET_PATH):
        return jsonify({"error": "No active dataset found."}), 404
        
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    search_query = request.args.get('search', '', type=str)
    
    try:
        df = pd.read_csv(ACTIVE_DATASET_PATH)
        
        # Filtering if search query is provided (search by name if column exists)
        if search_query and 'name' in df.columns:
            df = df[df['name'].astype(str).str.contains(search_query, case=False)]
            
        total_rows = len(df)
        
        # Paginate
        start = (page - 1) * per_page
        end = start + per_page
        df_page = df.iloc[start:end]
        
        # Convert NaN values to None for clean JSON serialization
        df_page = df_page.where(pd.notnull(df_page), None)
        
        return jsonify({
            "total_rows": total_rows,
            "page": page,
            "per_page": per_page,
            "columns": list(df.columns),
            "data": df_page.to_dict(orient='records')
        })
    except Exception as e:
        return jsonify({"error": f"Failed to read data: {str(e)}"}), 500

@app.route('/api/dataset/delete', methods=['DELETE'])
def delete_dataset_api():
    """Delete the active dataset."""
    if os.path.exists(ACTIVE_DATASET_PATH):
        try:
            os.remove(ACTIVE_DATASET_PATH)
            return jsonify({"success": True, "message": "Active dataset deleted successfully."})
        except Exception as e:
            return jsonify({"error": f"Failed to delete file: {str(e)}"}), 500
    return jsonify({"message": "No active dataset to delete."}), 400

# --- ML TRAINING ENDPOINTS ---

@app.route('/api/train', methods=['POST'])
def train_models_api():
    """Trigger training of all models and comparison of their scores."""
    if not os.path.exists(ACTIVE_DATASET_PATH):
        return jsonify({"error": "Cannot train models. No dataset is loaded."}), 400
        
    data = request.get_json() or {}
    split_ratio = float(data.get('split_ratio', 0.2))
    seed = int(data.get('seed', 42))
    
    try:
        results = run_training_pipeline(
            dataset_path=ACTIVE_DATASET_PATH,
            split_ratio=split_ratio,
            seed=seed
        )
        return jsonify({
            "success": True,
            "message": "Model training completed successfully.",
            "best_regressor": results["best_regressor"],
            "best_classifier": results["best_classifier"]
        })
    except Exception as e:
        return jsonify({"error": f"Model training failed: {str(e)}"}), 500

@app.route('/api/models/compare', methods=['GET'])
def get_model_comparison_api():
    """Get the evaluation metrics of all trained models stored in DB."""
    try:
        models_list = db.get_all_models()
        logs = db.get_training_logs()
        
        # Check if we have models in models/ folder
        preprocessor_path = os.path.join(MODELS_DIR, 'preprocessor.pkl')
        models_trained = os.path.exists(preprocessor_path)
        
        return jsonify({
            "trained": models_trained,
            "models": models_list,
            "logs": logs
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# --- PREDICTION ENDPOINTS ---

@app.route('/api/predict', methods=['POST'])
def predict_student_api():
    """Submit student details and get prediction scores, grades, and tips."""
    data = request.get_json()
    if not data:
        return jsonify({"error": "No input data provided."}), 400
        
    # Check for required fields
    missing_fields = [field for field in REQUIRED_FEATURES if field not in data]
    if 'name' not in data:
        missing_fields.append('name')
        
    if missing_fields:
        return jsonify({
            "error": "Missing input fields.",
            "message": f"Please provide: {', '.join(missing_fields)}"
        }), 400
        
    try:
        prediction_report = make_prediction(data)
        return jsonify(prediction_report)
    except FileNotFoundError as e:
        return jsonify({
            "error": "Model not trained.",
            "message": str(e)
        }), 400
    except Exception as e:
        return jsonify({"error": f"Prediction failed: {str(e)}"}), 500

# --- PREDICTION HISTORY ENDPOINTS ---

@app.route('/api/history', methods=['GET'])
def get_history_api():
    """Fetch prediction records history from SQLite."""
    try:
        history = db.get_prediction_history()
        return jsonify(history)
    except Exception as e:
        return jsonify({"error": f"Failed to retrieve history: {str(e)}"}), 500

@app.route('/api/history/<int:pred_id>', methods=['DELETE'])
def delete_history_api(pred_id):
    """Delete a prediction record by its ID."""
    try:
        success = db.delete_prediction(pred_id)
        if success:
            return jsonify({"success": True, "message": "Prediction history record deleted."})
        return jsonify({"error": "Record not found."}), 404
    except Exception as e:
        return jsonify({"error": f"Failed to delete record: {str(e)}"}), 500

@app.route('/api/history/clear', methods=['DELETE'])
def clear_history_api():
    """Delete all records in prediction history."""
    try:
        db.clear_prediction_history()
        return jsonify({"success": True, "message": "All prediction history cleared."})
    except Exception as e:
        return jsonify({"error": f"Failed to clear history: {str(e)}"}), 500

if __name__ == '__main__':
    # Start on local port 5050 (changed from 5000 to avoid conflicts with other projects)
    port = int(os.environ.get('PORT', 5050))
    app.run(host='127.0.0.1', port=port, debug=True)
