from datetime import date


VALID_GENDERS = ['Male', 'Female']
VALID_MARITAL_STATUSES = ['Single', 'Married', 'Divorced', 'Widowed']
VALID_EDUCATION_LEVELS = ['Primary', 'Secondary', 'Tertiary', 'Postgraduate']
VALID_EMPLOYMENT_TYPES = ['Salaried', 'Self-Employed', 'Unemployed']

MIN_LOAN = 10000
MAX_LOAN = 2000000
MIN_TENURE = 1
MAX_TENURE = 36
MIN_AGE = 18
MAX_AGE = 65


def calculate_age(date_of_birth_str):
    try:
        dob = date.fromisoformat(date_of_birth_str)
        today = date.today()
        age = today.year - dob.year - (
            (today.month, today.day) < (dob.month, dob.day)
        )
        return age
    except (ValueError, TypeError):
        return None


def validate_application(form_data):
    errors = []

    # Section 1: Personal Details
    full_name = form_data.get('full_name', '').strip()
    if not full_name:
        errors.append('Full name is required.')

    date_of_birth = form_data.get('date_of_birth', '').strip()
    if not date_of_birth:
        errors.append('Date of birth is required.')
    else:
        age = calculate_age(date_of_birth)
        if age is None:
            errors.append('Date of birth is not valid.')
        elif age < MIN_AGE or age > MAX_AGE:
            errors.append(
                f'Applicant must be between {MIN_AGE} and {MAX_AGE} years of age.'
            )

    gender = form_data.get('gender', '').strip()
    if gender not in VALID_GENDERS:
        errors.append('Please select a valid gender.')

    marital_status = form_data.get('marital_status', '').strip()
    if marital_status not in VALID_MARITAL_STATUSES:
        errors.append('Please select a valid marital status.')

    education_level = form_data.get('education_level', '').strip()
    if education_level not in VALID_EDUCATION_LEVELS:
        errors.append('Please select a valid education level.')

    # Section 2: Employment and Income
    employment_type = form_data.get('employment_type', '').strip()
    if employment_type not in VALID_EMPLOYMENT_TYPES:
        errors.append('Please select a valid employment status.')

    monthly_income_raw = form_data.get('monthly_income', '')
    try:
        monthly_income = float(monthly_income_raw)
        if monthly_income < 0:
            errors.append('Monthly income cannot be a negative number.')
    except (ValueError, TypeError):
        errors.append('Monthly income must be a valid number.')
        monthly_income = None

    # Section 3: Identity Verification
    bvn_number = form_data.get('bvn_number', '').strip()
    if not bvn_number:
        errors.append('BVN number is required.')
    elif not bvn_number.isdigit() or len(bvn_number) != 11:
        errors.append('BVN must be exactly 11 digits.')

    nin_number = form_data.get('nin_number', '').strip()
    if not nin_number:
        errors.append('NIN number is required.')
    elif not nin_number.isdigit() or len(nin_number) != 11:
        errors.append('NIN must be exactly 11 digits.')

    address = form_data.get('address', '').strip()
    if not address:
        errors.append('Home address is required.')

    city = form_data.get('city', '').strip()
    if not city:
        errors.append('City is required.')

    # Section 4: Loan Request
    loan_amount_raw = form_data.get('loan_amount_requested', '')
    try:
        loan_amount = float(loan_amount_raw)
        if loan_amount < MIN_LOAN or loan_amount > MAX_LOAN:
            errors.append(
                f'Loan amount must be between '
                f'\u20a6{MIN_LOAN:,} and \u20a6{MAX_LOAN:,}.'
            )
    except (ValueError, TypeError):
        errors.append('Loan amount must be a valid number.')
        loan_amount = None

    tenure_raw = form_data.get('loan_tenure_months', '')
    try:
        tenure = int(tenure_raw)
        if tenure < MIN_TENURE or tenure > MAX_TENURE:
            errors.append(
                f'Repayment period must be between {MIN_TENURE} and {MAX_TENURE} months.'
            )
    except (ValueError, TypeError):
        errors.append('Repayment period must be a valid number.')
        tenure = None

    existing_defaults_raw = form_data.get('existing_loan_defaults', '0')
    try:
        existing_defaults = int(existing_defaults_raw)
        if existing_defaults not in [0, 1]:
            errors.append('Please indicate whether you have existing loan defaults.')
    except (ValueError, TypeError):
        errors.append('Please indicate whether you have existing loan defaults.')
        existing_defaults = 0

    existing_loan_amount_raw = form_data.get('existing_loan_amount', '0') or '0'
    try:
        existing_loan_amount = float(existing_loan_amount_raw)
        if existing_loan_amount < 0:
            errors.append('Outstanding loan amount cannot be a negative number.')
    except (ValueError, TypeError):
        errors.append('Outstanding loan amount must be a valid number.')
        existing_loan_amount = 0

    if errors:
        return {'valid': False, 'errors': errors}

    age = calculate_age(date_of_birth)

    return {
        'valid': True,
        'errors': [],
        'data': {
            'full_name': full_name,
            'date_of_birth': date_of_birth,
            'age': age,
            'gender': gender,
            'marital_status': marital_status,
            'education_level': education_level,
            'employment_type': employment_type,
            'monthly_income': monthly_income,
            'bvn_number': bvn_number,
            'nin_number': nin_number,
            'bvn_registered': 1,
            'nin_registered': 1,
            'address': address,
            'city': city,
            'loan_amount_requested': loan_amount,
            'loan_tenure_months': tenure,
            'existing_loan_defaults': existing_defaults,
            'existing_loan_amount': existing_loan_amount
        }
    }
