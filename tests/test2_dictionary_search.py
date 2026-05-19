"""Тест: влияние размера базы динамических заданий на восстановление пароля
Длина пароля: 8 символов 
Метод атаки: словарь популярных паролей
"""
import os, string, random, time, re
from matplotlib import ticker
import matplotlib.pyplot as plt

""" ГЛОБАЛЬНЫЕ НАСТРОЙКИ """
PASSWORD_LENGTH = 8     # длина пароля
NUM_INTERCEPTS = 1      # количество перехватов
NUM_USERS = 500         # количество пользователей
DICT_WEIGHT = 0.5       # % паролей из словаря
NUM_TASKS = 20          # количество заданий


""" Загрузка словаря популярных паролей """
def load_dictionary(filepath="tests/common_passwords.txt", max_passwords=10000):
    if not os.path.exists(filepath):
        print(f"Файл {filepath} не найден. Используется тестовый словарь")
        test_dict = [
            "password", "12345678", "qwerty123", "abc12345", "letmein",
            "monkey123", "dragon123", "baseball", "football", "superman",
            "trustno1", "iloveyou", "sunshine", "princess", "welcome",
            "whatever", "nicole", "daniel", "babygirl", "happy123"
        ]
        with open(filepath, "w") as f:
            for pwd in test_dict:
                f.write(pwd + "\n")
        return test_dict
    
    with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
        passwords = [line.strip() for line in f.readlines()[:max_passwords]]
    print(f"Загружено {len(passwords)} паролей из словаря")
    return passwords


""" Генерация случайного пароля (буквы нижнего регистра и цифры) """
def generate_random_password(length=PASSWORD_LENGTH):
    # string.ascii_lowercase = "abcdefghijklmnopqrstuvwxyz"
    # string.digits = "0123456789"
    chars = string.ascii_lowercase + string.digits
    result = ""
    for n in range(length):
        result = result + random.choice(chars)
    return result


""" Генерация более реалистичного пароля (часть из словаря, часть случайных) """
def generate_realistic_password(dictionary):
    if random.random() < DICT_WEIGHT:
        # Случайный пароль из словаря + его мутация
        base = random.choice(dictionary)
        # Добавление цифры в конец (не всегда)
        if random.random() < 0.3:
            base = base + str(random.randint(0, 99))
        # Обрезка/достройка до 8 символов
        if len(base) > PASSWORD_LENGTH:
            base = base[:PASSWORD_LENGTH]
        elif len(base) < PASSWORD_LENGTH:
            base = base + ''.join(random.choice(string.digits) for n in range(PASSWORD_LENGTH - len(base)))
        return base.lower()
    else:
        return generate_random_password(PASSWORD_LENGTH)


"""Увеличение каждой цифры на X (циклически)"""
def inc_digits_forward(s: str, x: int) -> str:
    def shift(d: str) -> str:
        return str((int(d) + x) % 10)
    return re.sub(r'\d', lambda m: shift(m.group()), s)


"""Удаление X символа"""
def delete_char_forward(s: str, x: int) -> str:
    if 0 <= x < len(s):
        return s[:x] + s[x+1:]
    return s


"""Замена каждой буквы на ее номер в алфавите"""
def letter_to_number_forward(s: str) -> str:
    result = []
    for ch in s:
        if ch.isalpha():
            result.append(str(ord(ch.lower()) - ord('a') + 1))
        else:
            result.append(ch)
    return ''.join(result)


"""Замена X-й буквы на цифру N """
def replace_letter_with_digit_forward(s: str, x: int, n: int) -> str:
    if not 0 <= n <= 9:
        raise ValueError("N должно быть 0-9")
    letters_found = 0
    result = list(s)
    for i, ch in enumerate(result):
        if ch.isalpha():
            letters_found += 1
            if letters_found == x:
                result[i] = str(n)
                break
    return ''.join(result)


