import uuid

from flask import request, redirect, url_for, render_template, session
from graphic_factor import process_user_images, validate_images
from user import User
from flask_login import logout_user, login_user
from UserLogin import UserLogin
import re
from werkzeug.security import generate_password_hash, check_password_hash
from sessions import session_manager
import json
import random


def auth_login(app, dbase):
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        
        with app.app_context():
            # Проверяем, существует ли пользователь
            user = User.get_by_email(email, dbase)
            if not user:
                return render_template('login.html', 
                                     error="Пользователь с таким адресом электронной почты не зарегистрирован")
            
            # Сохраняем email во временную сессию
            session['auth_email'] = email
            
            # Перенаправляем на формулу
            return redirect(url_for('formula_auth'))
    
    # GET запрос — показываем форму
    return render_template('login.html')


"""Формульная аутентификация"""
def auth_formula_auth(app, dbase, auth_service):

    email = session.get('auth_email', '').strip().lower()
    
    if not email:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        session_id = request.form.get('session_id', '')
        user_answer = request.form.get('password', '')
        
        success, message, attempts_left = auth_service.verify_formula(session_id, user_answer)
        
        if success:
            # # Временно, пока нет graphic_auth
            # return render_template('formula_auth.html', 
            #                     email=email, 
            #                     success="Формула верна! (графика пока не настроена)")
            return redirect(url_for('graphic_auth'))  # закомментировано
        else:
            if attempts_left > 0:
                formula_session = session_manager.get_session(session_id)
                if formula_session:
                    return render_template('formula_auth.html',
                                         email=email,
                                         formula=formula_session.get('formula'),
                                         session_id=session_id,
                                         attempts_left=attempts_left,
                                         error=message)
            
            session.pop('auth_email', None)
            return render_template('formula_auth.html', email=email, error=message)
    
    # GET запрос
    formula, answer, session_id, error = auth_service.generate_formula(email)
    
    if error:
        return render_template('formula_auth.html', email=email, error=error)
    
    formula_session = session_manager.get_session(session_id)
    attempts_left = formula_session['attempts_left'] if formula_session else 3
    
    return render_template('formula_auth.html',
                         email=email,
                         formula=formula,
                         session_id=session_id,
                         attempts_left=attempts_left)


