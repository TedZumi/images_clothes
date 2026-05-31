"""Тест №2.2: Влияние ограничения количества попыток входа на восстановление пароля
"""
import os, string, random
from collections import Counter


PASSWORD_LENGTH = 10      # длина пароля
N_TASKS = 50              # фиксированное количество заданий
DICT_WEIGHT = 0.3         # 30% паролей из словаря
NUM_USERS = 300           # количество пользователей
MAX_INTERCEPTS = 10  # сколько максимум перехватов проверяем

def get_dictionary():
    dict_file = "tests/common_passwords.txt"
    
    if os.path.exists(dict_file):
        with open(dict_file, "r", encoding="utf-8", errors="ignore") as f:
            passwords = [line.strip() for line in f.readlines()]
        print(f"Загружено {len(passwords)} паролей из {dict_file}")
        return passwords
    
    # Если файла нет — создаём тестовый словарь
    print(f"Файл {dict_file} не найден. Используется тестовый словарь")
    test_dict = [
        "password", "12345678", "qwerty123", "abc12345", "letmein",
        "monkey123", "dragon123", "baseball", "football", "superman",
        "trustno1", "iloveyou", "sunshine", "princess", "welcome",
        "whatever", "nicole", "daniel", "babygirl", "happy123"
    ]
    with open(dict_file, "w") as f:
        for pwd in test_dict:
            f.write(pwd + "\n")
    print(f"Создан словарь: {len(test_dict)} паролей")
    return test_dict


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


"""Нахождение возможных вариантов с фильтрацией по словарю"""
def find_candidates(task, observed, dictionary):
    candidates = reverse_task(task, observed)
    
    dictionary_set = set(dictionary)
    candidates_from_dict = candidates.intersection(dictionary_set)
    
    if candidates_from_dict:
        return candidates_from_dict
    
    if len(candidates) > 1000:
        return set(list(candidates)[:1000])
    
    return candidates


"""Восстановление пароля по перехватам 
Возвращает: (восстановлен_ли, на_каком_шаге)"""
def recover_password_with_cumulative_intercepts(intercepts, dictionary):
    if not intercepts:
        return False, None
    
    # Начинаем с первого перехвата
    task1, obs1 = intercepts[0]
    possible = find_candidates(task1, obs1, dictionary)
    
    # Проверяем, восстановлен ли после 1 перехвата
    if len(possible) == 1:
        return True, 1
    
    # Добавляем перехваты по одному
    for step in range(1, len(intercepts)):
        task, observed = intercepts[step]
        candidates_this = find_candidates(task, observed, dictionary)
        possible = possible.intersection(candidates_this)
        
        if len(possible) == 0:
            return False, None  # пересечение пусто — не восстановить
        if len(possible) == 1:
            return True, step + 1  # восстановлен на этом шаге
    
    return False, None  # не восстановлен даже после всех перехватов


def generate_random_password(length=PASSWORD_LENGTH):
    chars = string.ascii_lowercase + string.digits
    return ''.join(random.choice(chars) for _ in range(length))


def generate_realistic_password(dictionary):
    if random.random() < DICT_WEIGHT:
        base = random.choice(dictionary)
        if len(base) > PASSWORD_LENGTH:
            base = base[:PASSWORD_LENGTH]
        elif len(base) < PASSWORD_LENGTH:
            base = base + ''.join(random.choice(string.digits) for _ in range(PASSWORD_LENGTH - len(base)))
        return base.lower()
    else:
        return generate_random_password(PASSWORD_LENGTH)


