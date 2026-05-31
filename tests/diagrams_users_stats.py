import json
import matplotlib.pyplot as plt
import numpy as np
from collections import defaultdict
import pandas as pd
from matplotlib.patches import Patch
from matplotlib.lines import Line2D

# Глобальная настройка шрифта
plt.rcParams['font.family'] = 'Times New Roman'
plt.rcParams['font.size'] = 16  # размер шрифта
plt.rcParams['axes.labelsize'] = 16  # размер подписей осей
plt.rcParams['xtick.labelsize'] = 14  # размер цифр на оси X
plt.rcParams['ytick.labelsize'] = 14  # размер цифр на оси Y
plt.rcParams['legend.fontsize'] = 14  # размер легенды

# Круговая диаграмма сравнения среднего времени фактора1 и фактора2
def plot_factor_time_pie_chart(json_file_path):
    # Чтение JSON файла
    with open(json_file_path, 'r', encoding='utf-8') as file:
        data = json.load(file)
    
    # Извлечение средних значений времени
    avg_factor1_time = data['average_time_factor1']
    avg_factor2_time = data['average_time_factor2']
    
    # Данные для диаграммы
    times = [avg_factor1_time, avg_factor2_time]
    labels = ['Фактор 1 (формульный)', 'Фактор 2 (графический)']
    colors = ["#279257", "#792466"]
    
    # Список штриховок для разных секторов (для ЧБ печати)
    hatch_patterns = ['/', '-']
    # Оттенки серого для ЧБ версии
    bw_colors = ['lightgray', 'darkgray']
    
    # Создание фигуры
    fig, ax = plt.subplots(figsize=(10, 8))
    
    # Построение круговой диаграммы
    wedges, texts, autotexts = ax.pie(
        times, 
        labels=None, 
        colors=bw_colors,
        autopct='%1.1f%%',
        startangle=90,
        textprops={'fontsize': 14},
        wedgeprops={'edgecolor': 'black', 'linewidth': 2}
    )
    
    # Штриховка к каждому сектору
    for i, wedge in enumerate(wedges):
        wedge.set_hatch(hatch_patterns[i % len(hatch_patterns)])
    
    # Настройка отображения процентов
    for autotext in autotexts:
        autotext.set_color('white')
        autotext.set_fontweight('bold')
        autotext.set_fontsize(28)
    
    """ # Добавление заголовка
    ax.set_title('Распределение общего времени аутентификации по факторам', 
                 fontsize=18, fontweight='bold', pad=10, loc='center') """
    
    """ 
    # Элементы легенды с образцами штриховки
    legend_elements = []
    for i, (label, time, hatch, color) in enumerate(zip(labels, times, hatch_patterns, bw_colors)):
        # Создаем прямоугольник с соответствующей штриховкой
        legend_elements.append(
            Patch(facecolor=color, 
                hatch=hatch,
                edgecolor='black',
                linewidth=1,
                label=f'{label}: {time:.1f} сек')
        )
    
    # Легенда
    legend = ax.legend(handles=legend_elements,
                    title="Факторы аутентификации",
                    loc="center left",
                    bbox_to_anchor=(1, 0, 0.9, 1),
                    fontsize=13,
                    title_fontsize=15,
                    frameon=True,
                    framealpha=0.7,
                    edgecolor='black',
                    handletextpad=1.0,     # расстояние между прямоугольником и текстом
                    borderpad=1.0,         # отступ от границы легенды
                    labelspacing=1.5,      # расстояние между строками
                    handlelength=3.0,      # длина прямоугольника 
                    handleheight=3.0)      # высота прямоугольника  """
    
    ax.axis('equal')
    
    """ # Подпись с общим временем
    total_time = avg_factor1_time + avg_factor2_time
    plt.figtext(0.6, 0.1, f'Общее среднее время: {total_time:.1f} секунд', 
                ha='center', fontsize=16, style='italic') """
    
    plt.tight_layout()
    plt.show()
    
    # Вывод данных в консоль
    print("Анализ времени аутентификации")
    print(f"Среднее время Factor 1: {avg_factor1_time:.1f} секунд")
    print(f"Среднее время Factor 2: {avg_factor2_time:.1f} секунд")
    print(f"Разница: {abs(avg_factor1_time - avg_factor2_time):.1f} секунд")