"""Графическая аутентификация"""
def auth_graphic_auth(app, dbase, auth_service):
    
    # Получаем email из сессии
    email = session.get('auth_email', '').strip().lower()
    
    print(f"[DEBUG] email из сессии: {email}")

    if not email:
        return redirect(url_for('login'))
    
    print(f"[DEBUG] request.method = {request.method}")
    
    if request.method == 'POST':
        print("\n[DEBUG] === ОБРАБОТКА POST ЗАПРОСА ===")

        # Читаем данные из HTML-формы (то, что отправил пользователь)
        session_id = request.form.get('session_id', '').strip()
        
        # Проверка графического ответа
        order_json = request.form.get('image_order', '[1,2,3,4]')
        rotations_json = request.form.get('image_rotations', '[0,0,0,0]')
        
        print(f"[DEBUG] session_id = {session_id}")
        print(f"[DEBUG] order_json = {order_json}")
        print(f"[DEBUG] rotations_json = {rotations_json}")

        try:
            # Превращаем JSON-строки в списки Python (то, что отправил пользователь)
            user_order = json.loads(order_json)
            user_rotations = json.loads(rotations_json)
            print(f"[DEBUG] user_order = {user_order}")
            print(f"[DEBUG] user_rotations = {user_rotations}")
        except Exception as e:
            print(f"Ошибка парсинга JSON: {e}")
            return render_template('graphic_auth.html', 
                                 email=email,
                                 error="Ошибка в данных последовательности")
        
        # Получение сессии
        graphic_session = session_manager.get_session(session_id)
        if not graphic_session or graphic_session.get('type') != 'graphic':
            print(f"Сессия истекла или не найдена")
            return render_template('graphic_auth.html', 
                                 email=email,
                                 error="Сессия истекла")    
        # Проверка email в сессии
        if graphic_session.get('email') != email:
            print(f"Несоответствие email в сессии")
            return render_template('graphic_auth.html', 
                                 email=email,
                                 error="Несоответствие сессии")

        # Получаем текущее количество попыток из сессии
        attempts_left = graphic_session.get('attempts_left', 3)

        # Берем правильные значения из сессии (они были сохранены при GET запросе из БД)
        correct_order_from_session = graphic_session.get('correct_order', [1, 2, 3, 4])
        correct_rotations_from_session = graphic_session.get('correct_rotations', [0, 0, 0, 0])
        
        print("\n[DEBUG] === СРАВНЕНИЕ ===")
        print(f"[DEBUG] Что отправил пользователь:")
        print(f"[DEBUG]   order:     {user_order}")
        print(f"[DEBUG]   rotations: {user_rotations}")
        print(f"[DEBUG] Что ожидает сервер (из сессии):")
        print(f"[DEBUG]   order:     {correct_order_from_session}")
        print(f"[DEBUG]   rotations: {correct_rotations_from_session}")
        print(f"[DEBUG]   attempts_left:     {attempts_left}")
        
        # 2.7 Сравниваем
        order_match = (user_order == correct_order_from_session)
        rotations_match = (user_rotations == correct_rotations_from_session)
        
        print(f"[DEBUG] order_match = {order_match}")
        print(f"[DEBUG] rotations_match = {rotations_match}")
        
        if order_match and rotations_match:
            print("\n[SUCCESS] === ПОЛЬЗОВАТЕЛЬ ПРОШЁЛ ГРАФИКУ! ===")
            user = User.get_by_email(email, dbase)
            if not user:
                return render_template('graphic_auth.html', 
                                     email=email,
                                     error="Пользователь не найден")
            
            # Вход через Flask-Login (создаёт постоянную сессию)          
            userlogin = UserLogin().create(user)
            login_user(userlogin)
            
            # Очищаем временную сессию
            session.pop('auth_email', None)

            # # Удаляем временную сессию session_manager
            # session_manager.remove_session(session_id)
            
            print(f"[SUCCESS] Пользователь {email} успешно авторизован!")
            # Перенаправляем на защищённую страницу
            return redirect(url_for('index'))  # или 'fashion' или '/'
        else:
            # УМЕНЬШАЕМ КОЛИЧЕСТВО ПОПЫТОК
            attempts_left = attempts_left - 1
            graphic_session['attempts_left'] = attempts_left
            
            print(f"[DEBUG] Неудача. Осталось попыток: {attempts_left}")            
            if attempts_left > 0:
                error_msg = "Последовательность неверная"
                return render_template('graphic_auth.html',
                                     email=email,
                                     session_id=session_id,
                                     user_images=graphic_session.get('user_images', []),
                                     display_order=graphic_session.get('display_order', [1, 2, 3, 4]),
                                     correct_order=correct_order_from_session,
                                     correct_rotations=correct_rotations_from_session,
                                     attempts_left=attempts_left,
                                     error=f"{error_msg}. Осталось попыток: {attempts_left}")
            else:
                # Попытки кончились
                session.pop('auth_email', None)
                return redirect(url_for('login', error="Превышено количество попыток"))
    
    print("\n[DEBUG] === ОБРАБОТКА GET ЗАПРОСА ===")

    # Получаем пользователя
    user = User.get_by_email(email, dbase)
    if not user:
        print(f"Пользователь не найден в БД")
        session.pop('auth_email', None)
        return redirect(url_for('login'))
    
    # Получаем графические данные из таблицы graphic_auth
    graphic_data = dbase.get_graphic_auth(user.id)

    print(f"[DEBUG] graphic_data = {graphic_data}")
    
    images_from_db  = graphic_data['images']
    image_sequence_from_db  = graphic_data['image_sequence']
    
    # Достаём правильные порядок и повороты из JSON
    correct_order_from_db  = image_sequence_from_db.get('order', [1, 2, 3, 4])
    correct_rotations_from_db  = image_sequence_from_db.get('rotations', [0, 0, 0, 0])

    print(f"[DEBUG] images_from_db = {images_from_db}")
    print(f"[DEBUG] correct_order_from_db = {correct_order_from_db}")
    print(f"[DEBUG] correct_rotations_from_db = {correct_rotations_from_db}")

    if not images_from_db or len(images_from_db) != 4:
        return render_template('graphic_auth.html', 
                             email=email,
                             error="У пользователя не настроена графическая аутентификация")
    
    # Создание случайного порядка для отображения
    display_order = list(range(1, 5))
    random.shuffle(display_order)
    
    # Создание сессии для графической аутентификации
    session_id = session_manager.create_graphic_session(
        email=email,
        user_data={'user_id': user.id, 'name': user.username, 'email': email},
        challenge_data={
            'correct_order': correct_order_from_db,
            'correct_rotations': correct_rotations_from_db,
            'user_images': images_from_db,
            'display_order': display_order
        }
    )

    print(f"[DEBUG] Создана графическая сессия: session_id = {session_id}")
    
    # Получение информации о сессии
    graphic_session = session_manager.get_session(session_id)
    attempts_left = graphic_session.get('attempts_left', 3) if graphic_session else 3

    print(f"[DEBUG] attempts_left = {attempts_left}")
    
    print("\n[DEBUG] === ОТОБРАЖАЕМ СТРАНИЦУ ===\n")

    return render_template('graphic_auth.html',
                         email=email,
                         session_id=session_id,
                         user_images=images_from_db,
                         display_order=display_order,
                         correct_order=correct_order_from_db,
                         correct_rotations=correct_rotations_from_db,
                         attempts_left=attempts_left)


