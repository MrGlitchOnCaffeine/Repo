// Loan Eligibility Prediction System
// Result page: gauge animation and PDF download

document.addEventListener('DOMContentLoaded', function () {

    // --------------------------------------------------------
    // Gauge animation
    // --------------------------------------------------------

    var gaugeFill = document.querySelector('.gauge-fill');
    var gaugeValueEl = document.getElementById('gauge-value');

    if (gaugeFill && gaugeValueEl) {
        var score = parseFloat(gaugeFill.getAttribute('data-score')) || 0;
        var predictedClass = gaugeFill.getAttribute('data-class') || '';

        var circumference = 314;

        // Colour based on result
        if (predictedClass === 'Eligible') {
            gaugeFill.style.stroke = '#4A7C3C';
        } else if (predictedClass === 'Not Eligible') {
            gaugeFill.style.stroke = '#B5483A';
        } else {
            gaugeFill.style.stroke = '#C9A227';
        }

        // Animate from 0 to the actual score
        var duration = 1200;
        var startTime = null;

        function animateGauge(timestamp) {
            if (!startTime) startTime = timestamp;
            var elapsed = timestamp - startTime;
            var progress = Math.min(elapsed / duration, 1);
            var eased = 1 - Math.pow(1 - progress, 3);

            var currentScore = score * eased;
            var offset = circumference - (circumference * currentScore / 100);
            gaugeFill.style.strokeDashoffset = offset;
            gaugeValueEl.textContent = Math.round(currentScore) + '%';

            if (progress < 1) {
                requestAnimationFrame(animateGauge);
            }
        }

        requestAnimationFrame(animateGauge);
    }

    // --------------------------------------------------------
    // PDF download using the browser print dialog
    // --------------------------------------------------------

    var downloadBtn = document.getElementById('download-pdf-btn');
    if (downloadBtn) {
        downloadBtn.addEventListener('click', function () {
            window.print();
        });
    }

});
