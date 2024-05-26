from flask import Flask, request, redirect, url_for, render_template
from user import User
from UserLogin import UserLogin
from data_base import Database
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import re
from werkzeug.security import generate_password_hash, check_password_hash


def login(app, dbase):
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        with app.app_context():
            user = User.get_by_email(email, dbase)
            if user:
                if check_password_hash(user.password_hash, password):

                    userlogin = UserLogin().create(user)
                    login_user(userlogin)
                    return redirect('/')
                else:
                    return render_template('login.html', error="Неверный пароль")
            else:
                return render_template('login.html', error="Пользователь с таким адресом электронной почты не зарегистрирован")

    else:
        return render_template('login.html')


def update_pass(app, person_id, password, new_password, repeat_new_password, dbase):
    if not all([password, new_password, repeat_new_password]):
        return "Не все поля заполнены"

    if len(new_password) < 8 or len(new_password) > 255:
        return "Длина пароля должна быть от 8 до 255 символов"

    if new_password != repeat_new_password:
        return "Пароли не совпадают"

    # Получение текущего пароля пользователя
    with app.app_context():
        user = User.get(person_id, dbase)
        print(user.password_hash)
        if not check_password_hash(user.password_hash, password):
            return "Неверный старый пароль"
        elif check_password_hash(user.password_hash, new_password):
            return "Новый пароль должен отличаться от старого"
        else:
            hash = generate_password_hash(new_password)
            User.add_new_password(person_id, hash, dbase)
            return None


def logout():
    logout_user()
    return redirect('/login')


def registration(app, dbase):
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']

        # Проверка адреса электронной почты
        if not re.match(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", email):
            # Адрес электронной почты не соответствует допустимому формату
            return render_template('registration.html', error="Введен некорректный адрес электронной почты")
        # Проверка пароля
        elif len(password) < 8 or len(password) > 255:
            # Пароль не соответствует требованиям длины
            return render_template('registration.html', error="Длина пароля должна быть от 8 до 255 символов")
        else:
            # Проверка адреса электронной почты в базе данных
            with app.app_context():
                # Проверка адреса электронной почты в базе данных
                user = User.get_by_email(email, dbase)
                if user:
                    # Адрес электронной почты уже существует в базе данных
                    return render_template('registration.html', error="Этот адрес электронной почты уже зарегистрирован")

                # Проверка пароля в базе данных
                hash = generate_password_hash(password)
                user = User.get_by_password(hash, dbase)
                if user:
                    # Пароль уже существует в базе данных
                    return render_template('registration.html', error="Этот пароль уже используется")

                # Добавление пользователя
                hash = generate_password_hash(password)
                user = User.create(name, email, hash, dbase)  # Получаем созданного пользователя
                if user:
                    return redirect('/login')  # Перенаправление на страницу входа
                else:
                    return render_template('registration.html', error="Ошибка при создании пользователя")

    else:
        return render_template('registration.html')