"""Замена X-й цифры на букву N"""
def replace_digit_with_letter_forward(s: str, x: int, letter: str) -> str:
    if len(letter) != 1 or not letter.isalpha():
        raise ValueError("Буква должна быть одна")
    digits_found = 0
    result = list(s)
    for i, ch in enumerate(result):
        if ch.isdigit():
            digits_found += 1
            if digits_found == x:
                result[i] = letter
                break
    return ''.join(result)


"""Сортировка символов в строке по алфавиту"""
def sort_chars_forward(s: str) -> str:
    return ''.join(sorted(s))


"""Постановка X-й буквы заглавной, остальные строчные"""
def make_xth_letter_case_forward(s: str, x: int) -> str:
    letters_found = 0
    result = []
    for ch in s:
        if ch.isalpha():
            letters_found += 1
            if letters_found == x:
                result.append(ch.upper())
            else:
                result.append(ch.lower())
        else:
            result.append(ch)
    return ''.join(result)


"""Генерация базы из N заданий (старая)"""
""" def generate_tasks(n_tasks):
    tasks = []
    for i in range(n_tasks):
        task_type = random.choice(['swap', 'shift', 'reverse'])
        # task_type = random.choice(['swap', 'shift', 'reverse', 'delete'])
        
        if task_type == 'swap':
            pos1 = random.randint(0, PASSWORD_LENGTH-1)
            pos2 = random.randint(0, PASSWORD_LENGTH-1)
            while pos2 == pos1:
                pos2 = random.randint(0, PASSWORD_LENGTH-1)
            tasks.append({
                'id': i,
                'type': 'swap',
                'params': (pos1, pos2)
            })
        
        elif task_type == 'shift':
            delta = random.choice([1, 2, 3, -1, -2])
            tasks.append({
                'id': i,
                'type': 'shift',
                'params': delta
            })
        
        elif task_type == 'reverse':
            tasks.append({
                'id': i,
                'type': 'reverse',
                'params': None
            })
        
        elif task_type == 'delete':
            pos = random.randint(0, PASSWORD_LENGTH-1)
            tasks.append({
                'id': i,
                'type': 'delete',
                'params': pos
            })
        # Замена каждой буквы на ее номер в алфавите
        elif task_type == 'letter_to_number_forward':
            tasks.append({
                'id': i,
                'type': 'letter_to_number_forward',
                'params': None
            })
        # Замена X-й буквы на цифру N
        elif task_type == 'replace_letter_with_digit_forward':
            x = random.randint(0, PASSWORD_LENGTH-1)
            n = random.randint(0, 9)
            tasks.append({
                'id': i,
                'type': 'replace_letter_with_digit_forward',
                'params': (x, n)
            })
        # Замена X-й цифры на букву N
        elif task_type == 'replace_digit_with_letter_forward':
            x = random.randint(0, PASSWORD_LENGTH-1)
            n = random.randint(0, 9)
            tasks.append({
                'id': i,
                'type': 'replace_digit_with_letter_forward',
                'params': (x, n)
            })
    
    return tasks """

"""Генерация базы из N заданий (новая)"""
def generate_tasks(n_tasks: int, stroke = PASSWORD_LENGTH) -> list:
    tasks = []
    
    # Список всех доступных типов заданий
    task_types = [
        'inc_digits',
        'delete_char',
        'letter_to_number',
        'replace_letter_with_digit',
        'replace_digit_with_letter',
        'sort_chars',
        'make_xth_letter_case'
    ]
    
    for i in range(n_tasks):
        task_type = random.choice(task_types)
        
        if task_type == 'inc_digits':
            x = random.randint(1, 9)
            tasks.append({
                'id': i,
                'type': 'inc_digits',
                'params': x
            })
        
        elif task_type == 'delete_char':
            pos = random.randint(0, stroke - 1) if stroke > 0 else 0
            tasks.append({
                'id': i,
                'type': 'delete_char',
                'params': pos
            })
        
        elif task_type == 'letter_to_number':
            tasks.append({
                'id': i,
                'type': 'letter_to_number',
                'params': None
            })
        
        elif task_type == 'replace_letter_with_digit':
            x = random.randint(1, stroke)  # позиция буквы
            n = random.randint(0, 9)  # цифра
            tasks.append({
                'id': i,
                'type': 'replace_letter_with_digit',
                'params': {'x': x, 'n': n}
            })
        
        elif task_type == 'replace_digit_with_letter':
            x = random.randint(1, stroke)  # позиция цифры
            letter = random.choice(string.ascii_letters)
            tasks.append({
                'id': i,
                'type': 'replace_digit_with_letter',
                'params': {'x': x, 'letter': letter}
            })
        
        elif task_type == 'sort_chars':
            tasks.append({
                'id': i,
                'type': 'sort_chars',
                'params': None
            })
        
        elif task_type == 'make_xth_letter_case':
            x = random.randint(1, stroke)  # позиция буквы
            tasks.append({
                'id': i,
                'type': 'make_xth_letter_case',
                'params': x
            })
    
    return tasks

