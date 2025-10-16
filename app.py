from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash
import random
import string
from models import User, SavedPassword, hash_password, verify_password
from auth import login_required, create_token, verify_token
import json

app = Flask(__name__)
app.secret_key = 'your-secret-key-here-change-in-production'


class PasswordGenerator:
    def init(self):
        self.lowercase = string.ascii_lowercase
        self.uppercase = string.ascii_uppercase
        self.digits = string.digits
        self.symbols = "!@#$%^&*()_+-=[]{}|;:,.<>?"

    def generate_password(self, length=12, use_uppercase=True, use_digits=True, use_symbols=True):
        characters = self.lowercase

        if use_uppercase:
            characters += self.uppercase
        if use_digits:
            characters += self.digits
        if use_symbols:
            characters += self.symbols

        # Убедимся, что есть хотя бы один символ каждого выбранного типа
        password = []

        if use_uppercase:
            password.append(random.choice(self.uppercase))
        if use_digits:
            password.append(random.choice(self.digits))
        if use_symbols:
            password.append(random.choice(self.symbols))

        # Заполняем оставшуюся длину
        remaining_length = length - len(password)
        if remaining_length > 0:
            password.extend(random.choice(characters) for _ in range(remaining_length))

        # Перемешиваем пароль
        random.shuffle(password)
        return ''.join(password)

    def generate_easy_password(self):
        return self.generate_password(length=8, use_uppercase=False, use_digits=True, use_symbols=False)

    def generate_medium_password(self):
        return self.generate_password(length=12, use_uppercase=True, use_digits=True, use_symbols=True)

    def generate_strong_password(self):
        return self.generate_password(length=16, use_uppercase=True, use_digits=True, use_symbols=True)


password_generator = PasswordGenerator()


# Маршруты аутентификации
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')

        if not username or not email or not password:
            flash('Все поля обязательны для заполнения', 'error')
            return render_template('register.html')

        if password != confirm_password:
            flash('Пароли не совпадают', 'error')
            return render_template('register.html')

        if len(password) < 6:
            flash('Пароль должен содержать минимум 6 символов', 'error')
            return render_template('register.html')

        user = User.create(username, email, password)
        if user:
            session['user_id'] = user.id
            session['username'] = user.username
            flash('Регистрация успешна! Добро пожаловать!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Пользователь с таким именем или email уже существует', 'error')

    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        user = User.authenticate(username, password)
        if user:
            session['user_id'] = user.id
            session['username'] = user.username
            flash('Вход выполнен успешно!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Неверное имя пользователя или пароль', 'error')

    return render_template('login.html')


@app.route('/logout')
def logout():
    session.clear()
    flash('Вы вышли из системы', 'info')
    return redirect(url_for('login'))

@app.route('/')
@login_required
def index():
    return render_template('index.html', username=session.get('username'))


@app.route('/profile')
@login_required
def profile():
    user_passwords = SavedPassword.get_user_passwords(session['user_id'])
    return render_template('profile.html', passwords=user_passwords, username=session.get('username'))


# API маршруты
@app.route('/api/generate_password', methods=['POST'])
@login_required
def api_generate_password():
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data received'}), 400

        password_type = data.get('type')

        if password_type == 'easy':
            password = password_generator.generate_easy_password()
        elif password_type == 'medium':
            password = password_generator.generate_medium_password()
        elif password_type == 'strong':
            password = password_generator.generate_strong_password()
        elif password_type == 'custom':
            length = int(data.get('length', 12))
            use_uppercase = data.get('uppercase', True)
            use_digits = data.get('digits', True)
            use_symbols = data.get('symbols', True)
            password = password_generator.generate_password(
                length, use_uppercase, use_digits, use_symbols
            )
        else:
            password = password_generator.generate_medium_password()

        return jsonify({'password': password})

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/check_strength', methods=['POST'])
def api_check_strength():
    try:
        data = request.get_json()
        password = data.get('password', '')

        score = 0
        feedback = []

        if len(password) >= 8:
            score += 1
        else:
            feedback.append("Пароль должен содержать минимум 8 символов")

        if any(c.isupper() for c in password) and any(c.islower() for c in password):
            score += 1
        else:
            feedback.append("Добавьте заглавные и строчные буквы")

        if any(c.isdigit() for c in password):
            score += 1
        else:
            feedback.append("Добавьте цифры")

        if any(c in password_generator.symbols for c in password):
            score += 1
        else:
            feedback.append("Добавьте специальные символы")

        if len(password) >= 12:
            score += 1

        if score <= 2:
            strength = "Слабый"
            color = "#ff4757"
        elif score == 3:
            strength = "Средний"
            color = "#ffa502"
        else:
            strength = "Сильный"
            color = "#2ed573"

        return jsonify({
            'strength': strength,
            'color': color,
            'score': score,
            'feedback': feedback
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/save_password', methods=['POST'])
@login_required
def api_save_password():
    try:
        data = request.get_json()
        title = data.get('title', 'Без названия')
        password = data.get('password')
        strength = data.get('strength', 'Средний')

        if not password:
            return jsonify({'error': 'Пароль обязателен'}), 400

        saved_password = SavedPassword.create(
            session['user_id'], title, password, strength
        )

        return jsonify({
            'success': True,
            'message': 'Пароль сохранен',
            'id': saved_password.id
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/delete_password/<int:password_id>', methods=['DELETE'])



@login_required
def api_delete_password(password_id):
    try:
        SavedPassword.delete(password_id, session['user_id'])
        return jsonify({'success': True, 'message': 'Пароль удален'})

    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