"""Запускает тест для заданного количества попыток"""
def run_distribution_test():
    """
    Запускает тест распределения перехватов
    """
    print("=" * 70)
    print("ТЕСТ №2.3: РАСПРЕДЕЛЕНИЕ ПЕРЕХВАТОВ, НЕОБХОДИМЫХ ДЛЯ ВЗЛОМА")
    print("=" * 70)
    print(f"Параметры: N_tasks={N_TASKS}, длина пароля={PASSWORD_LENGTH}")
    print(f"Словарных паролей: {DICT_WEIGHT*100}%")
    print(f"Пользователей: {NUM_USERS}, макс. перехватов: {MAX_INTERCEPTS}")
    print("=" * 70)
    
    # Загружаем словарь
    dictionary = get_dictionary()
    
    # Создаём базу заданий
    tasks_db = generate_tasks(N_TASKS)
    
    # Выводим распределение типов заданий
    type_counts = Counter([t['type'] for t in tasks_db])
    print(f"\n📚 Распределение типов заданий (N_tasks={N_TASKS}):")
    for t, count in type_counts.items():
        print(f"   {t}: {count} шт. ({count/N_TASKS*100:.0f}%)")
    
    # Результаты
    recovery_at_step = {i: 0 for i in range(1, MAX_INTERCEPTS + 1)}
    not_recovered = 0
    weak_passwords = 0
    strong_passwords = 0
    weak_recovered = 0
    strong_recovered = 0
    
    print(f"\n🔄 Запуск теста на {NUM_USERS} пользователях...")
    
    for user_id in range(NUM_USERS):
        # Генерируем пользователя
        real_password = generate_realistic_password(dictionary)
        is_weak = real_password in dictionary
        
        if is_weak:
            weak_passwords += 1
        else:
            strong_passwords += 1
        
        # Генерируем последовательные перехваты (до MAX_INTERCEPTS)
        intercepts = []
        for i in range(MAX_INTERCEPTS):
            task = random.choice(tasks_db)
            transformed = apply_task(real_password, task)
            intercepts.append((task, transformed))
        
        # Пытаемся восстановить
        recovered, step = recover_password_with_cumulative_intercepts(intercepts, dictionary)
        
        if recovered:
            recovery_at_step[step] += 1
            if is_weak:
                weak_recovered += 1
            else:
                strong_recovered += 1
        else:
            not_recovered += 1
        
        # Прогресс
        if (user_id + 1) % 20 == 0:
            print(f"   Обработано {user_id + 1}/{NUM_USERS} пользователей...")
    
    # ============================================================
    # ВЫВОД РЕЗУЛЬТАТОВ
    # ============================================================
    
    print("\n" + "=" * 70)
    print("РЕЗУЛЬТАТЫ ТЕСТА")
    print("=" * 70)
    
    print("\n📊 РАСПРЕДЕЛЕНИЕ ПО КОЛИЧЕСТВУ ПЕРЕХВАТОВ:")
    print("┌─────────────────────────┬──────────────┬────────────┐")
    print("│ Перехватов для взлома   │ Пользователей │    Доля    │")
    print("├─────────────────────────┼──────────────┼────────────┤")
    
    cumulative = 0
    for step in range(1, MAX_INTERCEPTS + 1):
        count = recovery_at_step[step]
        if count > 0:
            cumulative += count
            print(f"│ {step:^23} │ {count:>12} │ {count/NUM_USERS*100:>9.1f}% │")
    
    print("├─────────────────────────┼──────────────┼────────────┤")
    print(f"│ {'Не взломаны':^23} │ {not_recovered:>12} │ {not_recovered/NUM_USERS*100:>9.1f}% │")
    print("└─────────────────────────┴──────────────┴────────────┘")
    
    # Статистика по слабым/сильным паролям
    print("\n📊 СТАТИСТИКА ПО ТИПАМ ПАРОЛЕЙ:")
    print(f"   Слабых паролей (из словаря):  {weak_passwords} ({weak_passwords/NUM_USERS*100:.1f}%)")
    print(f"   Сильных паролей (случайные):  {strong_passwords} ({strong_passwords/NUM_USERS*100:.1f}%)")
    print(f"   Взломано слабых:             {weak_recovered} ({weak_recovered/weak_passwords*100 if weak_passwords > 0 else 0:.1f}%)")
    print(f"   Взломано сильных:            {strong_recovered} ({strong_recovered/strong_passwords*100 if strong_passwords > 0 else 0:.1f}%)")
    
    # Накопительный график
    print("\n📈 НАКОПИТЕЛЬНЫЙ ГРАФИК (% взломанных аккаунтов):")
    print("   (сколько аккаунтов взломано после N перехватов)")
    print()
    
    cumulative_percent = 0
    for step in range(1, MAX_INTERCEPTS + 1):
        cumulative_percent += recovery_at_step[step] / NUM_USERS * 100
        bar_length = int(cumulative_percent / 2)
        bar = "█" * bar_length
        print(f"   После {step:2} перехвата(ов): {cumulative_percent:5.1f}% [{bar:<50}]")
    
    # Итоговый вывод
    print("\n" + "=" * 70)
    print("ВЫВОДЫ:")
    print("=" * 70)
    
    if recovery_at_step[1] > 0:
        print(f"1. {recovery_at_step[1]} пользователей ({recovery_at_step[1]/NUM_USERS*100:.1f}%) — взломаны после 1 перехвата")
    
    first_three = sum(recovery_at_step[i] for i in range(1, 4))
    print(f"2. После 3 перехватов взломано: {first_three} пользователей ({first_three/NUM_USERS*100:.1f}%)")
    
    print(f"3. {not_recovered} пользователей ({not_recovered/NUM_USERS*100:.1f}%) — не взломаны даже после {MAX_INTERCEPTS} перехватов")
    
    if weak_passwords > 0:
        print(f"4. Слабые пароли взламываются чаще: {weak_recovered/weak_passwords*100:.1f}% против {strong_recovered/strong_passwords*100:.1f}% у сильных")
    
    # Рекомендация
    print("\n📌 РЕКОМЕНДАЦИЯ:")
    if recovery_at_step[1] > NUM_USERS * 0.3:
        print("   ⚠️ Много пользователей взламываются с 1 перехвата → нужно усложнять задания")
    elif not_recovered > NUM_USERS * 0.5:
        print("   ✅ Более половины пользователей не взломаны даже после 10 перехватов")
    else:
        print("   📊 Результаты в ожидаемом диапазоне")
    
    """ # Сохраняем результаты
    with open("results/test_2c_distribution.txt", "w", encoding="utf-8") as f:
        f.write("РЕЗУЛЬТАТЫ ТЕСТА №2.3 (распределение перехватов)\n")
        f.write("=" * 60 + "\n")
        f.write(f"N_tasks = {N_TASKS}\n")
        f.write(f"Длина пароля = {PASSWORD_LENGTH}\n")
        f.write(f"Словарных паролей = {DICT_WEIGHT*100}%\n")
        f.write(f"Пользователей = {NUM_USERS}\n\n")
        
        f.write("Распределение:\n")
        for step in range(1, MAX_INTERCEPTS + 1):
            if recovery_at_step[step] > 0:
                f.write(f"  {step} перехват(ов): {recovery_at_step[step]} ({recovery_at_step[step]/NUM_USERS*100:.1f}%)\n")
        f.write(f"  Не взломаны: {not_recovered} ({not_recovered/NUM_USERS*100:.1f}%)\n")
    
    print("\n✅ Результаты сохранены в results/test_2c_distribution.txt") """
    
    return recovery_at_step, not_recovered



