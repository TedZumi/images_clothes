"""Тест №2.1: влияние размера базы динамических заданий на восстановление пароля
Длина пароля: 8 символов 
Метод атаки: словарь популярных паролей
"""
import os, string, random, time

""" ГЛОБАЛЬНЫЕ НАСТРОЙКИ """
PASSWORD_LENGTH = 16      # длина пароля
NUM_INTERCEPTS = 1        # количество перехватов
NUM_USERS = 200           # количество пользователей
DICT_WEIGHT = 0.1         # 30% паролей из словаря


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


""" Генерация более реалистичного пароля (50% из словаря, 50% случайный) """
def generate_realistic_password(dictionary):
    if random.random() < DICT_WEIGHT:
        # Случайный пароль из словаря + его мутация
        base = random.choice(dictionary)
        # Добавление цифры в конец (не всегда)
        if random.random() < 0.3:
            base = base + str(random.randint(0, 99))
        # Обрезка/достройка до 8 символов
        if len(base) > 8:
            base = base[:8]
        elif len(base) < 8:
            base = base + ''.join(random.choice(string.digits) for n in range(8 - len(base)))
        return base.lower()
    else:
        return generate_random_password(PASSWORD_LENGTH)


"""Генерация базы из N заданий"""
def generate_tasks(n_tasks):
    tasks = []
    for i in range(n_tasks):
        task_type = random.choice(['swap', 'shift', 'reverse', 'delete'])
        
        if task_type == 'swap':
            pos1 = random.randint(0, 7)
            pos2 = random.randint(0, 7)
            while pos2 == pos1:
                pos2 = random.randint(0, 7)
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
            pos = random.randint(0, 7)
            tasks.append({
                'id': i,
                'type': 'delete',
                'params': pos
            })
    
    return tasks


"""Преобразование пароля по заданию"""
def apply_task(password, task):
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
    
    return password


"""Обратное преобразование к модернизированному паролю
Возвращает множество возможных исходных паролей
"""
def reverse_task(task, observed):
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
    print(f"Запуск: заданий={n_tasks}, пользователей={num_users}, перехватов={num_intercepts}")
    
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
        
        if (user_id + 1) % 20 == 0:
            print(f"    Прогресс: {user_id + 1}/{num_users}")
    
    recovery_rate = (recovered_count / num_users) * 100
    avg_candidates = total_candidates / num_users
    
    return {
        'n_tasks': n_tasks,
        'recovery_rate': recovery_rate,     # процент восстановленных
        'avg_candidates': avg_candidates,   # среднее число кандидатов
        'exact_recovered': exact_recovered, # точных восстановлений
        'weak_recovered': stats['weak_password_recovered'], # из слабых паролей
        'total_users': num_users
    }


def main():
    print("ТЕСТ - ВОССТАНОВЛЕНИЕ ПАРОЛЯ СО СЛОВАРЁМ")

    # Загружаем словарь
    dictionary = load_dictionary("tests/common_passwords.txt", max_passwords=10000)

    # Параметры
    tasks_variants = [5, 10, 20, 50, 100, 200, 300]  # общее число заданий
    num_users = 100                             # число пользователей
    num_intercepts = 3                          # количество перехватов
    
    results = []
    
    for n_tasks in tasks_variants:
        print(f"\Тест с числом заданий = {n_tasks}")
        start_time = time.time()
        
        result = run_experiment(n_tasks, dictionary, num_users, num_intercepts)
        results.append(result)
        
        elapsed = time.time() - start_time
        print(f"    Результат: {result['recovery_rate']:.1f}% паролей восстановлено")
        print(f"    Точное восстановление: {result['exact_recovered']}/{num_users}")
        print(f"    Среднее кандидатов: {result['avg_candidates']:.1f}")
        print(f"    Время: {elapsed:.1f} сек")
    
    # ВЫВОД ТАБЛИЦЫ
    print("\n" + "=" * 70)
    print("ИТОГОВЫЕ РЕЗУЛЬТАТЫ (реалистичная атака, 10 символов)")
    print("=" * 70)
    
    print("\n┌────────────┬──────────────┬─────────────────────┬──────────────┐")
    print("│ N_tasks    │ Восстановлено │ Среднее кандидатов  │ Точных побед │")
    print("├────────────┼──────────────┼─────────────────────┼──────────────┤")
    for r in results:
        print(f"│ {r['n_tasks']:<10} │ {r['recovery_rate']:>12.1f}% │ {r['avg_candidates']:>19.1f} │ {r['exact_recovered']:>12} │")
    print("└────────────┴──────────────┴─────────────────────┴──────────────┘")
    
    # ASCII-график
    print("\n   ГРАФИК ЗАВИСИМОСТИ (чем ниже — тем лучше)")
    print()
    for r in results:
        bar_length = int(r['recovery_rate'] / 2)
        bar = "█" * bar_length
        print(f"   {r['n_tasks']:>3} заданий: [{bar:<50}] {r['recovery_rate']:.1f}%")
    
    # Сравнение с обычным паролем
    print("\n" + "=" * 70)
    print("СРАВНЕНИЕ С ОБЫЧНОЙ ПАРОЛЬНОЙ АУТЕНТИФИКАЦИЕЙ")
    print("=" * 70)
    print("Обычный пароль (атака по словарю):")
    print("  - Слабые пароли (в словаре): 100% восстанавливаются за секунды")
    print("  - Сильные пароли (случайные): 0% (но пользователи редко их выбирают)")
    print()
    print("Ваш модуль (при N_tasks=200):")
    print(f"  - Общий процент восстановления: {results[-1]['recovery_rate']:.1f}%")
    print("  - Даже слабые пароли защищены формульным фактором")
    
    # Вывод
    print("\n" + "=" * 70)
    print("ВЫВОД:")
    print("=" * 70)
    print("1. При длине пароля 8 символов и использовании словаря атакующий")
    print(f"   восстанавливает не более {results[-1]['recovery_rate']:.1f}% паролей")
    print("2. Увеличение базы заданий с 5 до 200 снижает успех атаки")
    print(f"   с {results[0]['recovery_rate']:.1f}% до {results[-1]['recovery_rate']:.1f}%")


if __name__ == "__main__":
    main()