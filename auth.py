from flask import request, redirect, url_for, render_template, session
from graphic_factor import process_user_images, validate_images
from user import User
from flask_login import logout_user, login_user, current_user
from UserLogin import UserLogin
from werkzeug.security import generate_password_hash, check_password_hash
from sessions import session_manager
import json, random, re
from graph_seq_hash import hash_password, verify_password
from encrypt import encryption_pass, decryprion_pass


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
    email = request.args.get('email', '').strip().lower()
    title = request.args.get('title', "")  # забираем title
    description = request.args.get('description', "")   

    if not email:
        email = session.get('auth_email', '').strip().lower()
    
    change_target = request.args.get('change_target')
    if change_target:
        session['change_target'] = change_target
    
    if title:
        session['formula_title'] = title
    if description:
        session['formula_description'] = description

    if not email:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        session_id = request.form.get('session_id', '')
        user_answer = request.form.get('password', '')
        
        success, message, attempts_left = auth_service.verify_formula(session_id, user_answer)
        
        if success:
            change_target = session.get('change_target')
            title = session.get('formula_title', "")
            description = session.get('formula_description', "")
            if change_target:
                return redirect(url_for('graphic_auth', change_target=change_target, title=title,                           # передаём в шаблон
                                         description=description, email=email))
            else:
                return redirect(url_for('graphic_auth', email=email))
        else:
            if attempts_left > 0:
                formula_session = session_manager.get_session(session_id)
                if formula_session:
                    title = session.get('formula_title', "")
                    description = session.get('formula_description', "")
                    return render_template('formula_auth.html',
                                         email=email,
                                         title=title,                           # передаём в шаблон
                                         description=description,
                                         change_target=change_target,   
                                         formula=formula_session.get('formula'),
                                         session_id=session_id,
                                         attempts_left=attempts_left,
                                         error=message)
            
            session.pop('auth_email', None)
            return render_template('formula_auth.html', email=email, error=message)
    

    # GET запрос
    # Расшифровка пароля из БД
    user = User.get_by_email(email, dbase)
    decr_pass = decryprion_pass(user.password_hash)
    print(f"decr_pass = {decr_pass}")

    formula, answer, session_id, error = auth_service.generate_formula(email, decr_pass)
    
    if error:
        return render_template('formula_auth.html', email=email, error=error)
    
    formula_session = session_manager.get_session(session_id)
    attempts_left = formula_session['attempts_left'] if formula_session else 3
    
    return render_template('formula_auth.html',
                         email=email,
                         title=title,                           # передаём в шаблон
                         description=description,
                         change_target=change_target,   
                         formula=formula,
                         session_id=session_id,
                         attempts_left=attempts_left)


