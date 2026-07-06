import os
import joblib
import numpy as np

MODEL_PATH = os.path.join(os.path.dirname(__file__), 'model.pkl')
SCALER_PATH = os.path.join(os.path.dirname(__file__), 'scaler.pkl')
ENCODER_PATH = os.path.join(os.path.dirname(__file__), 'encoders.pkl')

_model = None
_scaler = None
_encoders = None


def _load_artifacts():
    global _model, _scaler, _encoders

    if _model is None:
        _model = joblib.load(MODEL_PATH)

    if _scaler is None:
        _scaler = joblib.load(SCALER_PATH)

    if _encoders is None:
        _encoders = joblib.load(ENCODER_PATH)


def predict_eligibility(form_data: dict) -> dict:
    """
    Takes cleaned form data and returns a prediction result.

    Expected keys in form_data:
        age, gender, education_level, employment_type,
        monthly_income, bvn_registered, nin_registered,
        existing_loan_defaults, existing_loan_amount,
        loan_amount_requested, loan_tenure_months

    Returns:
        dict with keys: score (float 0-1), eligible (int 0 or 1)
    """
    _load_artifacts()

    edu_order = _encoders['education_order']
    gender_enc = _encoders['gender']
    emp_enc = _encoders['employment']

    gender_encoded = int(gender_enc.transform([form_data['gender']])[0])
    education_encoded = edu_order.get(form_data['education_level'], 0)
    employment_encoded = int(emp_enc.transform([form_data['employment_type']])[0])

    monthly_income = float(form_data['monthly_income'])
    loan_amount = float(form_data['loan_amount_requested'])

    loan_to_income_ratio = (
        loan_amount / monthly_income if monthly_income > 0 else 999
    )

    feature_vector = np.array([[
        int(form_data['age']),
        gender_encoded,
        education_encoded,
        employment_encoded,
        monthly_income,
        int(form_data['bvn_registered']),
        int(form_data['nin_registered']),
        int(form_data['existing_loan_defaults']),
        float(form_data['existing_loan_amount']),
        loan_amount,
        int(form_data['loan_tenure_months']),
        loan_to_income_ratio
    ]])

    scaled = _scaler.transform(feature_vector)
    probability = float(_model.predict_proba(scaled)[0][1])
    prediction = int(_model.predict(scaled)[0])

    return {
        'score': round(probability, 4),
        'eligible': prediction
    }
