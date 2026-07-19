import pandas as pd
import numpy as np

class StudentDataPreprocessor:
    def __init__(self):
        # We define categorical mappings to be robust and handle unseen categories gracefully
        self.mappings = {
            'gender': {'male': 0, 'female': 1},
            'internet_access': {'no': 0, 'yes': 1},
            'family_support': {'no': 0, 'yes': 1},
            'tuition': {'no': 0, 'yes': 1},
            'extracurricular': {'no': 0, 'yes': 1},
            'parental_education': {'low': 0, 'medium': 1, 'high': 2}
        }
        
        self.numeric_cols = [
            'age', 'study_hours', 'attendance', 'prev_marks', 
            'assignments', 'participation', 'sleep_hours', 
            'discipline_score', 'internal_marks', 'practical_marks', 
            'quiz_marks', 'project_marks'
        ]
        
        self.categorical_cols = [
            'gender', 'internet_access', 'family_support', 
            'tuition', 'extracurricular', 'parental_education'
        ]
        
        # To store statistics for scaling and imputation during fit()
        self.medians = {}
        self.modes = {}
        self.means = {}
        self.stds = {}
        self.iqr_bounds = {}
        self.feature_columns_ = []

    def fit(self, df):
        """Fit the preprocessor on the training dataframe."""
        df_copy = df.copy()
        
        # 1. Learn medians and modes for imputation
        for col in self.numeric_cols:
            if col in df_copy.columns:
                self.medians[col] = df_copy[col].median()
            else:
                self.medians[col] = 0.0
                
        for col in self.categorical_cols:
            if col in df_copy.columns:
                # Get the mode or default to first category if empty
                modes = df_copy[col].mode()
                self.modes[col] = modes[0] if not modes.empty else list(self.mappings[col].keys())[0]
            else:
                self.modes[col] = list(self.mappings[col].keys())[0]

        # 2. Impute missing values and find outlier bounds
        for col in self.numeric_cols:
            if col in df_copy.columns:
                df_copy[col] = df_copy[col].fillna(self.medians[col])
                
                # Outlier detection bounds (IQR)
                q1 = df_copy[col].quantile(0.25)
                q3 = df_copy[col].quantile(0.75)
                iqr = q3 - q1
                self.iqr_bounds[col] = (q1 - 1.5 * iqr, q3 + 1.5 * iqr)
                
                # Cap outliers for learning proper scaling parameters
                low, high = self.iqr_bounds[col]
                capped = df_copy[col].clip(low, high)
                
                self.means[col] = capped.mean()
                self.stds[col] = capped.std() if capped.std() > 0 else 1.0

        for col in self.categorical_cols:
            if col in df_copy.columns:
                df_copy[col] = df_copy[col].fillna(self.modes[col])

        # Save feature column names (excluding target columns)
        self.feature_columns_ = [c for c in df_copy.columns if c in self.numeric_cols + self.categorical_cols]
        return self

    def transform(self, df):
        """Apply preprocessing, encoding, and scaling to the dataframe."""
        df_copy = df.copy()
        
        # 1. Drop duplicates (only during training, which would be handled, but clean here if training)
        # Note: If it's a single prediction, drop_duplicates does nothing.
        
        # 2. Missing values imputation
        for col in self.numeric_cols:
            if col in df_copy.columns:
                df_copy[col] = pd.to_numeric(df_copy[col], errors='coerce')
                df_copy[col] = df_copy[col].fillna(self.medians.get(col, 0.0))
            else:
                df_copy[col] = self.medians.get(col, 0.0)
                
        for col in self.categorical_cols:
            if col in df_copy.columns:
                df_copy[col] = df_copy[col].astype(str).str.lower().str.strip()
                df_copy[col] = df_copy[col].fillna(self.modes.get(col, ''))
            else:
                df_copy[col] = self.modes.get(col, '')

        # 3. Outlier capping for numerical features
        for col in self.numeric_cols:
            if col in self.iqr_bounds:
                low, high = self.iqr_bounds[col]
                df_copy[col] = df_copy[col].clip(low, high)

        # 4. Encoding categorical features
        for col in self.categorical_cols:
            mapping = self.mappings[col]
            default_val = list(mapping.values())[0]
            # Map values, default to standard mapping if value is unknown
            df_copy[col] = df_copy[col].map(mapping).fillna(default_val).astype(int)

        # 5. Standard Scaling for numerical features
        for col in self.numeric_cols:
            mean = self.means.get(col, 0.0)
            std = self.stds.get(col, 1.0)
            df_copy[col] = (df_copy[col] - mean) / std

        # Return only the preprocessed feature columns in consistent order
        return df_copy[self.feature_columns_]

    def fit_transform(self, df):
        return self.fit(df).transform(df)
