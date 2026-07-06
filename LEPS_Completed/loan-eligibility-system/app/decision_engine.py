MIN_INCOME = 30000
MAX_LOAN_TO_INCOME_RATIO = 10
ELIGIBLE_THRESHOLD = 0.55
REVIEW_THRESHOLD = 0.40

MIN_LOAN_ESTIMATE = 10000
MAX_LOAN_ESTIMATE = 2000000


def evaluate(ml_score: float, data: dict) -> dict:
    """
    Applies hard business rules on top of the ML score.
    Returns a structured result dictionary.

    Possible predicted_class values:
        Eligible      - passes all rules and score >= 55%
        Not Eligible  - fails at least one rule or score < 40%
        Under Review  - passes all rules but score is 40% to 54%
    """

    denial_reason = None
    predicted_class = None

    # Rule 1: Employment status
    if data.get('employment_type') == 'Unemployed':
        predicted_class = 'Not Eligible'
        denial_reason = 'Your employment status does not meet our requirements.'

    # Rule 2: Existing loan defaults
    elif int(data.get('existing_loan_defaults', 0)) == 1:
        predicted_class = 'Not Eligible'
        denial_reason = 'A history of loan defaults affects your eligibility.'

    # Rule 3: BVN registration
    elif int(data.get('bvn_registered', 1)) == 0:
        predicted_class = 'Not Eligible'
        denial_reason = 'A registered BVN is required to apply.'

    # Rule 4: NIN registration
    elif int(data.get('nin_registered', 1)) == 0:
        predicted_class = 'Not Eligible'
        denial_reason = 'A registered NIN is required to apply.'

    # Rule 5: Minimum income
    elif float(data.get('monthly_income', 0)) < MIN_INCOME:
        predicted_class = 'Not Eligible'
        denial_reason = 'Your income does not meet the minimum requirement.'

    # Rule 6: Loan to income ratio
    else:
        monthly_income = float(data.get('monthly_income', 1))
        loan_amount = float(data.get('loan_amount_requested', 0))
        ratio = loan_amount / monthly_income if monthly_income > 0 else 999

        if ratio > MAX_LOAN_TO_INCOME_RATIO:
            predicted_class = 'Not Eligible'
            denial_reason = (
                'The requested amount exceeds what your income supports.'
            )

        # Rule 7: ML score thresholds
        elif ml_score < REVIEW_THRESHOLD:
            predicted_class = 'Not Eligible'
            denial_reason = (
                'Your overall financial profile does not meet our threshold.'
            )

        elif ml_score < ELIGIBLE_THRESHOLD:
            predicted_class = 'Under Review'
            denial_reason = (
                'Your application requires manual review by a loan officer.'
            )

        else:
            predicted_class = 'Eligible'

    # Estimated loan amount (Eligible applicants only)
    estimated_loan_amount = None
    if predicted_class == 'Eligible':
        monthly_income = float(data.get('monthly_income', 0))
        annual_income = monthly_income * 12
        multiplier = min(ml_score * 2, 1.5)
        raw_estimate = annual_income * multiplier
        rounded = round(raw_estimate / 1000) * 1000
        estimated_loan_amount = max(
            MIN_LOAN_ESTIMATE, min(MAX_LOAN_ESTIMATE, rounded)
        )

    # Key factors
    key_factors = _build_key_factors(data, ml_score)

    return {
        'predicted_class': predicted_class,
        'probability_score': round(ml_score, 4),
        'eligibility_percentage': round(ml_score * 100, 1),
        'estimated_loan_amount': estimated_loan_amount,
        'denial_reason': denial_reason,
        'key_factors': key_factors
    }


def _build_key_factors(data: dict, ml_score: float) -> list:
    """
    Returns a short list of the top factors that influenced the result.
    """
    factors = []

    monthly_income = float(data.get('monthly_income', 0))
    if monthly_income >= 100000:
        factors.append('Strong monthly income')
    elif monthly_income >= 50000:
        factors.append('Adequate monthly income')
    else:
        factors.append('Low monthly income')

    if int(data.get('existing_loan_defaults', 0)) == 0:
        factors.append('No history of loan defaults')
    else:
        factors.append('Existing loan defaults recorded')

    if int(data.get('bvn_registered', 1)) == 1:
        factors.append('BVN registered')

    if int(data.get('nin_registered', 1)) == 1:
        factors.append('NIN registered')

    emp = data.get('employment_type', '')
    if emp == 'Salaried':
        factors.append('Stable salaried employment')
    elif emp == 'Self-Employed':
        factors.append('Self-employed status')
    elif emp == 'Unemployed':
        factors.append('No active employment')

    if ml_score >= 0.75:
        factors.append('High overall eligibility score')
    elif ml_score >= 0.55:
        factors.append('Satisfactory eligibility score')
    elif ml_score >= 0.40:
        factors.append('Borderline eligibility score')
    else:
        factors.append('Low eligibility score')

    return factors[:5]
