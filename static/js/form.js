// Loan Eligibility Prediction System
// Form navigation, validation, submission, loading overlay

(function () {
    'use strict';

    function init() {
        var totalSections = 4;
        var loadingTimer = null;
        var loadingMessageTimer = null;

        var loadingMessages = [
            'Validating your information...',
            'Preparing your assessment...',
            'Reviewing application details...',
            'Finalizing your results...'
        ];

        // --------------------------------------------------------
        // Loading overlay
        // --------------------------------------------------------
        function showLoading() {
            var overlay = document.getElementById('leps-loading-overlay');
            if (!overlay) return;

            overlay.classList.add('active');

            var label = overlay.querySelector('.loading-label');
            var spinner = overlay.querySelector('.loading-spinner-ring');
            var progress = overlay.querySelector('[data-loading-progress]');
            var progressValue = 0;
            var messageIndex = 0;

            if (label) {
                label.textContent = loadingMessages[0];
            }

            if (spinner) {
                spinner.style.animationPlayState = 'running';
            }

            if (progress) {
                progress.textContent = '0%';
            }

            clearInterval(loadingMessageTimer);
            loadingMessageTimer = setInterval(function () {
                messageIndex = (messageIndex + 1) % loadingMessages.length;
                if (label) {
                    label.textContent = loadingMessages[messageIndex];
                }
            }, 850);

            clearInterval(loadingTimer);
            loadingTimer = setInterval(function () {
                progressValue = Math.min(progressValue + 7, 92);
                if (progress) {
                    progress.textContent = progressValue + '%';
                }
            }, 180);
        }

        function hideLoading() {
            var overlay = document.getElementById('leps-loading-overlay');
            if (overlay) overlay.classList.remove('active');

            clearInterval(loadingTimer);
            clearInterval(loadingMessageTimer);
            loadingTimer = null;
            loadingMessageTimer = null;
        }

        function setSubmitState(isLoading) {
            var form = document.getElementById('loanApplicationForm');
            if (!form) return;

            var submitBtn = form.querySelector('button[type="submit"], input[type="submit"], .btn-submit');
            if (!submitBtn) return;

            if (isLoading) {
                submitBtn.disabled = true;
                submitBtn.dataset.originalText = submitBtn.textContent;
                submitBtn.textContent = 'Checking...';
            } else {
                submitBtn.disabled = false;
                if (submitBtn.dataset.originalText) {
                    submitBtn.textContent = submitBtn.dataset.originalText;
                }
            }
        }

        // --------------------------------------------------------
        // Show section
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
        // Error handling
        // --------------------------------------------------------
        function getFieldWrapper(field) {
            if (!field) return null;
            return field.closest('.mb-3') ||
                field.closest('.form-group') ||
                field.closest('.input-group') ||
                field.parentElement;
        }

        function getOrCreateFieldError(field) {
            var wrapper = getFieldWrapper(field);
            if (!wrapper) return null;

            var existing = wrapper.querySelector('.field-error-message');
            if (existing) return existing;

            var error = document.createElement('div');
            error.className = 'field-error-message';
            error.setAttribute('aria-live', 'polite');
            wrapper.appendChild(error);
            return error;
        }

        function setFieldError(fieldId, message) {
            var field = document.getElementById(fieldId);
            if (!field) return;

            field.classList.add('is-invalid');
            field.setAttribute('aria-invalid', 'true');

            var errorEl = getOrCreateFieldError(field);
            if (errorEl) {
                errorEl.textContent = message;
                errorEl.style.display = 'block';
            }
        }

        function clearFieldError(fieldId) {
            var field = document.getElementById(fieldId);
            if (!field) return;

            field.classList.remove('is-invalid');
            field.removeAttribute('aria-invalid');

            var wrapper = getFieldWrapper(field);
            if (!wrapper) return;

            var errorEl = wrapper.querySelector('.field-error-message');
            if (errorEl) {
                errorEl.textContent = '';
                errorEl.style.display = 'none';
            }
        }

        function clearAllFieldErrors() {
            var fields = document.querySelectorAll('#loanApplicationForm input, #loanApplicationForm select, #loanApplicationForm textarea');

            fields.forEach(function (field) {
                field.classList.remove('is-invalid');
                field.removeAttribute('aria-invalid');
            });

            var errors = document.querySelectorAll('.field-error-message');
            errors.forEach(function (el) {
                el.textContent = '';
                el.style.display = 'none';
            });

            clearErrors();
        }

        function showErrors(errors) {
            var banner = document.getElementById('form-error-banner');
            var text = document.getElementById('form-error-text');
            if (!banner || !text) return;

            if (!errors || errors.length === 0) {
                banner.style.display = 'none';
                return;
            }

            // banner text
            text.textContent = errors.map(function (item) {
                return item.message;
            }).join(' ');

            banner.style.display = 'block';
            banner.scrollIntoView({ behavior: 'smooth', block: 'center' });

            // first invalid field
            var firstError = errors[0];
            if (firstError && firstError.field) {
                var field = document.getElementById(firstError.field);
                if (field) {
                    field.focus({ preventScroll: true });
                    field.scrollIntoView({ behavior: 'smooth', block: 'center' });
                }
            }
        }

        function clearErrors() {
            var banner = document.getElementById('form-error-banner');
            if (banner) banner.style.display = 'none';
        }

        function addValidationError(errors, fieldId, message) {
            errors.push({ field: fieldId, message: message });
            setFieldError(fieldId, message);
        }

        // --------------------------------------------------------
        // Utilities
        // --------------------------------------------------------
        function calculateAge(dobString) {
            var dob = new Date(dobString);
            var today = new Date();
            var age = today.getFullYear() - dob.getFullYear();
            var m = today.getMonth() - dob.getMonth();
            if (m < 0 || (m === 0 && today.getDate() < dob.getDate())) age--;
            return age;
        }

        function onlyDigits(input) {
            if (!input) return;
            input.addEventListener('input', function () {
                var value = input.value.replace(/\D+/g, '');
                if (input.value !== value) {
                    input.value = value;
                }
                clearFieldError(input.id);
            });
        }

        function sanitizeDecimal(input) {
            if (!input) return;
            input.addEventListener('input', function () {
                var raw = input.value.replace(/,/g, '').replace(/[^\d.]/g, '');
                var parts = raw.split('.');
                if (parts.length > 2) {
                    raw = parts[0] + '.' + parts.slice(1).join('');
                }
                input.value = raw;
                clearFieldError(input.id);
            });
        }

        function attachLiveClear(id) {
            var el = document.getElementById(id);
            if (!el) return;
            el.addEventListener('input', function () {
                clearFieldError(id);
                clearErrors();
            });
            el.addEventListener('change', function () {
                clearFieldError(id);
                clearErrors();
            });
        }

        // --------------------------------------------------------
        // Section validators
        // --------------------------------------------------------
        function validateSection1() {
            var errors = [];

            var fullName = document.getElementById('full_name');
            if (!fullName || !fullName.value.trim()) {
                addValidationError(errors, 'full_name', 'Full name is required.');
            } else if (fullName.value.trim().split(/\s+/).length < 2) {
                addValidationError(errors, 'full_name', 'Please enter your full name.');
            }

            var dob = document.getElementById('date_of_birth');
            if (!dob || !dob.value) {
                addValidationError(errors, 'date_of_birth', 'Date of birth is required.');
            } else {
                var age = calculateAge(dob.value);
                if (age < 18 || age > 65) {
                    addValidationError(errors, 'date_of_birth', 'You must be between 18 and 65 years of age.');
                }
            }

            var gender = document.getElementById('gender');
            if (!gender || !gender.value) {
                addValidationError(errors, 'gender', 'Please select your gender.');
            }

            var marital = document.getElementById('marital_status');
            if (!marital || !marital.value) {
                addValidationError(errors, 'marital_status', 'Please select your marital status.');
            }

            var education = document.getElementById('education_level');
            if (!education || !education.value) {
                addValidationError(errors, 'education_level', 'Please select your education level.');
            }

            return errors;
        }

        function validateSection2() {
            var errors = [];

            var employment = document.getElementById('employment_type');
            if (!employment || !employment.value) {
                addValidationError(errors, 'employment_type', 'Please select your employment status.');
            }

            var income = document.getElementById('monthly_income');
            if (!income || income.value.trim() === '') {
                addValidationError(errors, 'monthly_income', 'Monthly income is required.');
            } else {
                var incomeValue = parseFloat(income.value);
                if (isNaN(incomeValue)) {
                    addValidationError(errors, 'monthly_income', 'Monthly income must be a valid number.');
                } else if (incomeValue < 0) {
                    addValidationError(errors, 'monthly_income', 'Monthly income cannot be negative.');
                }
            }

            return errors;
        }

        function validateSection3() {
            var errors = [];

            var bvn = document.getElementById('bvn_number');
            if (!bvn || !bvn.value.trim()) {
                addValidationError(errors, 'bvn_number', 'BVN number is required.');
            } else if (!/^\d{11}$/.test(bvn.value.trim())) {
                addValidationError(errors, 'bvn_number', 'BVN must be exactly 11 digits.');
            }

            var nin = document.getElementById('nin_number');
            if (!nin || !nin.value.trim()) {
                addValidationError(errors, 'nin_number', 'NIN number is required.');
            } else if (!/^\d{11}$/.test(nin.value.trim())) {
                addValidationError(errors, 'nin_number', 'NIN must be exactly 11 digits.');
            }

            var address = document.getElementById('address');
            if (!address || !address.value.trim()) {
                addValidationError(errors, 'address', 'Home address is required.');
            } else if (address.value.trim().length < 10) {
                addValidationError(errors, 'address', 'Please enter a more complete home address.');
            }

            var city = document.getElementById('city');
            if (!city || !city.value.trim()) {
                addValidationError(errors, 'city', 'City is required.');
            } else if (!/^[a-zA-Z\s'-]+$/.test(city.value.trim())) {
                addValidationError(errors, 'city', 'City can only contain letters.');
            }

            return errors;
        }

        function validateSection4() {
            var errors = [];

            var loanAmount = document.getElementById('loan_amount_requested');
            if (!loanAmount || loanAmount.value.trim() === '') {
                addValidationError(errors, 'loan_amount_requested', 'Loan amount is required.');
            } else {
                var amt = parseFloat(loanAmount.value);
                if (isNaN(amt)) {
                    addValidationError(errors, 'loan_amount_requested', 'Loan amount must be a valid number.');
                } else if (amt < 10000 || amt > 2000000) {
                    addValidationError(errors, 'loan_amount_requested', 'Loan amount must be between ₦10,000 and ₦2,000,000.');
                }
            }

            var tenure = document.getElementById('loan_tenure_months');
            if (!tenure || tenure.value.trim() === '') {
                addValidationError(errors, 'loan_tenure_months', 'Repayment period is required.');
            } else {
                var t = parseInt(tenure.value, 10);
                if (isNaN(t)) {
                    addValidationError(errors, 'loan_tenure_months', 'Repayment period must be a valid number.');
                } else if (t < 1 || t > 36) {
                    addValidationError(errors, 'loan_tenure_months', 'Repayment period must be between 1 and 36 months.');
                }
            }

            var defaultsYes = document.getElementById('defaults_yes');
            if (defaultsYes && defaultsYes.checked) {
                var existingAmount = document.getElementById('existing_loan_amount');
                if (!existingAmount || existingAmount.value.trim() === '') {
                    addValidationError(errors, 'existing_loan_amount', 'Please enter your outstanding loan amount.');
                } else {
                    var existingValue = parseFloat(existingAmount.value);
                    if (isNaN(existingValue) || existingValue < 0) {
                        addValidationError(errors, 'existing_loan_amount', 'Outstanding loan amount must be a valid non-negative number.');
                    }
                }
            }

            return errors;
        }

        // --------------------------------------------------------
        // Touch/click helpers
        // --------------------------------------------------------
        function attachHandler(id, fn) {
            var el = document.getElementById(id);
            if (!el) return;

            el.addEventListener('click', function (e) {
                e.preventDefault();
                fn();
            });

            el.addEventListener('touchend', function (e) {
                e.preventDefault();
                fn();
            }, { passive: false });
        }

        // --------------------------------------------------------
        // Next buttons
        // --------------------------------------------------------
        attachHandler('next-1', function () {
            clearAllFieldErrors();
            var errors = validateSection1();
            if (errors.length > 0) { showErrors(errors); return; }
            showSection(2);
        });

        attachHandler('next-2', function () {
            clearAllFieldErrors();
            var errors = validateSection2();
            if (errors.length > 0) { showErrors(errors); return; }
            showSection(3);
        });

        attachHandler('next-3', function () {
            clearAllFieldErrors();
            var errors = validateSection3();
            if (errors.length > 0) { showErrors(errors); return; }
            showSection(4);
        });

        // --------------------------------------------------------
        // Back buttons
        // --------------------------------------------------------
        attachHandler('back-2', function () { clearAllFieldErrors(); showSection(1); });
        attachHandler('back-3', function () { clearAllFieldErrors(); showSection(2); });
        attachHandler('back-4', function () { clearAllFieldErrors(); showSection(3); });

        // --------------------------------------------------------
        // Existing loan amount toggle
        // --------------------------------------------------------
        var defaultsYes = document.getElementById('defaults_yes');
        var defaultsNo = document.getElementById('defaults_no');
        var existingWrapper = document.getElementById('existing_loan_amount_wrapper');
        var existingInput = document.getElementById('existing_loan_amount');

        if (defaultsYes) {
            defaultsYes.addEventListener('change', function () {
                if (existingWrapper) existingWrapper.style.display = 'block';
                if (existingInput) existingInput.required = true;
                clearFieldError('existing_loan_amount');
            });
        }

        if (defaultsNo) {
            defaultsNo.addEventListener('change', function () {
                if (existingWrapper) existingWrapper.style.display = 'none';
                if (existingInput) {
                    existingInput.required = false;
                    existingInput.value = '';
                }
                clearFieldError('existing_loan_amount');
            });
        }

        // --------------------------------------------------------
        // Live validation and input sanitizing
        // --------------------------------------------------------
        attachLiveClear('full_name');
        attachLiveClear('date_of_birth');
        attachLiveClear('gender');
        attachLiveClear('marital_status');
        attachLiveClear('education_level');
        attachLiveClear('employment_type');
        attachLiveClear('monthly_income');
        attachLiveClear('bvn_number');
        attachLiveClear('nin_number');
        attachLiveClear('address');
        attachLiveClear('city');
        attachLiveClear('loan_amount_requested');
        attachLiveClear('loan_tenure_months');
        attachLiveClear('existing_loan_amount');

        onlyDigits(document.getElementById('bvn_number'));
        onlyDigits(document.getElementById('nin_number'));
        onlyDigits(document.getElementById('loan_tenure_months'));
        sanitizeDecimal(document.getElementById('monthly_income'));
        sanitizeDecimal(document.getElementById('loan_amount_requested'));
        sanitizeDecimal(document.getElementById('existing_loan_amount'));

        // --------------------------------------------------------
        // Form submission
        // --------------------------------------------------------
        var form = document.getElementById('loanApplicationForm');
        if (form) {
            form.addEventListener('submit', function (e) {
                e.preventDefault();
                clearAllFieldErrors();

                var errors = validateSection4();
                if (errors.length > 0) {
                    showErrors(errors);
                    return;
                }

                showLoading();
                setSubmitState(true);

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
                .then(function (response) {
                    return response.json().then(function (data) {
                        return {
                            ok: response.ok,
                            status: response.status,
                            data: data
                        };
                    });
                })
                .then(function (result) {
                    if (!result.ok || result.data.error) {
                        hideLoading();
                        setSubmitState(false);
                        showErrors([{ field: null, message: result.data.error || 'An error occurred while submitting your application.' }]);
                        return;
                    }
                    

                    window.location.href = '/application-submitted/' + result.data.application_id;
                })
                .catch(function () {
                    hideLoading();
                    setSubmitState(false);
                    showErrors([{ field: null, message: 'An error occurred. Please try again.' }]);
                });
            });
        }

        // --------------------------------------------------------
        // Init
        // --------------------------------------------------------
        showSection(1);
        clearAllFieldErrors();
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
}());