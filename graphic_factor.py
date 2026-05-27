import os
import re
import random
from werkzeug.utils import secure_filename

# Конфигурация загрузки файлов
USER_IMAGES_FOLDER = 'static/user_images'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

# Создаем папку если ее нет
os.makedirs(USER_IMAGES_FOLDER, exist_ok=True)

# Проверка расширения файла
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Сохранение изображения в user_images
def save_user_image(file, filename):
    try:
        safe_filename = secure_filename(filename)
        filepath = os.path.join(USER_IMAGES_FOLDER, safe_filename)
        file.save(filepath)
        print(f"[GRAPHIC] Изображение сохранено: {filepath}")
        return safe_filename
    except Exception as e:
        print(f"[GRAPHIC ERROR] Ошибка при сохранении изображения: {e}")
        return None

# Генерация имен изображений на основе email
def generate_image_names(email):
    email_parts = email.split('@')
    if email_parts and email_parts[0]:
        username = re.sub(r'[^a-zA-Z0-9_]', '_', email_parts[0]).lower()
    else:
        username = 'user'
    
    return [
        f"{username}_img1.jpg",
        f"{username}_img2.jpg",
        f"{username}_img3.jpg",
        f"{username}_img4.jpg"
    ]

# Валидация изображений при регистрации
def validate_images(image_files, image_names):

    if len(image_files) != 4:
        return False, f"Необходимо выбрать все 4 изображения (выбрано: {len(image_files)})"
    
    if len(image_names) != 4:
        return False, f"Ошибка в данных изображений (получено {len(image_names)} имен)"
    
    for i, (index, file) in enumerate(image_files, 1):
        if not file.filename:
            return False, f"Изображение {i} не выбрано"
        
        if not allowed_file(file.filename):
            return False, f"Файл {i} имеет недопустимый формат"
    
    return True, ""

# Обработка и сохранение изображений пользователей
def process_user_images(email, image_files, image_names):

    saved_filenames = []
    
    for i, (index, file) in enumerate(image_files, 1):
        if i-1 < len(image_names):
            filename = image_names[i-1]
        else:
            generated_names = generate_image_names(email)
            filename = generated_names[i-1] if i-1 < len(generated_names) else f"user_img{i}.jpg"
        
        saved_filename = save_user_image(file, filename)
        if saved_filename:
            saved_filenames.append(saved_filename)
        else:
            print(f"[GRAPHIC ERROR] Не удалось сохранить изображение {i} для {email}")
            for saved_file in saved_filenames:
                try:
                    os.remove(os.path.join(USER_IMAGES_FOLDER, saved_file))
                except:
                    pass
            return []
    
    return saved_filenames

# Очистка изображения пользователя
def delete_user_images(filenames):
    try:
        for filename in filenames:
            filepath = os.path.join(USER_IMAGES_FOLDER, filename)
            if os.path.exists(filepath):
                os.remove(filepath)
                print(f"[GRAPHIC] Удален файл: {filepath}")
        return True
    except Exception as e:
        print(f"[GRAPHIC ERROR] Ошибка при удалении изображений: {e}")
        return False


def prepare_graphic_challenge(user_data):
    """
    Подготавливает данные для графической аутентификации
    
    Args:
        user_data: данные пользователя из БД
    
    Returns:
        dict: данные для отображения на странице аутентификации
    """
    # Извлекаем правильную последовательность
    sequence = user_data.get('sequence', {
        'order': [1, 2, 3, 4],
        'rotations': [0, 0, 0, 0]
    })
    
    correct_order = sequence['order']  # Например: [1, 4, 3, 2]
    correct_rotations = sequence['rotations']  # Например: [0, 180, 90, 270]
    user_images = user_data.get('images', [])
    
    # Создаем случайный порядок отображения
    display_order = [1, 2, 3, 4]
    random.shuffle(display_order)
    
    # Создаем задачу
    challenge_data = {
        'display_order': display_order,  # Как показываем пользователю
        'correct_order': correct_order,  # Правильный порядок
        'correct_rotations': correct_rotations,  # Правильные повороты
        'user_images': user_images,  # Имена файлов
        'image_info': []  # Информация о каждом изображении
    }
    
    # Создаем информацию о каждом изображении
    for display_pos, image_num in enumerate(display_order, 1):
        # image_num - это какое изображение по номеру (1-4)
        # Находим, где это изображение должно быть в правильной последовательности
        correct_pos = correct_order.index(image_num) + 1
        
        # Получаем правильный поворот для этого изображения
        rotation_index = correct_order.index(image_num)
        correct_rotation = correct_rotations[rotation_index]
        
        # Имя файла
        if image_num - 1 < len(user_images):
            filename = user_images[image_num - 1]
        else:
            filename = f"image_{image_num}.jpg"
        
        challenge_data['image_info'].append({
            'display_position': display_pos,  # Где показываем (1-4)
            'image_number': image_num,  # Какое это изображение (1-4)
            'filename': filename,
            'correct_position': correct_pos,  # Где оно должно быть (1-4)
            'correct_rotation': correct_rotation,  # Какой должен быть поворот
            'current_rotation': 0  # Начинаем с нулевого поворота
        })
    
    print(f"[GRAPHIC] Challenge подготовлен:")
    print(f"  Показываем в порядке: {display_order}")
    print(f"  Должно быть: {correct_order}")
    print(f"  Повороты: {correct_rotations}")
    
    return challenge_data

def validate_graphic_response(challenge_data, user_order, user_rotations):
    """
    Проверяет правильность ответа пользователя
    
    Args:
        challenge_data: данные challenge
        user_order: порядок, указанный пользователем [1,2,3,4]
        user_rotations: повороты, указанные пользователем [0,90,180,270]
    
    Returns:
        tuple: (bool, str) - результат проверки и сообщение
    """
    correct_order = challenge_data['correct_order']
    correct_rotations = challenge_data['correct_rotations']
    
    print(f"[GRAPHIC AUTH] Проверка:")
    print(f"  Правильный порядок: {correct_order}")
    print(f"  Пользователь: {user_order}")
    print(f"  Правильные повороты: {correct_rotations}")
    print(f"  Пользовательские повороты: {user_rotations}")
    
    # Проверяем порядок
    if user_order != correct_order:
        return False, "Неправильный порядок изображений"
    
    # Проверяем повороты
    if user_rotations != correct_rotations:
        return False, "Неправильные повороты изображений"
    
    return True, "Успешная аутентификация"