"""Преобразование пароля по заданию (старая)"""
""" def apply_task(password, task):
    if task['type'] == 'swap':
        p1, p2 = task['params']
        lst = list(password)
        if p1 < len(lst) and p2 < len(lst):
            lst[p1], lst[p2] = lst[p2], lst[p1]
        return ''.join(lst)
    
    elif task['type'] == 'shift':
        delta = task['params']
        result = []
        for c in password:
            if c.isalpha():
                base = ord('a')
                new_ord = (ord(c) - base + delta) % 26 + base
                result.append(chr(new_ord))
            elif c.isdigit():
                new_digit = (int(c) + delta) % 10
                result.append(str(new_digit))
            else:
                result.append(c)
        return ''.join(result)
    
    elif task['type'] == 'reverse':
        return password[::-1]
    
    elif task['type'] == 'delete':
        pos = task['params']
        if pos < len(password):
            return password[:pos] + password[pos+1:]
        return password
    
    return password """


"""Преобразование пароля по заданию (новая)"""
def apply_task(stroke: str, task: dict) -> str:    
    if task['type'] == 'inc_digits':
        x = task['params']
        return inc_digits_forward(stroke, x)
    
    elif task['type'] == 'delete_char':
        pos = task['params']
        return delete_char_forward(stroke, pos)
    
    elif task['type'] == 'letter_to_number':
        return letter_to_number_forward(stroke)
    
    elif task['type'] == 'replace_letter_with_digit':
        params = task['params']
        x = params['x']
        n = params['n']
        return replace_letter_with_digit_forward(stroke, x, n)
    
    elif task['type'] == 'replace_digit_with_letter':
        params = task['params']
        x = params['x']
        letter = params['letter']
        return replace_digit_with_letter_forward(stroke, x, letter)
    
    elif task['type'] == 'sort_chars':
        return sort_chars_forward(stroke)
    
    elif task['type'] == 'make_xth_letter_case':
        x = task['params']
        return make_xth_letter_case_forward(stroke, x)
    
    else:
        raise ValueError(f"Неизвестный тип задания: {task['type']}")


"""Обратное преобразование к модернизированному паролю
Возвращает множество возможных исходных паролей
"""
""" def reverse_task(task, observed):
    if task['type'] == 'swap':
        # swap (без изменений)
        p1, p2 = task['params']
        lst = list(observed)
        if p1 < len(lst) and p2 < len(lst):
            lst[p1], lst[p2] = lst[p2], lst[p1]
        return {''.join(lst)}
    
    elif task['type'] == 'shift':
        # shift - противоположный сдвиг
        delta = -task['params']
        result = []
        for c in observed:
            if c.isalpha():
                base = ord('a')
                new_ord = (ord(c) - base + delta) % 26 + base
                result.append(chr(new_ord))
            elif c.isdigit():
                new_digit = (int(c) + delta) % 10
                result.append(str(new_digit))
            else:
                result.append(c)
        return {''.join(result)}
    
    elif task['type'] == 'reverse':
        # reverse обратим
        return {observed[::-1]}
    
    elif task['type'] == 'delete':
        # delete - перебор всех возможных вставок
        pos = task['params']
        candidates = set()
        chars = string.ascii_lowercase + string.digits
        for c in chars:
            candidate = observed[:pos] + c + observed[pos:]
            if len(candidate) == 8:  # только правильной длины
                candidates.add(candidate)
        return candidates
    
    return set() """


