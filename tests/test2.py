import random
import string
import hashlib

# ========== НАСТРОЙКИ ==========
PASSWORD_LENGTH = 10
N_TASKS = 20
NUM_USERS = 100
MAX_ATTEMPTS = 1

# ========== ПРОСТЫЕ ЗАДАНИЯ (ВАШИ) ==========
def generate_simple_tasks(n_tasks):
    tasks = []
    for i in range(n_tasks):
        # task_type = random.choice(['swap', 'shift', 'reverse', 'delete'])
        task_type = random.choice(['swap', 'shift', 'reverse'])
        
        if task_type == 'swap':
            pos1 = random.randint(0, PASSWORD_LENGTH - 1)
            pos2 = random.randint(0, PASSWORD_LENGTH - 1)
            while pos2 == pos1:
                pos2 = random.randint(0, PASSWORD_LENGTH - 1)
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
            pos = random.randint(0, PASSWORD_LENGTH - 1)
            tasks.append({
                'id': i,
                'type': 'delete',
                'params': pos
            })
    
    return tasks

# ========== СЛОЖНЫЕ ЗАДАНИЯ (50% хеш, 50% простые) ==========
def generate_complex_tasks(n_tasks):
    tasks = []
    for i in range(n_tasks):
        # 50% сложных (хеш), 50% простых
        if random.random() < 1:
            # Сложное задание: хеш
            salt = random.randint(1000, 9999)
            tasks.append({
                'id': i,
                'type': 'hash',
                'params': salt,
                'description': f'хеш с солью {salt}'
            })
        else:
            # Простое задание
            task_type = random.choice(['swap', 'shift', 'reverse', 'delete'])
            
            if task_type == 'swap':
                pos1 = random.randint(0, PASSWORD_LENGTH - 1)
                pos2 = random.randint(0, PASSWORD_LENGTH - 1)
                while pos2 == pos1:
                    pos2 = random.randint(0, PASSWORD_LENGTH - 1)
                tasks.append({'type': 'swap', 'params': (pos1, pos2)})
            
            elif task_type == 'shift':
                delta = random.choice([1, 2, 3, -1, -2])
                tasks.append({'type': 'shift', 'params': delta})
            
            elif task_type == 'reverse':
                tasks.append({'type': 'reverse', 'params': None})
            
            elif task_type == 'delete':
                pos = random.randint(0, PASSWORD_LENGTH - 1)
                tasks.append({'type': 'delete', 'params': pos})
    
    return tasks

# ========== ПРИМЕНЕНИЕ ЗАДАНИЙ ==========
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
    
    elif task['type'] == 'hash':
        combined = password + str(task['params'])
        return hashlib.sha256(combined.encode()).hexdigest()[:8]
    
    return password

# ========== ОБРАТНОЕ ПРЕОБРАЗОВАНИЕ ==========
def reverse_task(task, observed):
    if task['type'] == 'swap':
        p1, p2 = task['params']
        lst = list(observed)
        if p1 < len(lst) and p2 < len(lst):
            lst[p1], lst[p2] = lst[p2], lst[p1]
        return {''.join(lst)}
    
    elif task['type'] == 'shift':
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
        return {observed[::-1]}
    
    elif task['type'] == 'delete':
        pos = task['params']
        candidates = set()
        chars = string.ascii_lowercase + string.digits
        for c in chars:
            candidate = observed[:pos] + c + observed[pos:]
            if len(candidate) == PASSWORD_LENGTH:
                candidates.add(candidate)
        return candidates
    
    elif task['type'] == 'hash':
        # Хеш НЕОБРАТИМ! Возвращаем пустое множество
        return set()
    
    return set()

# ========== ГЕНЕРАЦИЯ ПАРОЛЕЙ ==========
def generate_password():
    chars = string.ascii_lowercase + string.digits
    return ''.join(random.choice(chars) for _ in range(PASSWORD_LENGTH))

