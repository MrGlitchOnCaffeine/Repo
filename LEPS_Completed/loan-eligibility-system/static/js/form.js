// Loan Eligibility Prediction System
// Form navigation, validation, and submission

(function () {
    'use strict';

    function init() {

        var totalSections = 4;

        // --------------------------------------------------------
        // Show a specific section, hide all others
        // --------------------------------------------------------
        function showSection(number) {
            for (var i = 1; i <= totalSections; i++) {
                var section = document.getElementById('section-' + i);
                var indicator = document.getElementById('step-indicator-' + i);

                if (section) {
                    section.style.display = (i === number) ? 'block' : 'none';
                }

                if (indicator) {
                    indicator.classList.remove('active', 'completed');
                    if (i < number) {
                        indicator.classList.add('completed');
                    } else if (i === number) {
                        indicator.classList.add('active');
                    }
                }
            }
            window.scrollTo({ top: 0, behavior: 'smooth' });
        }

        // --------------------------------------------------------
        // Show error banner
        // --------------------------------------------------------
        function showErrors(errors) {
            var banner = document.getElementById('form-error-banner');
            var text = document.getElementById('form-error-text');
            if (!banner || !text) return;
            if (errors.length === 0) {
                banner.style.display = 'none';
                return;
            }
            text.textContent = errors.join(' ');
            banner.style.display = 'block';
            banner.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }

        function clearErrors() {
            var banner = document.getElementById('form-error-banner');
            if (banner) banner.style.display = 'none';
        }

        // --------------------------------------------------------
        // Age calculator
        // --------------------------------------------------------
        function calculateAge(dobString) {
            var dob = new Date(dobString);
            var today = new Date();
            var age = today.getFullYear() - dob.getFullYear();
            var m = today.getMonth() - dob.getMonth();
            if (m < 0 || (m === 0 && today.getDate() < dob.getDate())) {
                age--;
            }
            return age;
        }

        // --------------------------------------------------------
        // Section validators
        // --------------------------------------------------------
        function validateSection1() {
            var errors = [];

            var fullName = document.getElementById('full_name');
            if (!fullName || !fullName.value.trim()) {
                errors.push('Full name is required.');
            }

            var dob = document.getElementById('date_of_birth');
            if (!dob || !dob.value) {
                errors.push('Date of birth is required.');
            } else {
                var age = calculateAge(dob.value);
                if (age < 18 || age > 65) {
                    errors.push('You must be between 18 and 65 years of age.');
                }
            }

            var gender = document.getElementById('gender');
            if (!gender || !gender.value) {
                errors.push('Please select your gender.');
            }

            var marital = document.getElementById('marital_status');
            if (!marital || !marital.value) {
                errors.push('Please select your marital status.');
            }

            var education = document.getElementById('education_level');
            if (!education || !education.value) {
                errors.push('Please select your education level.');
            }

            return errors;
        }

        function validateSection2() {
            var errors = [];

            var employment = document.getElementById('employment_type');
            if (!employment || !employment.value) {
                errors.push('Please select your employment status.');
            }

            var income = document.getElementById('monthly_income');
            if (!income || income.value === '') {
                errors.push('Monthly income is required.');
            } else if (parseFloat(income.value) < 0) {
                errors.push('Monthly income cannot be a negative number.');
            }

            return errors;
        }

        function validateSection3() {
            var errors = [];

            var bvn = document.getElementById('bvn_number');
            if (!bvn || !bvn.value.trim()) {
                errors.push('BVN number is required.');
            } else if (!/^\d{11}$/.test(bvn.value.trim())) {
                errors.push('BVN must be exactly 11 digits.');
            }

            var nin = document.getElementById('nin_number');
            if (!nin || !nin.value.trim()) {
                errors.push('NIN number is required.');
            } else if (!/^\d{11}$/.test(nin.value.trim())) {
                errors.push('NIN must be exactly 11 digits.');
            }

            var address = document.getElementById('address');
            if (!address || !address.value.trim()) {
                errors.push('Home address is required.');
            }

            var city = document.getElementById('city');
            if (!city || !city.value.trim()) {
                errors.push('City is required.');
            }

            return errors;
        }

        function validateSection4() {
            var errors = [];

            var loanAmount = document.getElementById('loan_amount_requested');
            if (!loanAmount || loanAmount.value === '') {
                errors.push('Loan amount is required.');
            } else {
                var amt = parseFloat(loanAmount.value);
                if (amt < 10000 || amt > 2000000) {
                    errors.push('Loan amount must be between \u20a610,000 and \u20a62,000,000.');
                }
            }

            var tenure = document.getElementById('loan_tenure_months');
            if (!tenure || tenure.value === '') {
                errors.push('Repayment period is required.');
            } else {
                var t = parseInt(tenure.value);
                if (t < 1 || t > 36) {
                    errors.push('Repayment period must be between 1 and 36 months.');
                }
            }

            var defaultsYes = document.getElementById('defaults_yes');
            if (defaultsYes && defaultsYes.checked) {
                var existingAmount = document.getElementById('existing_loan_amount');
                if (!existingAmount || existingAmount.value === '' || parseFloat(existingAmount.value) < 0) {
                    errors.push('Please enter your outstanding loan amount.');
                }
            }

            return errors;
        }

        // --------------------------------------------------------
        // Wire up Next buttons
        // --------------------------------------------------------
        var next1 = document.getElementById('next-1');
        if (next1) {
            next1.addEventListener('click', function () {
                clearErrors();
                var errors = validateSection1();
                if (errors.length > 0) {
                    showErrors(errors);
                    return;
                }
                showSection(2);
            });
        }

        var next2 = document.getElementById('next-2');
        if (next2) {
            next2.addEventListener('click', function () {
                clearErrors();
                var errors = validateSection2();
                if (errors.length > 0) {
                    showErrors(errors);
                    return;
                }
                showSection(3);
            });
        }

        var next3 = document.getElementById('next-3');
        if (next3) {
            next3.addEventListener('click', function () {
                clearErrors();
                var errors = validateSection3();
                if (errors.length > 0) {
                    showErrors(errors);
                    return;
                }
                showSection(4);
            });
        }

        // --------------------------------------------------------
        // Wire up Back buttons
        // --------------------------------------------------------
        var back2 = document.getElementById('back-2');
        if (back2) back2.addEventListener('click', function () { clearErrors(); showSection(1); });

        var back3 = document.getElementById('back-3');
        if (back3) back3.addEventListener('click', function () { clearErrors(); showSection(2); });

        var back4 = document.getElementById('back-4');
        if (back4) back4.addEventListener('click', function () { clearErrors(); showSection(3); });

        // --------------------------------------------------------
        // Toggle existing loan amount field
        // --------------------------------------------------------
        var defaultsYes = document.getElementById('defaults_yes');
        var defaultsNo = document.getElementById('defaults_no');
        var existingWrapper = document.getElementById('existing_loan_amount_wrapper');
        var existingInput = document.getElementById('existing_loan_amount');

        if (defaultsYes) {
            defaultsYes.addEventListener('change', function () {
                if (existingWrapper) existingWrapper.style.display = 'block';
                if (existingInput) existingInput.required = true;
            });
        }

        if (defaultsNo) {
            defaultsNo.addEventListener('change', function () {
                if (existingWrapper) existingWrapper.style.display = 'none';
                if (existingInput) {
                    existingInput.required = false;
                    existingInput.value = '';
                }
            });
        }

        // --------------------------------------------------------
        // Form submission
        // --------------------------------------------------------
        var form = document.getElementById('loanApplicationForm');
        if (form) {
            form.addEventListener('submit', function (e) {
                e.preventDefault();
                clearErrors();

                var errors = validateSection4();
                if (errors.length > 0) {
                    showErrors(errors);
                    return;
                }

                var submitBtn = document.getElementById('submit-btn');
                var submitText = document.getElementById('submit-text');
                var submitSpinner = document.getElementById('submit-spinner');

                if (submitBtn) submitBtn.disabled = true;
                if (submitText) submitText.textContent = 'Processing...';
                if (submitSpinner) submitSpinner.style.display = 'inline-block';

                var csrfToken = form.querySelector('[name="csrf_token"]');

                var defaultsYesEl = document.getElementById('defaults_yes');

                var formData = {
                    full_name: document.getElementById('full_name').value.trim(),
                    date_of_birth: document.getElementById('date_of_birth').value,
                    gender: document.getElementById('gender').value,
                    marital_status: document.getElementById('marital_status').value,
                    education_level: document.getElementById('education_level').value,
                    employment_type: document.getElementById('employment_type').value,
                    monthly_income: document.getElementById('monthly_income').value,
                    bvn_number: document.getElementById('bvn_number').value.trim(),
                    nin_number: document.getElementById('nin_number').value.trim(),
                    address: document.getElementById('address').value.trim(),
                    city: document.getElementById('city').value.trim(),
                    loan_amount_requested: document.getElementById('loan_amount_requested').value,
                    loan_tenure_months: document.getElementById('loan_tenure_months').value,
                    existing_loan_defaults: (defaultsYesEl && defaultsYesEl.checked) ? '1' : '0',
                    existing_loan_amount: document.getElementById('existing_loan_amount').value || '0'
                };

                fetch('/predict', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': csrfToken ? csrfToken.value : ''
                    },
                    body: JSON.stringify(formData)
                })
                .then(function (response) { return response.json(); })
                .then(function (data) {
                    if (data.error) {
                        showErrors([data.error]);
                        if (submitBtn) submitBtn.disabled = false;
                        if (submitText) submitText.textContent = 'Check My Eligibility';
                        if (submitSpinner) submitSpinner.style.display = 'none';
                        return;
                    }
                    window.location.href = '/result/' + data.application_id;
                })
                .catch(function () {
                    showErrors(['An error occurred. Please try again.']);
                    if (submitBtn) submitBtn.disabled = false;
                    if (submitText) submitText.textContent = 'Check My Eligibility';
                    if (submitSpinner) submitSpinner.style.display = 'none';
                });
            });
        }

        // --------------------------------------------------------
        // Initialise - show section 1 on load
        // --------------------------------------------------------
        showSection(1);
    }

    // Run after DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }

}());
