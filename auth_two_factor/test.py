import random
import string

# ========== НАСТРОЙКИ ==========
PASSWORD_LENGTH = 16
N_TASKS = 50
NUM_USERS = 50
MAX_ATTEMPTS = 3

# ========== ГЕНЕРАЦИЯ ЗАДАНИЙ (ВАШИ) ==========
def generate_tasks(n_tasks):
    tasks = []
    for i in range(n_tasks):
        task_type = random.choice(['swap', 'shift', 'reverse', 'delete'])
        
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
    
    return set()

# ========== ГЕНЕРАЦИЯ ПАРОЛЕЙ ==========
def generate_password():
    chars = string.ascii_lowercase + string.digits
    return ''.join(random.choice(chars) for _ in range(PASSWORD_LENGTH))

# ========== ОСНОВНОЙ ТЕСТ ==========
def main():
    print("=" * 60)
    print("ТЕСТ: каждый пользователь — в одну кучку")
    print("=" * 60)
    
    # Создаём базу заданий
    tasks_db = generate_tasks(N_TASKS)
    print(f"Создано заданий: {len(tasks_db)}")
    
    # Кучки
    buckets = {i: [] for i in range(1, MAX_ATTEMPTS + 1)}
    not_cracked = []
    
    for user_id in range(NUM_USERS):
        real_password = generate_password()
        print(f"\n[{user_id+1}] Пароль: {real_password}")
        
        intercepts = []
        cracked_at = None
        
        for attempt in range(1, MAX_ATTEMPTS + 1):
            # Новый перехват
            task = random.choice(tasks_db)
            transformed = apply_task(real_password, task)
            intercepts.append((task, transformed))
            
            # Пытаемся восстановить по всем накопленным перехватам
            candidates = None
            for t, obs in intercepts:
                cand = reverse_task(t, obs)
                if candidates is None:
                    candidates = cand
                else:
                    candidates = candidates.intersection(cand)
                
                if len(candidates) == 0:
                    break
            
            # Проверяем, восстановлен ли пароль
            if len(candidates) == 1:
                recovered = list(candidates)[0]
                if recovered == real_password:
                    cracked_at = attempt
                    break
        
        if cracked_at:
            buckets[cracked_at].append(real_password)
            print(f"  → ВЗЛОМАН на попытке {cracked_at}")
        else:
            not_cracked.append(real_password)
            print(f"  → НЕ ВЗЛОМАН за {MAX_ATTEMPTS} попыток")
    
    # ВЫВОД РЕЗУЛЬТАТОВ
    print("\n" + "=" * 60)
    print("РЕЗУЛЬТАТЫ (каждый пользователь в одной кучке)")
    print("=" * 60)
    
    for attempt in range(1, MAX_ATTEMPTS + 1):
        if buckets[attempt]:
            print(f"Кучка {attempt} (с {attempt} попытки): {len(buckets[attempt])} пользователей")
    
    if not_cracked:
        print(f"\nНе взломаны: {len(not_cracked)} пользователей")
    
    total = sum(len(buckets[i]) for i in buckets) + len(not_cracked)
    print(f"\nВсего: {total} пользователей")
    print("✅ Сумма корректна" if total == NUM_USERS else "❌ Ошибка в сумме")

if __name__ == "__main__":
    main()