def reverse_task(task: dict, observed: str, original_length: int = PASSWORD_LENGTH):    
    if task['type'] == 'inc_digits':
        x = task['params']
        candidates = set()
        
        # Перебираем варианты для каждой цифры
        patterns = []
        for ch in observed:
            if ch.isdigit():
                orig_digit = (int(ch) - x) % 10
                patterns.append([str(orig_digit)])
            else:
                patterns.append([ch])
        
        # Генерируем все комбинации
        def dfs(idx, current):
            if idx == len(patterns):
                candidates.add(''.join(current))
                return
            for option in patterns[idx]:
                dfs(idx + 1, current + [option])
        
        dfs(0, [])
        return candidates
    
    elif task['type'] == 'delete_char':
        pos = task['params']
        candidates = set()
        # Все возможные символы для вставки
        all_chars = string.ascii_lowercase + string.ascii_uppercase + string.digits + '!@#$%^&*()_+-= ,.'
        
        for c in all_chars:
            candidate = observed[:pos] + c + observed[pos:]
            # Если известна исходная длина, фильтруем
            if original_length is None or len(candidate) == original_length:
                candidates.add(candidate)
        
        return candidates
    
    elif task['type'] == 'letter_to_number':
        candidates = set()
        
        # Разбиваем на токены (числа и не-числа)
        tokens = re.findall(r'\d+|[^\d]+', observed)
        
        def expand_tokens(idx, current):
            if idx == len(tokens):
                candidates.add(''.join(current))
                return
            
            token = tokens[idx]
            if token.isdigit():
                num = int(token)
                # Вариант: одна буква
                if 1 <= num <= 26:
                    expand_tokens(idx + 1, current + [chr(ord('a') + num - 1)])
                
                # Вариант: несколько букв (разбиваем число)
                num_str = token
                def split_number(s, start, path):
                    if start == len(s):
                        expand_tokens(idx + 1, current + path)
                        return
                    for end in range(start + 1, min(start + 3, len(s) + 1)):
                        part = int(s[start:end])
                        if 1 <= part <= 26:
                            split_number(s, end, path + [chr(ord('a') + part - 1)])
                split_number(num_str, 0, [])
            else:
                expand_tokens(idx + 1, current + [token])
        
        expand_tokens(0, [])
        
        # Если известна исходная длина, фильтруем
        if original_length:
            candidates = {c for c in candidates if len(c) == original_length}
        
        return candidates
    
    elif task['type'] == 'replace_letter_with_digit':
        params = task['params']
        x = params['x']
        n = params['n']
        candidates = set()
        
        # Все возможные буквы
        letters = string.ascii_lowercase + string.ascii_uppercase
        
        # Находим позицию X-й буквы в наблюдаемой строке
        letters_found = 0
        pos = -1
        for i, ch in enumerate(observed):
            if ch.isalpha():
                letters_found += 1
                if letters_found == x:
                    pos = i
                    break
        
        if pos == -1:
            return candidates
        
        # Пробуем вставить каждую букву на это место
        for letter in letters:
            candidate = observed[:pos] + letter + observed[pos+1:]
            candidates.add(candidate)
        
        return candidates
    
    elif task['type'] == 'replace_digit_with_letter':
        params = task['params']
        x = params['x']
        letter = params['letter']
        candidates = set()
        digits = '0123456789'
        
        # Находим позицию X-й буквы (которая заменила цифру)
        letters_found = 0
        pos = -1
        for i, ch in enumerate(observed):
            if ch.isalpha():
                letters_found += 1
                if letters_found == x:
                    pos = i
                    break
        
        if pos == -1:
            return candidates
        
        # Пробуем вставить каждую цифру
        for digit in digits:
            candidate = observed[:pos] + digit + observed[pos+1:]
            candidates.add(candidate)
        
        return candidates
    
    elif task['type'] == 'sort_chars':
        from itertools import permutations
        
        candidates = set()
        chars = list(observed)
        
        # Все перестановки символов
        if len(chars) <= 7:  # Ограничение для производительности
            for perm in set(permutations(chars)):
                candidate = ''.join(perm)
                # Если известна исходная длина, она совпадает
                if original_length is None or len(candidate) == original_length:
                    candidates.add(candidate)
        else:
            # Для длинных строк - хотя бы исходная
            candidates.add(observed)
        
        return candidates
    
    elif task['type'] == 'make_xth_letter_case':
        x = task['params']
        candidates = set()
        
        # Находим позицию X-й буквы
        letters_found = 0
        pos = -1
        for i, ch in enumerate(observed):
            if ch.isalpha():
                letters_found += 1
                if letters_found == x:
                    pos = i
                    break
        
        if pos == -1:
            return candidates
        
        # Генерируем все варианты регистров
        def generate_variants(idx, current):
            if idx == len(observed):
                candidates.add(''.join(current))
                return
            
            ch = observed[idx]
            if idx == pos:
                # Эта буква стала заглавной
                generate_variants(idx + 1, current + [ch])  # была заглавной
                generate_variants(idx + 1, current + [ch.lower()])  # была строчной
            elif ch.isalpha():
                # Остальные буквы стали строчными
                generate_variants(idx + 1, current + [ch])  # была строчной
                generate_variants(idx + 1, current + [ch.upper()])  # была заглавной
            else:
                generate_variants(idx + 1, current + [ch])
        
        generate_variants(0, [])
        
        # Если известна исходная длина, фильтруем
        if original_length:
            candidates = {c for c in candidates if len(c) == original_length}
        
        return candidates
    
    else:
        # Неизвестный тип задания
        return set()