"""Графическая аутентификация"""
def auth_graphic_auth(app, dbase, auth_service):
    email = request.args.get('email', '').strip().lower()
    if not email:
        email = session.get('auth_email', '').strip().lower()
    
    change_target = request.args.get('change_target') or session.get('change_target')
    title = request.args.get('title', session.get('formula_title', ""))
    description = request.args.get('description', session.get('formula_description', ""))

    if not email:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        # Читаем данные из HTML-формы (то, что отправил пользователь)
        order_json = request.form.get('image_order', '[1,2,3,4]')
        rotations_json = request.form.get('image_rotations', '[0,0,0,0]')
        try:
            # Превращаем JSON-строки в списки Python (то, что отправил пользователь)
            user_order = json.loads(order_json)
            user_rotations = json.loads(rotations_json)
            image_sequence_data = str(user_order + user_rotations)
        except Exception as e:
            return render_template('graphic_auth.html', 
                                 email=email,
                                 error="Ошибка в данных последовательности")
        
        # Получаем попытки из сессии
        attempts_left = session.get('graphic_attempts_left', 3)
        
        # Получаем правильные значения из БД
        user = User.get_by_email(email, dbase)
        if not user:
            return render_template('graphic_auth.html', email=email, error="Пользователь не найден")
        
        graphic_data = dbase.get_graphic_auth(user.id)
        if not graphic_data:
            return render_template('graphic_auth.html', email=email, error="Графика не настроена")
        
        image_sequence_db = graphic_data['image_sequence']
        print(f"Тип: {type(image_sequence_db)}")
        print(f"Значение: '{image_sequence_db}'")
        print(f"Длина: {len(image_sequence_db) if image_sequence_db else 0}")

        # Проверка последовательности
        if verify_password(image_sequence_db, image_sequence_data):
            session.pop('graphic_attempts_left', None)
    
            if change_target == 'password':
                session.pop('change_target', None)
                return redirect(url_for('change_password'))
            elif change_target == 'images':
                session.pop('change_target', None)
                return redirect(url_for('change_user_images'))
            else:                
                # Вход через Flask-Login (создаёт постоянную сессию)          
                userlogin = UserLogin().create(user)
                login_user(userlogin)
                
                session.pop('auth_email', None)
                return redirect(url_for('index'))
        else:
            attempts_left = attempts_left - 1
            session['graphic_attempts_left'] = attempts_left
                     
            if attempts_left > 0:
                # Загружаем изображения из БД и создаём новый порядок
                user_images = graphic_data['images']
                new_display_order = list(range(1, 5))
                random.shuffle(new_display_order)
                
                error_msg = "Последовательность неверная"
                return render_template('graphic_auth.html',
                                    email=email,
                                    user_images=user_images,
                                    display_order=new_display_order,
                                    attempts_left=attempts_left,
                                    error=f"{error_msg}. Осталось попыток: {attempts_left}")
            else:
                session.pop('graphic_attempts_left', None)
                session.pop('auth_email', None)
                return redirect(url_for('login', error="Превышено количество попыток"))
    
    # Получаем пользователя
    user = User.get_by_email(email, dbase)
    if not user:
        session.pop('auth_email', None)
        return redirect(url_for('login'))
    
    graphic_data = dbase.get_graphic_auth(user.id)
    if not graphic_data:
        return render_template('graphic_auth.html', 
                             email=email,
                             error="У пользователя не настроена графическая аутентификация")
    
    images_from_db = graphic_data['images']
    if not images_from_db or len(images_from_db) != 4:
        return render_template('graphic_auth.html', 
                               email=email, 
                               error="У пользователя не настроена графическая аутентификация")

    # Создание случайного порядка для отображения
    display_order = list(range(1, 5))
    random.shuffle(display_order)
    
    session['graphic_attempts_left'] = 3

    return render_template('graphic_auth.html',
                         email=email,
                         title=title,
                         description=description,
                         change_target=change_target,
                         user_images=images_from_db,
                         display_order=display_order,
                         attempts_left=3)


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
        except Exception as e:
            print(f"[REGISTER ERROR] Ошибка парсинга последовательности: {e}")
            order = [1, 2, 3, 4]
            rotations = [0, 0, 0, 0]
        
        # Получаем имена изображений (из скрытого поля формы)
        image_names_json = request.form.get('image_names', '[]')
        try:
            image_names = json.loads(image_names_json)
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
        
        # Проверка существования пользователя
        existing_user = dbase.getUser_email(email)
        if existing_user:
            return render_template('registration.html', 
                                 error='Пользователь с таким email уже существует',
                                 name=name, email=email)
        
        # Шифрование пароля
        encr_pass = encryption_pass(password)

        # Создание пользователя в таблице person
        try:
            dbase.add_person(name, email, encr_pass)
        except Exception as e:
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
        
        # Обработка и сохранение изображений
        saved_filenames = process_user_images(email, image_files, image_names)
        
        if not saved_filenames or len(saved_filenames) != 4:
            # Удаление пользователя если не удалось сохранить изображения
            try:
                dbase.execute_update("DELETE FROM person WHERE person_id = %s", (person_id,))
            except:
                pass
            return render_template('registration.html', 
                                 error='Ошибка при сохранении изображений',
                                 name=name, email=email)
        
        image_sequence_data = {
            'order': order,
            'rotations': rotations
        }
        
        image_sequence_data = str(order + rotations)
        seq_hash = hash_password(image_sequence_data)

        try:
            dbase.add_graphic_auth(person_id, saved_filenames, seq_hash)
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
    
    return render_template('registration.html')


