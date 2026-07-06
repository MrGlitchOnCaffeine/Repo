import os
import numpy as np
import pandas as pd

np.random.seed(42)

NUM_RECORDS = 10000


def generate_dataset():
    age = np.random.randint(18, 66, NUM_RECORDS)

    gender = np.random.choice(['Male', 'Female'], NUM_RECORDS, p=[0.55, 0.45])

    education_level = np.random.choice(
        ['Primary', 'Secondary', 'Tertiary', 'Postgraduate'],
        NUM_RECORDS,
        p=[0.10, 0.35, 0.40, 0.15]
    )

    employment_type = np.random.choice(
        ['Salaried', 'Self-Employed', 'Unemployed'],
        NUM_RECORDS,
        p=[0.50, 0.35, 0.15]
    )

    monthly_income = np.where(
        employment_type == 'Unemployed',
        np.random.randint(0, 20000, NUM_RECORDS),
        np.where(
            employment_type == 'Salaried',
            np.random.randint(50000, 1000001, NUM_RECORDS),
            np.random.randint(30000, 700001, NUM_RECORDS)
        )
    )

    bvn_registered = np.where(
        employment_type == 'Unemployed',
        np.random.choice([1, 0], NUM_RECORDS, p=[0.40, 0.60]),
        np.random.choice([1, 0], NUM_RECORDS, p=[0.85, 0.15])
    )

    nin_registered = np.where(
        employment_type == 'Unemployed',
        np.random.choice([1, 0], NUM_RECORDS, p=[0.35, 0.65]),
        np.random.choice([1, 0], NUM_RECORDS, p=[0.80, 0.20])
    )

    existing_loan_defaults = np.where(
        monthly_income < 40000,
        np.random.choice([1, 0], NUM_RECORDS, p=[0.55, 0.45]),
        np.random.choice([1, 0], NUM_RECORDS, p=[0.15, 0.85])
    )

    existing_loan_amount = np.where(
        existing_loan_defaults == 1,
        np.random.randint(50000, 500001, NUM_RECORDS),
        np.random.randint(0, 200001, NUM_RECORDS)
    )

    loan_amount_requested = np.random.randint(10000, 2000001, NUM_RECORDS)

    loan_tenure_months = np.random.randint(1, 37, NUM_RECORDS)

    # Label generation
    loan_to_income_ratio = np.where(
        monthly_income > 0,
        loan_amount_requested / monthly_income,
        999
    )

    eligible = np.where(
        (employment_type == 'Unemployed') |
        (existing_loan_defaults == 1) |
        (bvn_registered == 0) |
        (nin_registered == 0) |
        (monthly_income < 30000) |
        (loan_to_income_ratio > 10),
        0,
        np.where(
            (monthly_income >= 50000) &
            (bvn_registered == 1) &
            (nin_registered == 1) &
            (existing_loan_defaults == 0) &
            (loan_to_income_ratio <= 6),
            1,
            # Borderline cases - add realistic noise
            np.random.choice([0, 1], NUM_RECORDS, p=[0.45, 0.55])
        )
    )

    df = pd.DataFrame({
        'age': age,
        'gender': gender,
        'education_level': education_level,
        'employment_type': employment_type,
        'monthly_income': monthly_income,
        'bvn_registered': bvn_registered,
        'nin_registered': nin_registered,
        'existing_loan_defaults': existing_loan_defaults,
        'existing_loan_amount': existing_loan_amount,
        'loan_amount_requested': loan_amount_requested,
        'loan_tenure_months': loan_tenure_months,
        'eligible': eligible
    })

    return df


if __name__ == '__main__':
    df = generate_dataset()

    output_path = os.path.join(
        os.path.dirname(__file__), '..', '..', 'data', 'loan_dataset.csv'
    )
    output_path = os.path.abspath(output_path)

    df.to_csv(output_path, index=False)

    total = len(df)
    eligible_count = df['eligible'].sum()
    not_eligible_count = total - eligible_count

    print(f'Dataset generated: {total} records')
    print(f'Eligible:          {eligible_count} ({eligible_count / total * 100:.1f}%)')
    print(f'Not Eligible:      {not_eligible_count} ({not_eligible_count / total * 100:.1f}%)')
    print(f'Saved to:          {output_path}')