"""Регистрация нового пользователя с двухфакторной аутентификацией"""
def auth_register(app, dbase):
    
    if request.method == 'POST':
        # Получаем данные из формы
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        password_confirm = request.form.get('password_confirm', '')
        
        # Получаем последовательность
        order_json = request.form.get('image_order', '[1,2,3,4]')
        rotations_json = request.form.get('image_rotations', '[0,0,0,0]')
        try:
            order = json.loads(order_json)
            rotations = json.loads(rotations_json)
            print(f"[REGISTER] Последовательность: order={order}, rotations={rotations}")
        except Exception as e:
            print(f"[REGISTER ERROR] Ошибка парсинга последовательности: {e}")
            order = [1, 2, 3, 4]
            rotations = [0, 0, 0, 0]
        
        # Получаем имена изображений (из скрытого поля формы)
        image_names_json = request.form.get('image_names', '[]')
        try:
            image_names = json.loads(image_names_json)
            print(f"[REGISTER] Имена изображений: {image_names}")
        except json.JSONDecodeError as e:
            print(f"[REGISTER ERROR] Ошибка парсинга JSON: {e}")
            image_names = []
        
        # Получаем файлы изображений
        image_files = []
        for i in range(1, 5):
            file_key = f'image{i}'
            if file_key in request.files:
                file = request.files[file_key]
                if file and file.filename:
                    image_files.append((i, file))
        
        # Валидация основных полей
        if not all([name, email, password, password_confirm]):
            return render_template('registration.html', 
                                 error='Все поля обязательны для заполнения',
                                 name=name, email=email)
        
        if password != password_confirm:
            return render_template('registration.html', 
                                 error='Пароли не совпадают',
                                 name=name, email=email)
        
        if len(password) < 8:
            return render_template('registration.html', 
                                 error='Пароль должен содержать минимум 8 символов',
                                 name=name, email=email)
        
        # Валидация изображений через существующую функцию
        is_valid, error_msg = validate_images(image_files, image_names)
        if not is_valid:
            return render_template('registration.html', 
                                 error=error_msg,
                                 name=name, email=email)
        
        # Проверяем существование пользователя через наш dbase
        existing_user = dbase.getUser_email(email)
        if existing_user:
            return render_template('registration.html', 
                                 error='Пользователь с таким email уже существует',
                                 name=name, email=email)
        
        # Создаём пользователя в таблице person
        try:
            dbase.add_person(name, email, password)
            print(f"[REGISTER] Пользователь {email} добавлен в БД")
        except Exception as e:
            print(f"[REGISTER ERROR] Ошибка при создании пользователя: {e}")
            return render_template('registration.html', 
                                 error='Ошибка при создании пользователя',
                                 name=name, email=email)
        
        # Получаем ID созданного пользователя
        user_data = dbase.getUser_email(email)
        if not user_data:
            return render_template('registration.html', 
                                 error='Ошибка при получении ID пользователя',
                                 name=name, email=email)
        
        person_id = user_data['id']
        
        # Обрабатываем и сохраняем изображения через существующую функцию
        saved_filenames = process_user_images(email, image_files, image_names)
        
        if not saved_filenames or len(saved_filenames) != 4:
            # Удаляем пользователя если не удалось сохранить изображения
            try:
                dbase.execute_update("DELETE FROM person WHERE person_id = %s", (person_id,))
            except:
                pass
            return render_template('registration.html', 
                                 error='Ошибка при сохранении изображений',
                                 name=name, email=email)
        
        # Сохраняем графическую аутентификацию в таблицу graphic_auth
        image_sequence_data = {
            'order': order,
            'rotations': rotations
        }
        
        try:
            dbase.add_graphic_auth(person_id, saved_filenames, image_sequence_data)
            print(f"[REGISTER] Графическая аутентификация сохранена для {email}")
        except Exception as e:
            print(f"[REGISTER ERROR] Ошибка при сохранении графики: {e}")
            # Удаляем пользователя
            try:
                dbase.execute_update("DELETE FROM person WHERE person_id = %s", (person_id,))
            except:
                pass
            return render_template('registration.html', 
                                 error='Ошибка при сохранении графической аутентификации',
                                 name=name, email=email)
        
        # Регистрация успешна
        print(f"[REGISTER SUCCESS] Пользователь {email} успешно зарегистрирован")
        return redirect(url_for('login', 
                                success="Регистрация успешна! Теперь вы можете войти в систему."))
    
    # GET запрос — показываем форму регистрации
    return render_template('registration.html')


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