# Круговая диаграмма соотношения успешных и неудачных попыток аутентификации
def plot_factor_success_fail_pie_chart(json_file_path):
    with open(json_file_path, 'r', encoding='utf-8') as file:
        data = json.load(file)
    
    total_attempts = data['total_attempts']
    successful_logins = data['successful_logins']
    failed_logins = data['failed_logins']
    
    fig, ax = plt.subplots(figsize=(8, 8))
    
    sizes = [successful_logins, failed_logins]
    labels = [f'Успешно\n{successful_logins}', f'Неудачно\n{failed_logins}']
    colors = ['#2ECC71', '#E74C3C']
    
    ax.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%', startangle=90)
    ax.set_title(f'Статистика аутентификации\nВсего попыток: {total_attempts}', 
                 fontsize=14, fontweight='bold')
    
    plt.tight_layout()
    plt.show()


# Анализ зависимости времени аутентификации от номера попытки
def auth_time_vs_attempts(json_file_path):
    with open(json_file_path, 'r', encoding='utf-8') as file:
        data = json.load(file)
    
    # Анализ данных по пользователям
    users_data = defaultdict(list)
    
    # Сбор данных по каждому пользователю
    for log in data['detailed_logs']:
        email = log['email']
        total_time = log['factor1_time'] + log['factor2_time']
        errors = log['factor1_errors'] + log['factor2_errors']
        success = log['success']
        
        users_data[email].append({
            'total_time': total_time,
            'factor1_time': log['factor1_time'],
            'factor2_time': log['factor2_time'],
            'errors': errors,
            'success': success
        })
    
    # Подготовка данных для графика
    all_attempts_times = []
    avg_times_by_attempt = defaultdict(list)
    
    # Анализ каждого пользователя
    for email, attempts in users_data.items():
        attempt_numbers = list(range(1, len(attempts) + 1))
        times = [attempt['total_time'] for attempt in attempts]
        
        # Фиксация времени по номерам попыток
        for i, time in enumerate(times):
            avg_times_by_attempt[i+1].append(time)
        
        all_attempts_times.append((attempt_numbers, times, email))
    
    attempt_numbers_avg = sorted(avg_times_by_attempt.keys())
    avg_times = [np.mean(avg_times_by_attempt[n]) for n in attempt_numbers_avg]
    # Вывод статистики в консоль
    print("Анализ времени по попыткам")
    
    print("\nСреднее время по попыткам:")
    print(f"{'Попытка':<10} {'Среднее время':<15} {'Станд. отклонение':<20} {'Кол-во данных':<15}")
    
    for attempt_num in attempt_numbers_avg:
        avg_time = np.mean(avg_times_by_attempt[attempt_num])
        std_time = np.std(avg_times_by_attempt[attempt_num])
        count = len(avg_times_by_attempt[attempt_num])
        print(f"{attempt_num:<10} {avg_time:<15.2f} {std_time:<20.2f} {count:<15}")
    
    # Расчет улучшения от первой к последней попытке
    print("\nПрогресс пользователей:")
    
    for email, attempts in users_data.items():
        if len(attempts) >= 2:
            first_time = attempts[0]['total_time']
            last_time = attempts[-1]['total_time']
            improvement = ((first_time - last_time) / first_time) * 100
            
            print(f"{email.split('@')[0]:<20}")
            print(f"    1-я попытка: {first_time:.1f} сек")
            print(f"    Последняя попытка: {last_time:.1f} сек")
            print(f"    Улучшение: {improvement:.1f}%")
            print(f"    Кол-во попыток: {len(attempts)}")
            print()
    
    # Расчет общей статистики улучшения
    if len(attempt_numbers_avg) >= 2:
        first_avg = avg_times[0]
        last_avg = avg_times[-1]
        overall_improvement = ((first_avg - last_avg) / first_avg) * 100
        
        print(f"\nОбщий прогресс:")
        print(f"Среднее время на 1-ю попытку: {first_avg:.2f} сек")
        print(f"Среднее время на последнюю попытку: {last_avg:.2f} сек")
        print(f"Общее улучшение: {overall_improvement:.1f}%")
        print(f"Среднее улучшение на попытку: {overall_improvement/(len(attempt_numbers_avg)-1):.1f}%")