def auth_change_password(app, dbase):
    if request.method == 'POST':
        new_password = request.form.get('new_password', '')
        confirm_password = request.form.get('confirm_password', '')
        
        # Валидация
        if not new_password:
            return render_template('change_password.html', error="Введите новый пароль")
        
        if len(new_password) < 8:
            return render_template('change_password.html', error="Пароль должен быть не менее 8 символов")
        
        if new_password != confirm_password:
            return render_template('change_password.html', error="Пароли не совпадают")
        
        user = User.get(current_user.get_id(), dbase)
        if not user:
            return render_template('change_password.html', error="Пользователь не найден")
        
        new_encr_pass = encryption_pass(new_password)

        if user.password_hash == new_encr_pass:
            return render_template('change_password.html', error="Новый пароль должен отличаться от старого")
        
        # Сохранение нового пароля
        try:
            dbase.update_password(user.id, new_encr_pass)
            return redirect(url_for('profile', success="Пароль успешно изменён!"))
        except Exception as e:
            return render_template('change_password.html', error="Ошибка при сохранении пароля")
    
    return render_template('change_password.html')


"""Смена пользовательских изображений"""
def auth_change_images(app, dbase):
    if request.method == 'POST':
        # Получаем последовательность из формы
        order_json = request.form.get('image_order', '[1,2,3,4]')
        rotations_json = request.form.get('image_rotations', '[0,0,0,0]')
        
        try:
            sequence_order = json.loads(order_json)
            sequence_rotations = json.loads(rotations_json)
        except Exception as e:
            return render_template('change_user_images.html', error="Ошибка в данных последовательности")
        
        # Получаем имена изображений
        image_names_json = request.form.get('image_names', '[]')
        try:
            image_names = json.loads(image_names_json)
        except:
            image_names = []
        
        # Получаем файлы изображений
        image_files = []
        for i in range(1, 5):
            file_key = f'image{i}'
            if file_key in request.files:
                file = request.files[file_key]
                if file and file.filename:
                    image_files.append((i, file))
        
        # Валидация
        is_valid, error_msg = validate_images(image_files, image_names)
        if not is_valid:
            return render_template('change_user_images.html', error=error_msg)
        
        # Сохраняем новые файлы
        user = User.get(current_user.get_id(), dbase)
        if not user:
            return render_template('change_images.html', error="Пользователь не найден")
        # print(f"[DEBUG] image_files = {image_files}")
        print(f"[DEBUG] user.email = {user.email}")
        # print(f"[DEBUG] len(image_files) = {len(image_files)}") 
        saved_filenames = process_user_images(user.email, image_files, [])
        # print(f"[DEBUG] saved_filenames = {saved_filenames}") 
        
        if not saved_filenames or len(saved_filenames) != 4:
            return render_template('change_user_images.html', error="Ошибка при сохранении изображений")
        
        # Получаем пользователя
        user = User.get(current_user.get_id(), dbase)
        if not user:
            return render_template('change_user_images.html', error="Пользователь не найден")
        
        # Формируем данные для БД
        graphic_sequence = {
            'order': sequence_order,
            'rotations': sequence_rotations
        }
        
        graphic_sequence = str(sequence_order + sequence_rotations)
        seq_hash = hash_password(graphic_sequence)

        try:
            dbase.update_graphic_auth(user.id, saved_filenames, seq_hash)
            return redirect(url_for('profile', success="Изображения успешно обновлены!"))
        except Exception as e:
            return render_template('change_user_images.html', error="Ошибка при сохранении")
    
    return render_template('change_user_images.html')


def logout():
    logout_user()
    return redirect('/login')


# Старая функция смены пароля
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

# Старая функция регистрации
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