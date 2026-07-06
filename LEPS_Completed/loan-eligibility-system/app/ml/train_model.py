import os
import joblib
import numpy as np
import pandas as pd

from sklearn.model_selection import train_test_split, cross_val_score, GridSearchCV
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score,
    f1_score, roc_auc_score, confusion_matrix, classification_report
)

try:
    from xgboost import XGBClassifier
    XGBOOST_AVAILABLE = True
except ImportError:
    XGBOOST_AVAILABLE = False

try:
    from imblearn.over_sampling import SMOTE
    SMOTE_AVAILABLE = True
except ImportError:
    SMOTE_AVAILABLE = False


DATA_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'loan_dataset.csv')
)
MODEL_PATH = os.path.join(os.path.dirname(__file__), 'model.pkl')
SCALER_PATH = os.path.join(os.path.dirname(__file__), 'scaler.pkl')
ENCODER_PATH = os.path.join(os.path.dirname(__file__), 'encoders.pkl')


def load_and_preprocess(path):
    df = pd.read_csv(path)

    # Encode gender
    gender_enc = LabelEncoder()
    df['gender_encoded'] = gender_enc.fit_transform(df['gender'])

    # Encode education level (ordered)
    edu_order = {'Primary': 0, 'Secondary': 1, 'Tertiary': 2, 'Postgraduate': 3}
    df['education_encoded'] = df['education_level'].map(edu_order)

    # Encode employment type
    emp_enc = LabelEncoder()
    df['employment_encoded'] = emp_enc.fit_transform(df['employment_type'])

    # Feature engineering
    df['loan_to_income_ratio'] = np.where(
        df['monthly_income'] > 0,
        df['loan_amount_requested'] / df['monthly_income'],
        999
    )

    feature_columns = [
        'age',
        'gender_encoded',
        'education_encoded',
        'employment_encoded',
        'monthly_income',
        'bvn_registered',
        'nin_registered',
        'existing_loan_defaults',
        'existing_loan_amount',
        'loan_amount_requested',
        'loan_tenure_months',
        'loan_to_income_ratio'
    ]

    X = df[feature_columns]
    y = df['eligible']

    encoders = {
        'gender': gender_enc,
        'employment': emp_enc,
        'education_order': edu_order,
        'feature_columns': feature_columns
    }

    return X, y, encoders


def evaluate_model(name, model, X_test, y_test):
    y_pred = model.predict(X_test)
    y_prob = model.predict_proba(X_test)[:, 1]

    print(f'\n{name}')
    print('-' * 40)
    print(f'Accuracy:  {accuracy_score(y_test, y_pred):.4f}')
    print(f'Precision: {precision_score(y_test, y_pred):.4f}')
    print(f'Recall:    {recall_score(y_test, y_pred):.4f}')
    print(f'F1 Score:  {f1_score(y_test, y_pred):.4f}')
    print(f'ROC-AUC:   {roc_auc_score(y_test, y_prob):.4f}')
    print(f'\nConfusion Matrix:')
    cm = confusion_matrix(y_test, y_pred)
    print(f'  True Negative:  {cm[0][0]}  |  False Positive: {cm[0][1]}')
    print(f'  False Negative: {cm[1][0]}  |  True Positive:  {cm[1][1]}')

    return {
        'accuracy': accuracy_score(y_test, y_pred),
        'f1': f1_score(y_test, y_pred),
        'roc_auc': roc_auc_score(y_test, y_prob)
    }


def train():
    print('Loading dataset...')
    X, y, encoders = load_and_preprocess(DATA_PATH)

    print(f'Dataset loaded: {len(X)} records')
    print(f'Eligible: {y.sum()} | Not Eligible: {(y == 0).sum()}')

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.20, random_state=42, stratify=y
    )

    # Apply SMOTE if available and needed
    if SMOTE_AVAILABLE:
        smote = SMOTE(random_state=42)
        X_train, y_train = smote.fit_resample(X_train, y_train)
        print(f'\nAfter SMOTE - Training set: {len(X_train)} records')

    # Scale features
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    results = {}

    # Model 1: Logistic Regression (baseline)
    print('\nTraining Logistic Regression...')
    lr = LogisticRegression(max_iter=1000, random_state=42)
    lr.fit(X_train_scaled, y_train)
    results['Logistic Regression'] = {
        'model': lr,
        'metrics': evaluate_model('Logistic Regression', lr, X_test_scaled, y_test)
    }

    # Model 2: Random Forest
    print('\nTraining Random Forest...')
    rf_params = {
        'n_estimators': [100, 200],
        'max_depth': [10, 20, None],
        'min_samples_split': [2, 5]
    }
    rf = GridSearchCV(
        RandomForestClassifier(random_state=42),
        rf_params,
        cv=5,
        scoring='f1',
        n_jobs=-1,
        verbose=0
    )
    rf.fit(X_train_scaled, y_train)
    best_rf = rf.best_estimator_
    print(f'Best RF params: {rf.best_params_}')
    results['Random Forest'] = {
        'model': best_rf,
        'metrics': evaluate_model('Random Forest', best_rf, X_test_scaled, y_test)
    }

    # Model 3: XGBoost (if available)
    if XGBOOST_AVAILABLE:
        print('\nTraining XGBoost...')
        xgb_params = {
            'n_estimators': [100, 200],
            'max_depth': [4, 6],
            'learning_rate': [0.05, 0.1]
        }
        xgb = GridSearchCV(
            XGBClassifier(random_state=42, eval_metric='logloss', verbosity=0),
            xgb_params,
            cv=5,
            scoring='f1',
            n_jobs=-1,
            verbose=0
        )
        xgb.fit(X_train_scaled, y_train)
        best_xgb = xgb.best_estimator_
        print(f'Best XGB params: {xgb.best_params_}')
        results['XGBoost'] = {
            'model': best_xgb,
            'metrics': evaluate_model('XGBoost', best_xgb, X_test_scaled, y_test)
        }

    # Select best model by F1 score
    best_name = max(results, key=lambda k: results[k]['metrics']['f1'])
    best_model = results[best_name]['model']

    print(f'\nBest model selected: {best_name}')
    print(f'F1 Score: {results[best_name]["metrics"]["f1"]:.4f}')
    print(f'ROC-AUC:  {results[best_name]["metrics"]["roc_auc"]:.4f}')

    # Save model, scaler, and encoders
    joblib.dump(best_model, MODEL_PATH)
    joblib.dump(scaler, SCALER_PATH)
    joblib.dump(encoders, ENCODER_PATH)

    print(f'\nModel saved to:   {MODEL_PATH}')
    print(f'Scaler saved to:  {SCALER_PATH}')
    print(f'Encoders saved to: {ENCODER_PATH}')
    print('\nTraining complete.')


if __name__ == '__main__':
    train()