# График тренда времени по попыткам (с обработкой аномалий)
def plot_simple_time_trend_anom(json_file_path):
    with open(json_file_path, 'r', encoding='utf-8') as file:
        data = json.load(file)

    users_data = defaultdict(list)

    for log in data['detailed_logs']:
        email = log['email']
        total_time = log['factor1_time'] + log['factor2_time']
        users_data[email].append(total_time)

    # Средние значения по попыткам
    max_attempts = max(len(times) for times in users_data.values())
    avg_by_attempt = []
    attempt_counts = []

    for i in range(max_attempts):
        attempt_times = []
        for times in users_data.values():
            if i < len(times):
                attempt_times.append(times[i])
        if attempt_times:
            avg_by_attempt.append(np.mean(attempt_times))
            attempt_counts.append(len(attempt_times))

    # Построение графика
    plt.figure(figsize=(9, 7))

    x_full = range(1, len(avg_by_attempt) + 1)
    step = 3  # Берем каждую 2-ю точку
    x_filtered = x_full[::step]
    y_filtered = avg_by_attempt[::step]

    # График средних значений (с выбранными точками)
    plt.plot(x_filtered, y_filtered, 
            marker='o', linewidth=2, markersize=5, color='black', 
            label='Среднее время', zorder=3)

    # Линия тренда
    z = np.polyfit(x_full, avg_by_attempt, 1)
    p = np.poly1d(z)
    plt.plot(x_full, p(x_full), 
            "--", color='gray', linewidth=3, alpha=0.8, 
            label=f'Тренд: y={z[0]:.2f}x+{z[1]:.2f}')

    plt.xlabel('Номер попытки', fontsize=16, fontweight='bold')
    plt.ylabel('Среднее время аутентификации (секунды)', fontsize=16, fontweight='bold')
    # Заголовок закомментирован
    # plt.title('Тренд времени аутентификации по попыткам', fontsize=16, fontweight='bold', pad=15)
    plt.grid(True, alpha=0.3)
        
    for i, (x, y) in enumerate(zip(x_filtered, y_filtered)):
        # Определяем вертикальное смещение
        if i < len(y_filtered) - 1:
            next_y = y_filtered[i+1]
            if abs(next_y - y) < 0.5:
                offset = 0.4
            else:
                offset = 0.3 if next_y > y else -0.3
        else:
            offset = 0.3
        
        # Получаем границы графика
        y_min, y_max = plt.ylim()
        x_min, x_max = plt.xlim()
        
        # Корректируем вертикальную позицию, чтобы текст не выходил за границы
        text_y = y + offset
        margin_y = (y_max - y_min) * 0.05
        
        if text_y > y_max - margin_y:
            text_y = y - offset
            if text_y < y_min + margin_y:
                text_y = y
            va = 'top' if text_y > y else 'bottom'
        elif text_y < y_min + margin_y:
            text_y = y + abs(offset)
            va = 'bottom'
        else:
            va = 'bottom' if offset > 0 else 'top'
        
        # Корректируем горизонтальную позицию для крайних точек
        margin_x = (x_max - x_min) * 0.05
        
        if x <= x_min + margin_x:  # левый край
            ha = 'left'
            x_offset = 0.15
        elif x >= x_max - margin_x:  # правый край
            ha = 'right'
            x_offset = -0.15
        else:
            ha = 'center' if offset > 0 else 'right'
            x_offset = 0
        
        plt.text(x + x_offset, text_y, f'{y:.1f}', 
                ha=ha, va=va, 
                fontweight='bold',
                fontsize=16)

    plt.tight_layout()
    plt.show()

    # Вывод статистики
    print(f"Анализ времени аутентификации (после удаления аномалий)")
    print(f"Количество пользователей: {len(users_data)}")
    print(f"Количество попыток: {max_attempts}")
    print(f"Начальное среднее время: {avg_by_attempt[0]:.1f} сек")
    print(f"Конечное среднее время: {avg_by_attempt[-1]:.1f} сек")
    print(f"Общее улучшение: {avg_by_attempt[0] - avg_by_attempt[-1]:.1f} сек")