"""Комбинированный метод:
1. Сначала обратное преобразование (мгновенно)
2. Если кандидатов много — фильтруем по словарю
3. Если словарь не дал результатов — расширяем поиск
"""
def find_candidates_with_dictionary(task, observed, dictionary, max_candidates=1000):
    # 1: обратное преобразование
    candidates = reverse_task(task, observed)
    
    # 2: если один вариант вышел — отлично, пароль нашли
    if len(candidates) == 1:
        return candidates
    
    # 3: если вышло несколько вариантов — проверка по словарю
    dictionary_set = set(dictionary)
    candidates_from_dict = candidates.intersection(dictionary_set)
    
    if candidates_from_dict:
        return candidates_from_dict
    
    # 4: если словарь не помог — возвращаем все получанные варианты
    if len(candidates) > max_candidates:
        return set(list(candidates)[:max_candidates])
    
    return candidates


"""Восстанавление пароля по перехватам, используя словарь
intercepts — список перехваченных входов (задание + преобразовынный пароль)
dictionary — словарь популярных паролей
"""
def recover_password_from_intercepts(intercepts, dictionary):
    if not intercepts:
        return None, 0
    
    # Начинаем с кандидатов от первого перехвата
    task1, obs1 = intercepts[0]
    possible_passwords = find_candidates_with_dictionary(task1, obs1, dictionary)
    
    # Пересекаем с кандидатами от остальных перехватов
    for task, observed in intercepts[1:]:
        candidates_this = find_candidates_with_dictionary(task, observed, dictionary)
        possible_passwords = possible_passwords.intersection(candidates_this)
        
        if len(possible_passwords) <= 1:
            break
        if len(possible_passwords) > 1000:
            # Слишком много кандидатов — ограничиваем
            possible_passwords = set(list(possible_passwords)[:1000])
    
    if len(possible_passwords) == 1:
        return possible_passwords.pop(), 1
    else:
        return None, len(possible_passwords)


