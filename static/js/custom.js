// static/js/custom.js

// ============================================
// ❌ REMOVED: Auto-dismiss alerts (was hiding forms)
// ============================================

// ============================================
// ENABLE TOOLTIPS
// ============================================
document.addEventListener('DOMContentLoaded', function() {
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function(tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
});

// ============================================
// CONFIRM DELETE
// ============================================
function confirmDelete(message) {
    return confirm(message || 'Are you sure you want to delete this item?');
}

// ============================================
// FORMAT CURRENCY
// ============================================
function formatCurrency(amount) {
    return '₹' + Number(amount).toLocaleString('en-IN', {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
    });
}

// ============================================
// CALCULATE NET AMOUNT
// ============================================
function calculateNetAmount(gross, deductions) {
    return gross - deductions;
}

// ============================================
// SHOW/HIDE LOADER
// ============================================
function showLoader() {
    const loader = document.getElementById('loader');
    if (loader) {
        loader.style.display = 'block';
    }
}

function hideLoader() {
    const loader = document.getElementById('loader');
    if (loader) {
        loader.style.display = 'none';
    }
}

// ============================================
// PRINT REPORT
// ============================================
function printReport() {
    window.print();
}

// ============================================
// EXPORT TO CSV
// ============================================
function exportCSV(data, filename) {
    const csv = data.map(row => row.join(',')).join('\n');
    const blob = new Blob([csv], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename + '.csv';
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    window.URL.revokeObjectURL(url);
}

// ============================================
// TOGGLE PASSWORD VISIBILITY
// ============================================
function togglePassword(inputId, iconId) {
    const input = document.getElementById(inputId);
    const icon = document.getElementById(iconId);

    if (input && icon) {
        if (input.type === 'password') {
            input.type = 'text';
            icon.classList.remove('fa-eye');
            icon.classList.add('fa-eye-slash');
        } else {
            input.type = 'password';
            icon.classList.remove('fa-eye-slash');
            icon.classList.add('fa-eye');
        }
    }
}

// ============================================
// AUTO CALCULATE NET PAY
// ============================================
document.addEventListener('DOMContentLoaded', function() {
    const grossInput = document.getElementById('id_gross_amount');
    const deductionsInput = document.getElementById('id_total_deductions');
    const netInput = document.getElementById('id_net_amount');

    if (grossInput && deductionsInput && netInput) {
        function autoCalculate() {
            const gross = parseFloat(grossInput.value) || 0;
            const deductions = parseFloat(deductionsInput.value) || 0;
            netInput.value = (gross - deductions).toFixed(2);
        }

        grossInput.addEventListener('input', autoCalculate);
        deductionsInput.addEventListener('input', autoCalculate);
    }
});

// ============================================
// FILE INPUT DISPLAY (For Import Forms)
// ============================================
document.addEventListener('DOMContentLoaded', function() {
    const fileInputs = document.querySelectorAll('input[type="file"]');
    fileInputs.forEach(function(input) {
        input.addEventListener('change', function() {
            if (this.files && this.files[0]) {
                const fileName = this.files[0].name;
                const fileSize = (this.files[0].size / 1024 / 1024).toFixed(2);
                const label = this.parentElement.querySelector('.file-name-display');
                if (label) {
                    label.textContent = '📄 ' + fileName + ' (' + fileSize + ' MB)';
                    label.style.display = 'block';
                }
            }
        });
    });
});