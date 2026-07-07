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

        if (predictedClass === 'Eligible') {
            gaugeFill.style.stroke = '#2D6B40';
        } else if (predictedClass === 'Not Eligible') {
            gaugeFill.style.stroke = '#8C2A1E';
        } else {
            gaugeFill.style.stroke = '#7A5200';
        }

        var duration = 1400;
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
            if (progress < 1) requestAnimationFrame(animateGauge);
        }

        // Delay gauge start slightly so CSS reveal animation plays first
        setTimeout(function () {
            requestAnimationFrame(animateGauge);
        }, 350);
    }

    // --------------------------------------------------------
    // PDF download via browser print
    // --------------------------------------------------------
    var downloadBtn = document.getElementById('download-pdf-btn');
    if (downloadBtn) {
        downloadBtn.addEventListener('click', function () {
            window.print();
        });

        downloadBtn.addEventListener('touchend', function (e) {
            e.preventDefault();
            window.print();
        }, { passive: false });
    }

});