def main():
    print("=" * 70)
    print("ТЕСТ №2.2: ВЛИЯНИЕ ОГРАНИЧЕНИЯ ПОПЫТОК ВХОДА")
    print("=" * 70)
    print(f"Параметры: N_tasks={N_TASKS}, длина пароля={PASSWORD_LENGTH}")
    print(f"Словарных паролей: {DICT_WEIGHT*100}%, пользователей: {NUM_USERS}")
    print("=" * 70)
    
    # Загружаем словарь
    dictionary = get_dictionary()
    
    # Создаём базу заданий (фиксированную для всех экспериментов)
    tasks_db = generate_tasks(N_TASKS)
    
    # Выводим распределение типов заданий
    type_counts = Counter([t['type'] for t in tasks_db])
    print(f"\nРаспределение типов заданий (N_tasks={N_TASKS}):")
    for t, count in type_counts.items():
        print(f"  {t}: {count} шт. ({count/N_TASKS*100:.0f}%)")
    
    results = []
    
    print("\n▶ Запуск экспериментов:")
    print("┌─────────────────┬──────────────┬──────────────┐")
    print("│ Попыток (перехватов) │ Восстановлено │ Точных побед │")
    print("├─────────────────┼──────────────┼──────────────┤")
    
    for attempts in ATTEMPTS_VARIANTS:
        print(f"│ {attempts:^15} │ ", end="", flush=True)
        
        result = run_experiment(attempts, dictionary, tasks_db)
        results.append(result)
        
        print(f"{result['recovery_rate']:>12.1f}% │ {result['exact_recovered']:>12} │")
    
    print("└─────────────────┴──────────────┴──────────────┘")
    
    # ASCII-график
    print("\n📊 ГРАФИК ЗАВИСИМОСТИ ОТ КОЛИЧЕСТВА ПЕРЕХВАТОВ")
    print()
    
    max_rate = max(r['recovery_rate'] for r in results)
    
    for r in results:
        bar_length = int(r['recovery_rate'] / max_rate * 30)
        bar = "█" * bar_length
        print(f"   {r['attempts_limit']:2} перехвата(ов): [{bar:<30}] {r['recovery_rate']:.1f}%")
    
    # Выводы
    print("\n" + "=" * 70)
    print("ВЫВОДЫ:")
    print("=" * 70)
    
    first = results[0]
    last = results[-1]
    
    print(f"1. При 1 перехвате: {first['recovery_rate']:.1f}% восстановления")
    print(f"2. При {last['attempts_limit']} перехватах: {last['recovery_rate']:.1f}% восстановления")
    print(f"3. Снижение: {first['recovery_rate'] - last['recovery_rate']:.1f}%")
    
    # Рекомендация
    print("\n📌 РЕКОМЕНДАЦИЯ:")
    for r in results:
        if r['recovery_rate'] < 40:
            print(f"   ✅ Оптимально: ограничить до {r['attempts_limit']} попыток")
            print(f"      (восстановление только {r['recovery_rate']:.1f}%)")
            break
    else:
        print(f"   ⚠️ Даже при {results[-1]['attempts_limit']} попытках восстановление {results[-1]['recovery_rate']:.1f}%")
        print(f"   → Рекомендуется добавить необратимые задания")
    
    # # Сохраняем результаты
    # with open("results/test_2b_results.txt", "w", encoding="utf-8") as f:
    #     f.write("РЕЗУЛЬТАТЫ ТЕСТА №2.2 (ограничение попыток)\n")
    #     f.write("=" * 60 + "\n")
    #     f.write(f"N_tasks = {N_TASKS}\n")
    #     f.write(f"Длина пароля = {PASSWORD_LENGTH}\n")
    #     f.write(f"Словарных паролей = {DICT_WEIGHT*100}%\n\n")
        
    #     for r in results:
    #         f.write(f"Перехватов: {r['attempts_limit']} → {r['recovery_rate']:.1f}% восстановления\n")
    
    # print("\n✅ Результаты сохранены в results/test_2b_results.txt")


if __name__ == "__main__":
    # random.seed(42)  # для воспроизводимости
    run_distribution_test()