# ========== ТЕСТ ДЛЯ ОДНОГО ТИПА ЗАДАНИЙ ==========
def run_test(tasks_db, test_name):
    print(f"\nТЕСТ: {test_name}")
    
    buckets = {i: 0 for i in range(1, MAX_ATTEMPTS + 1)}
    not_cracked = 0
    
    for user_id in range(NUM_USERS):
        real_password = generate_password()
        
        intercepts = []
        cracked_at = None
        
        for attempt in range(1, MAX_ATTEMPTS + 1):
            task = random.choice(tasks_db)
            transformed = apply_task(real_password, task)
            intercepts.append((task, transformed))
            
            # Пытаемся восстановить
            candidates = None
            for t, obs in intercepts:
                cand = reverse_task(t, obs)
                if candidates is None:
                    candidates = cand
                else:
                    candidates = candidates.intersection(cand)
                
                if len(candidates) == 0:
                    break
            
            if len(candidates) == 1 and list(candidates)[0] == real_password:
                cracked_at = attempt
                break
        
        if cracked_at:
            buckets[cracked_at] += 1
        else:
            not_cracked += 1
    
    # Вывод результатов
    total_cracked = sum(buckets.values())
    print(f"\nВзломано всего: {total_cracked} из {NUM_USERS} ({total_cracked/NUM_USERS*100:.1f}%)")
    print(f"Не взломано: {not_cracked} ({not_cracked/NUM_USERS*100:.1f}%)")
    
    for attempt in range(1, MAX_ATTEMPTS + 1):
        if buckets[attempt] > 0:
            print(f"  с {attempt} попытки: {buckets[attempt]} пользователей")
    
    return {
        'name': test_name,
        'cracked': total_cracked,
        'cracked_percent': total_cracked/NUM_USERS*100,
        'not_cracked': not_cracked
    }

# ========== ЗАПУСК ==========
def main():
    print("СРАВНЕНИЕ: ПРОСТЫЕ ЗАДАНИЯ vs СЛОЖНЫЕ (ХЕШ)")
    
    # Создаём базы заданий
    simple_tasks = generate_simple_tasks(N_TASKS)
    complex_tasks = generate_complex_tasks(N_TASKS)
    
    """ # Подсчёт типов в сложных заданиях
    hash_count = sum(1 for t in complex_tasks if t['type'] == 'hash')
    print(f"\nСложные задания: {hash_count} хеш-заданий ({hash_count/N_TASKS*100:.0f}%), остальные — простые")
     """
    # Запускаем тесты
    result_simple = run_test(simple_tasks, "ПРОСТЫЕ ЗАДАНИЯ (swap, shift, reverse и др.)")
    result_complex = run_test(complex_tasks, "СЛОЖНЫЕ ЗАДАНИЯ (необратимые хеш-задания)")
    
    # Сравнение
    print("\nСРАВНЕНИЕ РЕЗУЛЬТАТОВ")
    
    print(f"\n┌─────────────────────┬──────────────┬──────────────┐")
    print(f"│                     │ Простые      │ Сложные      │")
    print(f"├─────────────────────┼──────────────┼──────────────┤")
    print(f"│ Взломано            │ {result_simple['cracked_percent']:>11.1f}% │ {result_complex['cracked_percent']:>11.1f}% │")
    print(f"│ Не взломано         │ {100 - result_simple['cracked_percent']:>11.1f}% │ {100 - result_complex['cracked_percent']:>11.1f}% │")
    print(f"└─────────────────────┴──────────────┴──────────────┘")
    
    improvement = result_simple['cracked_percent'] - result_complex['cracked_percent']
    print(f"\nУлучшение: {improvement:.1f}% меньше взломов")
    
    # Вывод
    print("\nВЫВОД:")
    print(f"Простые задания:     взломано {result_simple['cracked_percent']:.1f}% пользователей")
    print(f"Сложные задания:     взломано {result_complex['cracked_percent']:.1f}% пользователей")
    print(f"Разница:             {improvement:.1f}%")
    
    if result_complex['cracked_percent'] < 20:
        print("\nСложные задания дают хорошую защиту (взломано <20%)")


if __name__ == "__main__":
    random.seed(42)
    main()