# Обработка аномалий
def error_data(json_file_path):
    with open(json_file_path, 'r', encoding='utf-8') as file:
        data = json.load(file)

    # Группировка данных по пользователям
    users_attempts = defaultdict(list)

    for log in data['detailed_logs']:
        email = log['email']
        total_time = log['factor1_time'] + log['factor2_time']
        
        # Номер попытки для пользователя
        attempt_num = len(users_attempts[email]) + 1
        users_attempts[email].append({
            'attempt': attempt_num,
            'time': total_time,
            'timestamp': log.get('timestamp', None)
        })

    # Показ первых 3х пользователей для примера
    for email, attempts in list(users_attempts.items())[:3]:
        print(f"\n{email}:")
        for att in attempts:
            print(f"  Попытка {att['attempt']}: {att['time']:.1f} сек")

    # Анализ аномалий по номерам попыток (учитывая, что у разных пользователей 
    # номера попыток могут не совпадать)
    print("\nАнализ аномальных значений")

    # Сбор данных по номерам попыток
    max_attempts = max(len(attempts) for attempts in users_attempts.values())
    attempts_by_number = [[] for _ in range(max_attempts)]

    for email, attempts in users_attempts.items():
        for attempt_data in attempts:
            attempt_num = attempt_data['attempt'] - 1  # переводим в индекс
            attempts_by_number[attempt_num].append(attempt_data['time'])

    # Поиск аномалий
    anomalies = []
    for i, attempt_times in enumerate(attempts_by_number):
        if len(attempt_times) > 1:  # Нужно хотя бы 2 значения
            q1 = np.percentile(attempt_times, 25)
            q3 = np.percentile(attempt_times, 75)
            iqr = q3 - q1
            lower_bound = q1 - 1.5 * iqr
            upper_bound = q3 + 1.5 * iqr
            
            for email, attempts in users_attempts.items():
                for attempt_data in attempts:
                    if attempt_data['attempt'] - 1 == i:
                        time = attempt_data['time']
                        if time > upper_bound or time < lower_bound:
                            anomalies.append({
                                'attempt': i + 1,
                                'email': email,
                                'time': time,
                                'upper_bound': upper_bound,
                                'lower_bound': lower_bound,
                                'median': np.median(attempt_times)
                            })

    # Вывод аномалий
    if anomalies:
        print("\nНайдены следующие аномальные значения:\n")
        for a in anomalies:
            print(f"{a['attempt']}-я попытка пользователя {a['email']}:")
            print(f"  Время: {a['time']:.1f} сек")
            print(f"  Норма: [{a['lower_bound']:.1f}, {a['upper_bound']:.1f}]")
            print(f"  Отклонение: {a['time'] - a['median']:.1f} сек")
            print()
    else:
        print("\nАномалий не найдено")


    # Подробно пользователи с аномальными значениями
    users_with_anomalies = set()
    for a in anomalies:
        users_with_anomalies.add(a['email'])

    for email in users_with_anomalies:
        print(f"\nПользователь: {email}")
        attempts = users_attempts[email]
        times = [att['time'] for att in attempts]
        print(f"  Всего попыток: {len(attempts)}")
        print(f"  Времена: {', '.join([f'{t:.1f}' for t in times])}")
        
        # Аномальные попытки у пользователя
        user_anomalies = [a for a in anomalies if a['email'] == email]
        for a in user_anomalies:
            print(f"\n{a['attempt']}-я попытка: {a['time']:.1f} сек")
            print(f"Нормальный диапазон для {a['attempt']}-й попытки: [{a['lower_bound']:.1f}, {a['upper_bound']:.1f}]")


if __name__ == "__main__":
    json_file = "auth_statistics.json"
    
    # КД сравнения среднего времени фактора1 и фактора2
    # plot_factor_time_pie_chart(json_file)

    # КД успешных/неудачных попыток
    # plot_factor_success_fail_pie_chart(json_file)

    # Анализ зависимости времени аутентификации от номера попытки
    # auth_time_vs_attempts(json_file)

    # Тренд времени по попыткам
    # plot_simple_time_trend_anom(json_file)
    
    # Аномалии
    error_data(json_file)