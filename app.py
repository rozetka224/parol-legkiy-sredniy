from flask import Flask, render_template, request, jsonify
import random
import string

app = Flask(__name__)


class PasswordGenerator:
    def __init__(self):
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

        if not characters:
            characters = self.lowercase

        password = ''.join(random.choice(characters) for _ in range(length))
        return password

    def generate_easy_password(self):
        return self.generate_password(length=8, use_uppercase=False, use_digits=True, use_symbols=False)

    def generate_medium_password(self):
        return self.generate_password(length=12, use_uppercase=True, use_digits=True, use_symbols=False)

    def generate_strong_password(self):
        return self.generate_password(length=16, use_uppercase=True, use_digits=True, use_symbols=True)

    def generate_custom_password(self, length, use_uppercase, use_digits, use_symbols):
        return self.generate_password(length, use_uppercase, use_digits, use_symbols)


password_generator = PasswordGenerator()


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/generate_password', methods=['POST'])
def generate_password():
    data = request.json
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
        password = password_generator.generate_custom_password(
            length, use_uppercase, use_digits, use_symbols
        )
    else:
        password = password_generator.generate_medium_password()

    return jsonify({'password': password})


@app.route('/check_strength', methods=['POST'])
def check_strength():
    password = request.json.get('password', '')
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
        color = "red"
    elif score == 3:
        strength = "Средний"
        color = "orange"
    else:
        strength = "Сильный"
        color = "green"

    return jsonify({
        'strength': strength,
        'color': color,
        'score': score,
        'feedback': feedback
    })


if __name__ == '__main__':
    app.run(debug=True)