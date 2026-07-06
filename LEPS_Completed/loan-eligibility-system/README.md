# Loan Eligibility Prediction System

A web-based machine learning application that predicts loan eligibility for applicants in the Nigerian financial sector.

## Overview

This system allows applicants to submit their personal and financial details and receive an instant, data-driven assessment of their loan eligibility. The system uses a trained machine learning model combined with a business rules engine to produce one of three outcomes: Eligible, Not Eligible, or Under Review.

## Features

- Applicant registration and login
- Four-section loan application form
- AI-powered eligibility prediction (Random Forest / XGBoost)
- Animated eligibility score gauge on the result page
- Estimated loan amount for eligible applicants
- PDF download of result via browser print
- Email notification sent to applicant after assessment
- Application history for returning users
- Full admin dashboard with search, filter, status update, and result override
- Automatic admin action logging

## Technology Stack

| Layer | Technology |
|---|---|
| Frontend | HTML5, CSS3, Bootstrap 5, JavaScript |
| Backend | Python, Flask |
| Machine Learning | Scikit-learn, XGBoost, Pandas, NumPy |
| Database | SQLite (development) / PostgreSQL (production) |
| Authentication | Flask-Login |
| Email | Flask-Mail |

## Setup Instructions

1. Clone the repository
2. Install dependencies: `pip install -r requirements.txt`
3. Create a `.env` file using `.env` as a template and fill in your credentials
4. Generate the dataset: `python app/ml/generate_data.py`
5. Train the model: `python app/ml/train_model.py`
6. Start the app: `python run.py`
7. Visit `http://127.0.0.1:5000` in your browser

## Academic Notice

This project is an academic demonstration developed as part of a research portfolio on machine learning applications in the Nigerian financial sector. It does not constitute a licensed financial product or service.