""" ЗАПУСК ТЕСТА """
def run_experiment(n_tasks, dictionary, num_users=NUM_USERS, num_intercepts=NUM_INTERCEPTS):
    print(f"Запуск: заданий = {n_tasks}, пользователей = {num_users}, перехватов = {num_intercepts}")
    
    # Создаём базу заданий
    tasks_db = generate_tasks(n_tasks)
    
    recovered_count = 0     # количество восстановленных паролей
    exact_recovered = 0     # восстановлено точно
    total_candidates = 0    # общее число по всем пользователям
    # статистика по слабым/сильным паролям
    stats = {
        'weak_password_recovered': 0, 
        'strong_password_recovered': 0
        }
    
    for user_id in range(num_users):
        # Генерация реалистичного пароля
        real_password = generate_realistic_password(dictionary)
        is_weak = real_password in dictionary
        
        # Симуляция перехвата
        intercepts = []
        for _ in range(num_intercepts):
            task = random.choice(tasks_db)                  # случайное задание из БД
            transformed = apply_task(real_password, task)   # применение задания
            intercepts.append((task, transformed))          # сохранение (задание, результат)
        
        # Атака
        recovered, candidate_count = recover_password_from_intercepts(intercepts, dictionary)
        
        # Проверка успешности атаки
        if recovered == real_password:
            recovered_count += 1
            exact_recovered += 1
            if is_weak:
                stats['weak_password_recovered'] += 1
            else:
                stats['strong_password_recovered'] += 1
        
        # Сбор статистики по всем пользователям
        total_candidates += candidate_count
        
        # if (user_id + 1) % 20 == 0:
        #     print(f"    Прогресс: {user_id + 1}/{num_users}")
    
    recovery_rate = (recovered_count / num_users) * 100
    avg_candidates = total_candidates / num_users
    
    return {
        'n_tasks': n_tasks,
        'n_intercepts': num_intercepts,
        'recovery_rate': recovery_rate,     # процент восстановленных
        'avg_candidates': avg_candidates,   # среднее число кандидатов
        'exact_recovered': exact_recovered, # точных восстановлений
        'weak_recovered': stats['weak_password_recovered'], # из слабых паролей
        'total_users': num_users
    }


""" Построение столбчатой диаграммы восстановления в зависимости от числа заданий 
results: список словарей с ключами 'n_tasks' и 'recovery_rate'
title: заголовок диаграммы
save_path: путь для сохранения
show_values: показывать ли значения над столбцами
"""
def attak_tasks_sucsess_graph(results, title=None, save_path=None, show_values=True):
    x_values = [r['n_tasks'] for r in results]
    y_values = [r['recovery_rate'] for r in results]
    
    plt.figure(figsize=(8, 5))
    bars = plt.bar(x_values, y_values, width=4, color='steelblue', edgecolor='black', linewidth=0.8)
    
    plt.xlabel('Количество заданий', fontsize=11)
    plt.ylabel('Восстановление (%)', fontsize=11)
    plt.ylim(0, 100)
    plt.gca().xaxis.set_major_locator(ticker.MaxNLocator(integer=True))

    if title:
        plt.title(title, fontsize=12)
    
    if show_values:
        for bar, rate in zip(bars, y_values):
            height = bar.get_height()
            plt.text(bar.get_x() + bar.get_width()/2., height + 1,
                    f'{rate:.1f}%', ha='center', va='bottom', fontsize=9)
    
    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
    
    plt.show()


""" Построение столбчатой диаграммы восстановления в зависимости от числа перехватов 
results: список словарей с ключами 'n_intercepts' и 'recovery_rate'
title: заголовок диаграммы
save_path: путь для сохранения
show_values: показывать ли значения над столбцами
"""
def attak_intercepts_sucsess_graph(results, title=None, save_path=None, show_values=True):
    x_values = [r['n_intercepts'] for r in results]
    y_values = [r['recovery_rate'] for r in results]
    
    plt.figure(figsize=(8, 5))
    bars = plt.bar(x_values, y_values, color='steelblue', edgecolor='black', linewidth=0.8)
    
    plt.xlabel('Количество перехватов атакующего', fontsize=11)
    plt.ylabel('Восстановление (%)', fontsize=11)
    plt.ylim(0, 100)
    plt.gca().xaxis.set_major_locator(ticker.MaxNLocator(integer=True))

    if title:
        plt.title(title, fontsize=12)
    
    if show_values:
        for bar, rate in zip(bars, y_values):
            height = bar.get_height()
            plt.text(bar.get_x() + bar.get_width()/2., height + 1,
                    f'{rate:.1f}%', ha='center', va='bottom', fontsize=9)
    
    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
    
    plt.show()


