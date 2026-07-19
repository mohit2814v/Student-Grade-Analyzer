import time
import numpy as np
from sklearn.metrics import (
    mean_absolute_error, mean_squared_error, r2_score,
    accuracy_score, precision_score, recall_score, f1_score,
    confusion_matrix, classification_report
)

# Regression Models
from sklearn.linear_model import LinearRegression
from sklearn.tree import DecisionTreeRegressor
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor, AdaBoostRegressor, ExtraTreesRegressor
from sklearn.svm import SVR
from sklearn.neighbors import KNeighborsRegressor

# Classification Models
from sklearn.linear_model import LogisticRegression
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier, AdaBoostClassifier, ExtraTreesClassifier
from sklearn.svm import SVC
from sklearn.neighbors import KNeighborsClassifier

def get_regression_models(seed=42):
    return {
        "Linear Regression": LinearRegression(),
        "Decision Tree Regressor": DecisionTreeRegressor(random_state=seed),
        "Random Forest Regressor": RandomForestRegressor(random_state=seed, n_estimators=100),
        "Support Vector Regressor": SVR(kernel='rbf'),
        "K-Nearest Neighbors Regressor": KNeighborsRegressor(n_neighbors=5),
        "Gradient Boosting Regressor": GradientBoostingRegressor(random_state=seed),
        "AdaBoost Regressor": AdaBoostRegressor(random_state=seed),
        "Extra Trees Regressor": ExtraTreesRegressor(random_state=seed, n_estimators=100)
    }

def get_classification_models(seed=42):
    return {
        "Logistic Regression": LogisticRegression(max_iter=1000, random_state=seed),
        "Decision Tree Classifier": DecisionTreeClassifier(random_state=seed),
        "Random Forest Classifier": RandomForestClassifier(random_state=seed, n_estimators=100),
        "Support Vector Classifier": SVC(probability=True, random_state=seed),
        "K-Nearest Neighbors Classifier": KNeighborsClassifier(n_neighbors=5),
        "Gradient Boosting Classifier": GradientBoostingClassifier(random_state=seed),
        "AdaBoost Classifier": AdaBoostClassifier(random_state=seed),
        "Extra Trees Classifier": ExtraTreesClassifier(random_state=seed, n_estimators=100)
    }

def evaluate_regression(model, X_train, X_test, y_train, y_test):
    """
    Train a regressor and evaluate its performance.
    Returns a dictionary of metrics, training time, and prediction time.
    """
    # Measure Training Time
    start_train = time.time()
    model.fit(X_train, y_train)
    train_time = time.time() - start_train
    
    # Measure Prediction Time and Test Performance
    start_pred = time.time()
    y_pred = model.predict(X_test)
    pred_time = time.time() - start_pred
    
    # Train performance (for comparison)
    y_pred_train = model.predict(X_train)
    
    # Calculate metrics
    mae_test = float(mean_absolute_error(y_test, y_pred))
    mse_test = float(mean_squared_error(y_test, y_pred))
    rmse_test = float(np.sqrt(mse_test))
    r2_test = float(r2_score(y_test, y_pred))
    
    r2_train = float(r2_score(y_train, y_pred_train))
    
    return {
        "training_time_sec": float(train_time),
        "prediction_time_sec": float(pred_time),
        "train_r2": r2_train,
        "test_r2": r2_test,
        "test_mae": mae_test,
        "test_mse": mse_test,
        "test_rmse": rmse_test
    }

def evaluate_classification(model, X_train, X_test, y_train, y_test):
    """
    Train a classifier and evaluate its performance.
    Returns a dictionary of metrics, training time, and prediction time.
    """
    # Measure Training Time
    start_train = time.time()
    model.fit(X_train, y_train)
    train_time = time.time() - start_train
    
    # Measure Prediction Time and Test Performance
    start_pred = time.time()
    y_pred = model.predict(X_test)
    pred_time = time.time() - start_pred
    
    # Train performance
    y_pred_train = model.predict(X_train)
    
    # Calculate metrics
    acc_train = float(accuracy_score(y_train, y_pred_train))
    acc_test = float(accuracy_score(y_test, y_pred))
    
    precision = float(precision_score(y_test, y_pred, zero_division=0))
    recall = float(recall_score(y_test, y_pred, zero_division=0))
    f1 = float(f1_score(y_test, y_pred, zero_division=0))
    
    cm = confusion_matrix(y_test, y_pred).tolist()
    cr = classification_report(y_test, y_pred, zero_division=0, output_dict=True)
    
    return {
        "training_time_sec": float(train_time),
        "prediction_time_sec": float(pred_time),
        "train_accuracy": acc_train,
        "test_accuracy": acc_test,
        "precision": precision,
        "recall": recall,
        "f1_score": f1,
        "confusion_matrix": cm,
        "classification_report": cr
    }
