// Синхронизация ползунка и числового поля
document.addEventListener('DOMContentLoaded', function() {
    const lengthSlider = document.getElementById('lengthSlider');
    const lengthInput = document.getElementById('length');

    lengthSlider.addEventListener('input', function() {
        lengthInput.value = this.value;
    });

    lengthInput.addEventListener('input', function() {
        let value = parseInt(this.value);
        if (value < 4) value = 4;
        if (value > 32) value = 32;
        this.value = value;
        lengthSlider.value = value;
    });

    // Генерируем пароль при загрузке
    generatePassword('medium');
});

async function generatePassword(type) {
    showLoading();

    try {
        const response = await fetch('/generate_password', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ type: type })
        });

        const data = await response.json();

        if (data.error) {
            throw new Error(data.error);
        }

        document.getElementById('passwordOutput').value = data.password;
        await checkPasswordStrength(data.password);

    } catch (error) {
        console.error('Error:', error);
        showError('Ошибка при генерации пароля: ' + error.message);
    } finally {
        hideLoading();
    }
}

async function generateCustomPassword() {
    showLoading();

    const length = parseInt(document.getElementById('length').value);
    const uppercase = document.getElementById('uppercase').checked;
    const digits = document.getElementById('digits').checked;
    const symbols = document.getElementById('symbols').checked;

    // Проверяем, что выбран хотя бы один тип символов
    if (!uppercase && !digits && !symbols) {
        showError('Выберите хотя бы один тип символов!');
        hideLoading();
        return;
    }

    try {
        const response = await fetch('/generate_password', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                type: 'custom',
                length: length,
                uppercase: uppercase,
                digits: digits,
                symbols: symbols
            })
        });

        const data = await response.json();

        if (data.error) {
            throw new Error(data.error);
        }

        document.getElementById('passwordOutput').value = data.password;
        await checkPasswordStrength(data.password);

    } catch (error) {
        console.error('Error:', error);
        showError('Ошибка при генерации пароля: ' + error.message);
    } finally {
        hideLoading();
    }
}

async function checkPasswordStrength(password) {
    if (!password) return;

    try {
        const response = await fetch('/check_strength', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ password: password })
        });

        const data = await response.json();

        if (data.error) {
            throw new Error(data.error);
        }

        document.getElementById('strengthText').textContent = data.strength;
        document.getElementById('strengthText').style.color = data.color;

        const strengthBar = document.getElementById('strengthBar');
        strengthBar.style.width = (data.score * 20) + '%';
        strengthBar.style.backgroundColor = data.color;

    } catch (error) {
        console.error('Error:', error);
    }
}

function copyPassword() {
    const passwordField = document.getElementById('passwordOutput');
    if (passwordField.value) {
        passwordField.select();
        document.execCommand('copy');

        // Визуальная обратная связь
        const copyButton = document.querySelector('.copy-btn');
        const originalHTML = copyButton.innerHTML;
        copyButton.innerHTML = '<span class="copy-icon">✅</span><span class="copy-text">Скопировано!</span>';
        copyButton.style.background = '#10b981';

        setTimeout(() => {
            copyButton.innerHTML = originalHTML;
            copyButton.style.background = '';
        }, 2000);
    }
}

function showLoading() {
    const output = document.getElementById('passwordOutput');
    output.value = 'Генерация...';
    output.style.color = '#6b7280';
}

function hideLoading() {
    const output = document.getElementById('passwordOutput');
    output.style.color = '#1f2937';
}

function showError(message) {
    const output = document.getElementById('passwordOutput');
    output.value = 'Ошибка!';
    output.style.color = '#ef4444';

    alert(message);
}