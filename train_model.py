import os
import joblib
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split

from utils.preprocessor import StudentDataPreprocessor
from utils.generate_dataset import generate_student_dataset
import utils.db_helper as db
import model

# Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATASET_PATH = os.path.join(BASE_DIR, 'dataset', 'student_data.csv')
MODELS_DIR = os.path.join(BASE_DIR, 'models')
LOG_PATH = os.path.join(MODELS_DIR, 'training_log.txt')

def run_training_pipeline(dataset_path=DATASET_PATH, split_ratio=0.2, seed=42):
    """
    Orchestrates the ML pipeline:
    1. Loads dataset (generating synthetic if missing).
    2. Runs Preprocessor fitting & transformation.
    3. Splits data into train & test.
    4. Trains and evaluates all regressors and classifiers.
    5. Identifies best models and serializes them.
    6. Logs metrics in SQLite and text files.
    """
    os.makedirs(MODELS_DIR, exist_ok=True)
    db.init_db()
    
    logs = []
    def log_print(msg):
        print(msg)
        logs.append(msg)
        
    log_print(f"=== Starting Model Training Pipeline at {pd.Timestamp.now()} ===")
    
    # 1. Check/Generate Dataset
    if not os.path.exists(dataset_path):
        log_print("Dataset not found. Generating default synthetic dataset...")
        generate_student_dataset(dataset_path, num_samples=1000, seed=seed)
        
    df = pd.read_csv(dataset_path)
    log_print(f"Loaded dataset: {df.shape[0]} rows, {df.shape[1]} columns.")
    
    # 2. Check for missing values and duplicates
    missing_cnt = df.isnull().sum().sum()
    duplicate_cnt = df.duplicated().sum()
    log_print(f"Initial checks: {missing_cnt} missing values, {duplicate_cnt} duplicates found.")
    
    # Remove duplicates before fit
    if duplicate_cnt > 0:
        df = df.drop_duplicates().reset_index(drop=True)
        log_print(f"Removed duplicates. New shape: {df.shape[0]} rows.")
        
    # Verify we have target column
    if 'final_score' not in df.columns:
        raise ValueError("Dataset does not contain target column: 'final_score'")
        
    # 3. Fit and save preprocessor
    log_print("Fitting data preprocessor...")
    preprocessor = StudentDataPreprocessor()
    preprocessor.fit(df)
    
    # Save the fitted preprocessor
    preprocessor_path = os.path.join(MODELS_DIR, 'preprocessor.pkl')
    joblib.dump(preprocessor, preprocessor_path)
    log_print(f"Preprocessor saved to {preprocessor_path}")
    
    # Transform dataset
    X_processed = preprocessor.transform(df)
    y_regression = df['final_score'].values
    y_classification = (y_regression >= 50.0).astype(int)  # 1 = Pass, 0 = Fail
    
    log_print(f"Preprocessed features shape: {X_processed.shape}")
    
    # 4. Train-Test Split
    X_train, X_test, y_train_reg, y_test_reg = train_test_split(
        X_processed, y_regression, test_size=split_ratio, random_state=seed
    )
    _, _, y_train_clf, y_test_clf = train_test_split(
        X_processed, y_classification, test_size=split_ratio, random_state=seed
    )
    
    # 5. Train & Evaluate Regressors
    log_print("\n--- Training Regression Models (Target: Final Score) ---")
    reg_models = model.get_regression_models(seed=seed)
    reg_results = {}
    
    for name, reg in reg_models.items():
        log_print(f"Training {name}...")
        try:
            results = model.evaluate_regression(reg, X_train, X_test, y_train_reg, y_test_reg)
            reg_results[name] = {
                "model_obj": reg,
                "metrics": results
            }
            log_print(f"  -> R² Score: {results['test_r2']:.4f} | MAE: {results['test_mae']:.4f} | Time: {results['training_time_sec']:.4f}s")
        except Exception as e:
            log_print(f"  -> Failed training {name}: {str(e)}")

    # 6. Train & Evaluate Classifiers
    log_print("\n--- Training Classification Models (Target: Pass/Fail) ---")
    clf_models = model.get_classification_models(seed=seed)
    clf_results = {}
    
    for name, clf in clf_models.items():
        log_print(f"Training {name}...")
        try:
            results = model.evaluate_classification(clf, X_train, X_test, y_train_clf, y_test_clf)
            clf_results[name] = {
                "model_obj": clf,
                "metrics": results
            }
            log_print(f"  -> Accuracy: {results['test_accuracy']:.4f} | F1 Score: {results['f1_score']:.4f} | Time: {results['training_time_sec']:.4f}s")
        except Exception as e:
            log_print(f"  -> Failed training {name}: {str(e)}")

    # 7. Select and Save Best Regressor (Highest Test R²)
    best_reg_name = None
    best_reg_r2 = -float('inf')
    for name, res in reg_results.items():
        if res["metrics"]["test_r2"] > best_reg_r2:
            best_reg_r2 = res["metrics"]["test_r2"]
            best_reg_name = name
            
    if best_reg_name:
        best_reg_model = reg_results[best_reg_name]["model_obj"]
        best_reg_path = os.path.join(MODELS_DIR, 'best_regressor.pkl')
        joblib.dump(best_reg_model, best_reg_path)
        log_print(f"\nBest Regressor Selected: {best_reg_name} (R² = {best_reg_r2:.4f})")
        log_print(f"Saved to: {best_reg_path}")
        
        # Save to database
        db.save_trained_model(
            model_name=best_reg_name,
            model_type='regression',
            metrics=reg_results[best_reg_name]["metrics"],
            file_path=best_reg_path,
            is_active=1
        )
        
        # Save other regressor metrics to DB as inactive models for comparison history
        for name, res in reg_results.items():
            if name != best_reg_name:
                db.save_trained_model(
                    model_name=name,
                    model_type='regression',
                    metrics=res["metrics"],
                    file_path="",
                    is_active=0
                )
    else:
        log_print("No regressor trained successfully.")

    # 8. Select and Save Best Classifier (Highest Test F1 Score)
    best_clf_name = None
    best_clf_f1 = -float('inf')
    for name, res in clf_results.items():
        if res["metrics"]["f1_score"] > best_clf_f1:
            best_clf_f1 = res["metrics"]["f1_score"]
            best_clf_name = name
            
    if best_clf_name:
        best_clf_model = clf_results[best_clf_name]["model_obj"]
        best_clf_path = os.path.join(MODELS_DIR, 'best_classifier.pkl')
        joblib.dump(best_clf_model, best_clf_path)
        log_print(f"Best Classifier Selected: {best_clf_name} (F1 Score = {best_clf_f1:.4f})")
        log_print(f"Saved to: {best_clf_path}")
        
        # Save to database
        db.save_trained_model(
            model_name=best_clf_name,
            model_type='classification',
            metrics=clf_results[best_clf_name]["metrics"],
            file_path=best_clf_path,
            is_active=1
        )
        
        # Save other classifier metrics to DB
        for name, res in clf_results.items():
            if name != best_clf_name:
                db.save_trained_model(
                    model_name=name,
                    model_type='classification',
                    metrics=res["metrics"],
                    file_path="",
                    is_active=0
                )
    else:
        log_print("No classifier trained successfully.")
        
    # 9. Log Training session in SQLite
    dataset_name = os.path.basename(dataset_path)
    best_clf_acc = clf_results[best_clf_name]["metrics"]["test_accuracy"] if best_clf_name else 0.0
    
    db.log_training_run(
        dataset_name=dataset_name,
        num_samples=df.shape[0],
        regression_best_model=best_reg_name or "None",
        regression_best_r2=best_reg_r2,
        classification_best_model=best_clf_name or "None",
        classification_best_accuracy=best_clf_acc,
        log_message=f"Training pipeline run complete. Best regressor: {best_reg_name}. Best classifier: {best_clf_name}."
    )
    
    # 10. Write text log file
    with open(LOG_PATH, 'w') as f:
        f.write("\n".join(logs))
        
    log_print(f"Training run logs written to: {LOG_PATH}")
    log_print("=== Training Pipeline Complete ===")
    
    return {
        "regressors": {k: v["metrics"] for k, v in reg_results.items()},
        "classifiers": {k: v["metrics"] for k, v in clf_results.items()},
        "best_regressor": best_reg_name,
        "best_classifier": best_clf_name
    }

if __name__ == "__main__":
    run_training_pipeline()