def main_tasks():
    print("ТЕСТ - ВОССТАНОВЛЕНИЕ ПАРОЛЯ СО СЛОВАРЁМ")

    # Загружаем словарь
    dictionary = load_dictionary("tests/common_passwords.txt", max_passwords=10000)

    # Параметры
    tasks_variants = [5, 10, 20, 50, 100]    # общее число заданий
    num_users = NUM_USERS                           # число пользователей
    num_intercepts = NUM_INTERCEPTS                 # количество перехватов
    
    results = []
    
    for n_tasks in tasks_variants:
        print(f"Тест с числом заданий = {n_tasks}")
        start_time = time.time()
        
        result = run_experiment(n_tasks, dictionary, num_users, num_intercepts)
        results.append(result)
        
        elapsed = time.time() - start_time
        print(f"    Результат: {result['recovery_rate']:.1f}% паролей восстановлено")
        print(f"    Точно восстановлено: {result['exact_recovered']}/{num_users}")
        print(f"    Время: {elapsed:.1f} сек")
    
    print("\nИТОГОВЫЕ РЕЗУЛЬТАТЫ\n")
    for r in results:
        print(f"Количество заданий = {r['n_tasks']} \
              Восстановлено паролей = {r['recovery_rate']:.2f}%")
    
    # Диаграмма
    # for r in results:
    #     bar_length = int(r['recovery_rate'] / 2)
    #     bar = "█" * bar_length
    #     print(f"   {r['n_tasks']:>3} заданий: [{bar:<50}] {r['recovery_rate']:.1f}%")
    
    attak_tasks_sucsess_graph(results, "Процент востановления паролей в зависимости от количества заданий")

    # Вывод
    print(f"\nПри длине пароля {PASSWORD_LENGTH} символов и использовании словаря атакующий\
    восстанавливает {results[-1]['recovery_rate']:.1f}% паролей")


def main_intercepts():
    print("ТЕСТ - ВОССТАНОВЛЕНИЕ ПАРОЛЯ СО СЛОВАРЁМ")

    # Загружаем словарь
    dictionary = load_dictionary("tests/common_passwords.txt", max_passwords=10000)

    # Параметры
    tasks_variants = NUM_TASKS                  # общее число заданий
    num_users = NUM_USERS                       # число пользователей
    num_intercepts = [1, 2, 3, 4, 5, 10]      # число перехватов
    
    results = []
    
    for n_intercepts in num_intercepts:
        print(f"Тест с количеством перехватов = {n_intercepts}")
        start_time = time.time()
        
        result = run_experiment(tasks_variants, dictionary, num_users, n_intercepts)
        results.append(result)
        
        elapsed = time.time() - start_time
        print(f"    Результат: {result['recovery_rate']:.1f}% паролей восстановлено")
        print(f"    Точно восстановлено: {result['exact_recovered']}/{num_users}")
        print(f"    Время: {elapsed:.1f} сек")
    
    print("\nИТОГОВЫЕ РЕЗУЛЬТАТЫ\n")
    for r in results:
        print(f"Количество перехватов = {r['n_intercepts']} \
              Восстановлено паролей = {r['recovery_rate']:.2f}%")
    
    # Диаграмма
    # for r in results:
    #     bar_length = int(r['recovery_rate'] / 2)
    #     bar = "█" * bar_length
    #     print(f"   {r['n_intercepts']:>3} перехватов: [{bar:<50}] {r['recovery_rate']:.1f}%")
    
    attak_intercepts_sucsess_graph(results, "Процент востановления паролей в зависимости от количества перехватов атакующего")

    # Вывод
    print(f"\nПри длине пароля {PASSWORD_LENGTH} символов и использовании словаря атакующий\
    восстанавливает {results[-1]['recovery_rate']:.1f}% паролей")


if __name__ == "__main__":
    main_tasks()
    main_intercepts()