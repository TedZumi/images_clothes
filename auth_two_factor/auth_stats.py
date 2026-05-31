import json
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import os
import seaborn as sns

# Настройки стиля графиков
plt.style.use('seaborn-v0_8-darkgrid')
sns.set_palette("husl")


""" Загрузка статистики из JSON файла """
def load_statistics(filename='auth_statistics.json'):
    print(f"Загрузка статистики из {filename}")
    
    current_dir = os.getcwd()
    file_path = os.path.join(current_dir, filename)

    if not os.path.exists(file_path):
        print(f"Ошибка: файл {file_path} не найден!")
        return None
    
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        print(f"Успешно загружено:")
        print(f"  Всего записей: {len(data.get('detailed_logs', []))}")
        print(f"  Всего попыток: {data.get('total_attempts', 0)}")
        print(f"  Успешных: {data.get('successful_logins', 0)}")
        print(f"  Неудачных: {data.get('failed_logins', 0)}")
        
        return data
    
    except Exception as e:
        print(f"Ошибка загрузки файла: {e}")
        return None


""" Изменения времени первого фактора по попыткам """
def plot_factor1_time_evolution(data):
    print("\nПостроение графика времени фактора 1")
    
    logs = data.get('detailed_logs', [])
    if not logs:
        print("Нет данных для построения графика")
        return
    
    # Сортировка по порядку
    sorted_logs = sorted(logs, key=lambda x: x.get('attempt_number', 0))
    
    # Подготовка данных
    attempts = []
    times = []
    successes = []
    errors = []
    
    for i, log in enumerate(sorted_logs, 1):
        attempts.append(i)
        times.append(log.get('factor1_time', 0))
        successes.append(1 if log.get('success', False) else 0)
        errors.append(log.get('factor1_errors', 0))
    
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10))
    fig.suptitle('Фактор 1 (динамические задания): время выполнения и ошибки', fontsize=16, fontweight='bold')
    
    # График времени
    ax1.plot(attempts, times, 'b-', alpha=0.7, linewidth=1.5, label='Время выполнения')
    
    # Скользящее среднее
    window = 20
    if len(times) > window:
        rolling_mean = pd.Series(times).rolling(window=window, min_periods=1).mean()
        ax1.plot(attempts, rolling_mean, color='red', linestyle='-', linewidth=2.5, 
                        label=f'Скользящее среднее ({window} попыток)')
    
    # Разделение на успешные/неуспешные
    success_times = [t if s else None for t, s in zip(times, successes)]
    fail_times = [t if not s else None for t, s in zip(times, successes)]
    
    ax1.scatter(attempts, success_times, c='green', alpha=0.6, s=30, label='Успешные', marker='o')
    ax1.scatter(attempts, fail_times, c='red', alpha=0.6, s=50, label='Неудачные', marker='x')
    
    ax1.set_xlabel('Номер попытки', fontsize=12)
    ax1.set_ylabel('Время (секунды)', fontsize=12)
    ax1.set_title('Время выполнения формулы', fontsize=14)
    ax1.legend(loc='best')
    ax1.grid(True, alpha=0.3)
    
    # Горизонтальная линия среднего
    avg_time = data.get('average_time_factor1', 0)
    ax1.axhline(y=avg_time, color='orange', linestyle='--', alpha=0.7, 
                label=f'Среднее: {avg_time:.1f}с')
    
    # График ошибок
    ax2.bar(attempts, errors, color='coral', alpha=0.7, label='Ошибки')
    ax2.set_xlabel('Номер попытки', fontsize=12)
    ax2.set_ylabel('Количество ошибок', fontsize=12)
    ax2.set_title('Ошибки в формуле', fontsize=14)
    ax2.legend(loc='upper right')
    ax2.grid(True, alpha=0.3, axis='y')
    
    # Линия тренда ошибок
    if len(errors) > 5:
        z = np.polyfit(attempts, errors, 1)
        p = np.poly1d(z)
        ax2.plot(attempts, p(attempts), color='red', linestyle='--', 
                        alpha=0.8, linewidth=2, label='Тренд ошибок')
    
    plt.tight_layout()
    plt.savefig('factor1_time_evolution.png', dpi=150, bbox_inches='tight')
    print("График сохранен как factor1_time_evolution.png")


""" Изменения времени второго фактора по попыткам """
def plot_factor2_time_evolution(data):
    print("\nПостроение графика времени Фактора 2")
    
    logs = data.get('detailed_logs', [])
    if not logs:
        print("Нет данных для построения графика")
        return
    
    # Фильтрация попыток, где время второго фактора > 0
    filtered_logs = [log for log in logs if log.get('factor2_time', 0) > 0]
    
    if not filtered_logs:
        print("Нет данных с измеренным временем второго фактора")
        return
    
    sorted_logs = sorted(filtered_logs, key=lambda x: x.get('attempt_number', 0))
    
    attempts = list(range(1, len(sorted_logs) + 1))
    times = [log.get('factor2_time', 0) for log in sorted_logs]
    errors = [log.get('factor2_errors', 0) for log in sorted_logs]
    
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10))
    fig.suptitle('Фактор 2 (Графический): Время выполнения и ошибки', fontsize=16, fontweight='bold')
    
    # График времени
    ax1.plot(attempts, times, 'g-', alpha=0.7, linewidth=1.5, label='Время выполнения')
    
    # Скользящее среднее
    window = min(15, len(times) // 3)
    if len(times) > window:
        rolling_mean = pd.Series(times).rolling(window=window, min_periods=1).mean()
        ax1.plot(attempts, rolling_mean, color='purple', linestyle='-', linewidth=2.5, 
                label=f'Скользящее среднее ({window} попыток)')
    
    ax1.set_xlabel('Номер попытки (только с измеренным временем Ф2)', fontsize=12)
    ax1.set_ylabel('Время (секунды)', fontsize=12)
    ax1.set_title('Время выполнения графического этапа', fontsize=14)
    ax1.legend(loc='best')
    ax1.grid(True, alpha=0.3)
    
    # Среднее время
    avg_time = data.get('average_time_factor2', 0)
    ax1.axhline(y=avg_time, color='orange', linestyle='--', alpha=0.7, 
                label=f'Среднее: {avg_time:.1f}с')
    
    # График ошибок
    ax2.bar(attempts, errors, color='lightcoral', alpha=0.7, label='Ошибки')
    ax2.set_xlabel('Номер попытки', fontsize=12)
    ax2.set_ylabel('Количество ошибок', fontsize=12)
    ax2.set_title('Ошибки в графическом этапе', fontsize=14)
    ax2.legend(loc='upper right')
    ax2.grid(True, alpha=0.3, axis='y')
    
    # Процент попыток с ошибками
    error_percentage = (sum(1 for e in errors if e > 0) / len(errors)) * 100
    ax2.text(0.02, 0.98, f'Попыток с ошибками: {error_percentage:.1f}%', 
             transform=ax2.transAxes, verticalalignment='top',
             bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
    
    plt.tight_layout()
    plt.savefig('factor2_time_evolution.png', dpi=150, bbox_inches='tight')
    print("График сохранен как factor2_time_evolution.png")


""" Сравнительные гистограммы времени обоих факторов """
def plot_comparison_histograms(data):
    print("\nПостроение сравнительных гистограмм")
    
    logs = data.get('detailed_logs', [])
    if not logs:
        print("Нет данных для построения графика")
        return
    
    # Время первого фактора (все попытки)
    times_factor1 = [log.get('factor1_time', 0) for log in logs]
    
    # Время второго фактора (только > 0)
    times_factor2 = [log.get('factor2_time', 0) for log in logs if log.get('factor2_time', 0) > 0]
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
    fig.suptitle('Распределение времени выполнения факторов', fontsize=16, fontweight='bold')
    
    # Гистограмма первого фактора
    ax1.hist(times_factor1, bins=30, color='skyblue', edgecolor='black', alpha=0.7)
    ax1.axvline(np.mean(times_factor1), color='red', linestyle='--', linewidth=2, 
                label=f'Среднее: {np.mean(times_factor1):.1f}с')
    ax1.axvline(np.median(times_factor1), color='green', linestyle=':', linewidth=2,
                label=f'Медиана: {np.median(times_factor1):.1f}с')
    ax1.set_xlabel('Время (секунды)', fontsize=12)
    ax1.set_ylabel('Количество попыток', fontsize=12)
    ax1.set_title('Фактор 1 (Формула)', fontsize=14)
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # Фиксация статистики
    stats_text = f'Всего: {len(times_factor1)}\n'
    stats_text += f'Min: {np.min(times_factor1):.1f}с\n'
    stats_text += f'Max: {np.max(times_factor1):.1f}с\n'
    stats_text += f'Std: {np.std(times_factor1):.1f}с'
    ax1.text(0.02, 0.98, stats_text, transform=ax1.transAxes, verticalalignment='top',
             bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
    
    # Гистограмма второго фактора
    if times_factor2:
        ax2.hist(times_factor2, bins=20, color='lightgreen', edgecolor='black', alpha=0.7)
        ax2.axvline(np.mean(times_factor2), color='red', linestyle='--', linewidth=2,
                    label=f'Среднее: {np.mean(times_factor2):.1f}с')
        ax2.axvline(np.median(times_factor2), color='green', linestyle=':', linewidth=2,
                    label=f'Медиана: {np.median(times_factor2):.1f}с')
        ax2.set_xlabel('Время (секунды)', fontsize=12)
        ax2.set_ylabel('Количество попыток', fontsize=12)
        ax2.set_title('Фактор 2 (Графический)', fontsize=14)
        ax2.legend()
        ax2.grid(True, alpha=0.3)
        
        stats_text = f'Всего: {len(times_factor2)}\n'
        stats_text += f'Min: {np.min(times_factor2):.1f}с\n'
        stats_text += f'Max: {np.max(times_factor2):.1f}с\n'
        stats_text += f'Std: {np.std(times_factor2):.1f}с'
        ax2.text(0.02, 0.98, stats_text, transform=ax2.transAxes, verticalalignment='top',
                 bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
    else:
        ax2.text(0.5, 0.5, 'Нет данных\n(все попытки прерваны\nдо второго фактора)', 
                 ha='center', va='center', transform=ax2.transAxes, fontsize=12)
        ax2.set_title('Фактор 2 (графический)', fontsize=14)
    
    plt.tight_layout()
    plt.savefig('factors_comparison_hist.png', dpi=150, bbox_inches='tight')
    print("График сохранен как factors_comparison_hist.png")


""" Распределение ошибок по факторам """
def plot_error_distribution(data):
    print("\nПостроение графика распределения ошибок")
    
    logs = data.get('detailed_logs', [])
    if not logs:
        print("Нет данных для построения графика")
        return
    
    # Подсчет ошибок
    errors_factor1 = sum(log.get('factor1_errors', 0) for log in logs)
    errors_factor2 = sum(log.get('factor2_errors', 0) for log in logs)
    
    # Попытки с ошибками
    attempts_with_errors_f1 = sum(1 for log in logs if log.get('factor1_errors', 0) > 0)
    attempts_with_errors_f2 = sum(1 for log in logs if log.get('factor2_errors', 0) > 0)
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
    fig.suptitle('Распределение ошибок по факторам аутентификации', fontsize=16, fontweight='bold')
    
    # Круговая диаграмма общего распределения ошибок
    labels = ['Фактор 1\n(динамическое задание)', 'Фактор 2\n(графический)']
    sizes = [errors_factor1, errors_factor2]
    colors = ['#ff9999', '#66b3ff']
    explode = (0.1, 0)
    
    ax1.pie(sizes, explode=explode, labels=labels, colors=colors, autopct='%1.1f%%',
            shadow=True, startangle=90)
    ax1.axis('equal')
    ax1.set_title(f'Всего ошибок: {errors_factor1 + errors_factor2}', fontsize=14)
    
    # Столбчатая диаграмма попыток с ошибками
    categories = ['Фактор 1', 'Фактор 2']
    attempts_data = [attempts_with_errors_f1, attempts_with_errors_f2]
    total_attempts = len(logs)
    percentages = [(a/total_attempts)*100 for a in attempts_data]
    
    bars = ax2.bar(categories, attempts_data, color=['#ff9999', '#66b3ff'], alpha=0.7)
    ax2.set_xlabel('Фактор', fontsize=12)
    ax2.set_ylabel('Количество попыток с ошибками', fontsize=12)
    ax2.set_title('Попытки с хотя бы одной ошибкой', fontsize=14)
    ax2.grid(True, alpha=0.3, axis='y')
    
    # Добавление значений на столбцы
    for bar, percentage in zip(bars, percentages):
        height = bar.get_height()
        ax2.text(bar.get_x() + bar.get_width()/2., height + 0.5,
                f'{height}\n({percentage:.1f}%)', ha='center', va='bottom', fontsize=10)
    
    # Сравнение средней сложности
    avg_errors_per_attempt_f1 = errors_factor1 / total_attempts
    avg_errors_per_attempt_f2 = errors_factor2 / total_attempts
    
    comparison_text = f'Среднее ошибок на попытку:\n'
    comparison_text += f'Фактор 1: {avg_errors_per_attempt_f1:.2f}\n'
    comparison_text += f'Фактор 2: {avg_errors_per_attempt_f2:.2f}\n'
    comparison_text += f'Соотношение: {avg_errors_per_attempt_f1/avg_errors_per_attempt_f2:.1f}:1'
    
    ax2.text(0.02, 0.98, comparison_text, transform=ax2.transAxes, verticalalignment='top',
             bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
    
    plt.tight_layout()
    plt.savefig('error_distribution.png', dpi=150, bbox_inches='tight')
    print("График сохранен как error_distribution.png")


""" Анализ успешности аутентификации """
def plot_success_rate_analysis(data):
    print("\nПостроение графика анализа успешности")
    
    logs = data.get('detailed_logs', [])
    if not logs:
        print("Нет данных для построения графика")
        return
    
    # Группировка по пользователям
    user_stats = {}
    for log in logs:
        email = log.get('email', 'unknown')
        if email not in user_stats:
            user_stats[email] = {'attempts': 0, 'successes': 0, 'times_f1': [], 'times_f2': []}
        
        user_stats[email]['attempts'] += 1
        if log.get('success', False):
            user_stats[email]['successes'] += 1
        
        user_stats[email]['times_f1'].append(log.get('factor1_time', 0))
        if log.get('factor2_time', 0) > 0:
            user_stats[email]['times_f2'].append(log.get('factor2_time', 0))
    
    # Сортировка пользователей по количеству попыток
    sorted_users = sorted(user_stats.items(), key=lambda x: x[1]['attempts'], reverse=True)
    
    # Разрез топ-10 пользователей
    top_users = sorted_users[:10]
    
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 12))
    fig.suptitle('Анализ успешности по пользователям', fontsize=16, fontweight='bold')
    
    # График успешности
    user_names = [email.split('@')[0] for email, _ in top_users]
    attempts_data = [stats['attempts'] for _, stats in top_users]
    success_rates = [(stats['successes']/stats['attempts'])*100 for _, stats in top_users]
    
    x = np.arange(len(user_names))
    width = 0.35
    
    bars1 = ax1.bar(x - width/2, attempts_data, width, label='Всего попыток', color='lightblue')
    ax1.set_xlabel('Пользователь', fontsize=12)
    ax1.set_ylabel('Количество попыток', fontsize=12, color='lightblue')
    ax1.tick_params(axis='y', labelcolor='lightblue')
    ax1.set_xticks(x)
    ax1.set_xticklabels(user_names, rotation=45, ha='right')
    
    ax2_alt = ax1.twinx()
    line = ax2_alt.plot(x, success_rates, 'ro-', linewidth=2, markersize=8, label='Процент успеха')
    ax2_alt.set_ylabel('Процент успеха (%)', fontsize=12, color='red')
    ax2_alt.tick_params(axis='y', labelcolor='red')
    ax2_alt.set_ylim([0, 105])
    
    # Объединяем легенды
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2_alt.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper right')
    
    ax1.set_title('Топ-10 пользователей по количеству попыток', fontsize=14)
    ax1.grid(True, alpha=0.3, axis='y')
    
    # Вывод значений на столбцы
    for i, (bar, rate) in enumerate(zip(bars1, success_rates)):
        ax1.text(bar.get_x() + bar.get_width()/2., bar.get_height() + 0.5,
                f'{int(bar.get_height())}', ha='center', va='bottom', fontsize=9)
        ax2_alt.text(i, rate + 1, f'{rate:.1f}%', ha='center', va='bottom', color='red', fontsize=9)
    
    # График среднего времени
    avg_times_f1 = [np.mean(stats['times_f1']) if stats['times_f1'] else 0 for _, stats in top_users]
    avg_times_f2 = [np.mean(stats['times_f2']) if stats['times_f2'] else 0 for _, stats in top_users]
    
    x = np.arange(len(user_names))
    ax2.bar(x - width/2, avg_times_f1, width, label='Среднее время Ф1', color='skyblue')
    ax2.bar(x + width/2, avg_times_f2, width, label='Среднее время Ф2', color='lightgreen')
    
    ax2.set_xlabel('Пользователь', fontsize=12)
    ax2.set_ylabel('Среднее время (секунды)', fontsize=12)
    ax2.set_xticks(x)
    ax2.set_xticklabels(user_names, rotation=45, ha='right')
    ax2.set_title('Среднее время выполнения по факторам', fontsize=14)
    ax2.legend()
    ax2.grid(True, alpha=0.3, axis='y')
    
    plt.tight_layout()
    plt.savefig('success_rate_analysis.png', dpi=150, bbox_inches='tight')
    print("График сохранен как success_rate_analysis.png")


""" Общая статистика """
def plot_overall_summary(data):
    print("\nПостроение общей статистики")
    
    fig = plt.figure(figsize=(16, 12))
    fig.suptitle('Общая статистика аутентификации', fontsize=18, fontweight='bold')
    
    # Основные метрики
    ax1 = plt.subplot(2, 3, 1)
    metrics = ['Всего попыток', 'Успешных', 'Неудачных']
    values = [
        data.get('total_attempts', 0),
        data.get('successful_logins', 0),
        data.get('failed_logins', 0)
    ]
    
    colors = ['#4CAF50', '#2196F3', '#F44336']
    bars = ax1.bar(metrics, values, color=colors, alpha=0.7)
    ax1.set_ylabel('Количество', fontsize=12)
    ax1.set_title('Основные метрики', fontsize=14)
    ax1.grid(True, alpha=0.3, axis='y')
    
    for bar, value in zip(bars, values):
        ax1.text(bar.get_x() + bar.get_width()/2., bar.get_height() + 0.5,
                f'{value}', ha='center', va='bottom', fontsize=11, fontweight='bold')
    
    # Процент успеха
    success_rate = (data.get('successful_logins', 0) / max(data.get('total_attempts', 1), 1)) * 100
    ax1.text(0.5, 0.95, f'Успешность: {success_rate:.1f}%', 
             transform=ax1.transAxes, ha='center', va='top',
             bbox=dict(boxstyle='round', facecolor='yellow', alpha=0.3),
             fontsize=11)
    
    # Среднее время
    ax2 = plt.subplot(2, 3, 2)
    factors = ['Фактор 1\n(формула)', 'Фактор 2\n(графический)']
    avg_times = [data.get('average_time_factor1', 0), data.get('average_time_factor2', 0)]
    
    bars = ax2.bar(factors, avg_times, color=['#FF9800', '#9C27B0'], alpha=0.7)
    ax2.set_ylabel('Время (секунды)', fontsize=12)
    ax2.set_title('Среднее время выполнения', fontsize=14)
    ax2.grid(True, alpha=0.3, axis='y')
    
    for bar, time in zip(bars, avg_times):
        ax2.text(bar.get_x() + bar.get_width()/2., bar.get_height() + 0.1,
                f'{time:.1f}с', ha='center', va='bottom', fontsize=11, fontweight='bold')
    
    # Ошибки
    ax3 = plt.subplot(2, 3, 3)
    errors = ['Ошибки Ф1', 'Ошибки Ф2']
    error_counts = [data.get('factor1_errors', 0), data.get('factor2_errors', 0)]
    
    bars = ax3.bar(errors, error_counts, color=['#E91E63', '#00BCD4'], alpha=0.7)
    ax3.set_ylabel('Количество ошибок', fontsize=12)
    ax3.set_title('Общее количество ошибок', fontsize=14)
    ax3.grid(True, alpha=0.3, axis='y')
    
    for bar, count in zip(bars, error_counts):
        ax3.text(bar.get_x() + bar.get_width()/2., bar.get_height() + 0.5,
                f'{count}', ha='center', va='bottom', fontsize=11, fontweight='bold')
    
    # Ошибки на попытку
    attempts = max(data.get('total_attempts', 1), 1)
    errors_per_attempt = [error_counts[0]/attempts, error_counts[1]/attempts]
    ax3.text(0.5, 0.95, f'Ошибок на попытку: {errors_per_attempt[0]:.2f}/{errors_per_attempt[1]:.2f}',
             transform=ax3.transAxes, ha='center', va='top',
             bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.3),
             fontsize=10)
    
    # Соотношение успешных/неудачных
    ax4 = plt.subplot(2, 3, 4)
    labels = ['Успешные', 'Неудачные']
    sizes = [data.get('successful_logins', 0), data.get('failed_logins', 0)]
    colors = ['#4CAF50', '#F44336']
    
    wedges, texts, autotexts = ax4.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%',
                                       startangle=90, shadow=True)
    
    for autotext in autotexts:
        autotext.set_color('white')
        autotext.set_fontweight('bold')
    
    ax4.axis('equal')
    ax4.set_title('Соотношение успешных/неудачных', fontsize=14)
    
    # Соотношение времени факторов
    ax5 = plt.subplot(2, 3, 5)
    total_time_f1 = avg_times[0] * attempts
    total_time_f2 = avg_times[1] * attempts
    labels = ['Время на формулы', 'Время на графику']
    sizes = [total_time_f1, total_time_f2]
    colors = ['#FF9800', '#9C27B0']
    
    wedges, texts, autotexts = ax5.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%',
                                       startangle=90, shadow=True)
    
    for autotext in autotexts:
        autotext.set_color('white')
        autotext.set_fontweight('bold')
    
    ax5.axis('equal')
    ax5.set_title('Распределение общего времени', fontsize=14)
    
    # Эффективность системы
    ax6 = plt.subplot(2, 3, 6)
    
    # Метрики эффективности
    efficiency_metrics = [
        'Скорость\n(сек/попытка)',
        'Надежность\n(% успеха)',
        'Точность\n(1 - ошибок)'
    ]
    
    # Скорость = общее время / попытки
    speed = (total_time_f1 + total_time_f2) / attempts
    
    # Надежность = процент успеха
    reliability = success_rate
    
    # Точность = 1 - (общие ошибки / общее время)
    total_errors = sum(error_counts)

    # Нормализация для графика
    accuracy = 100 - (total_errors / attempts * 20)
    
    efficiency_values = [speed, reliability, accuracy]
    
    bars = ax6.bar(efficiency_metrics, efficiency_values, color=['#8BC34A', '#03A9F4', '#FF5722'], alpha=0.7)
    ax6.set_ylabel('Значение', fontsize=12)
    ax6.set_title('Метрики эффективности системы', fontsize=14)
    ax6.grid(True, alpha=0.3, axis='y')
    ax6.set_ylim([0, 110])
    
    for bar, value, metric in zip(bars, efficiency_values, efficiency_metrics):
        if metric == 'Скорость\n(сек/попытка)':
            text = f'{value:.1f}с'
        else:
            text = f'{value:.1f}%'
        
        ax6.text(bar.get_x() + bar.get_width()/2., bar.get_height() + 1,
                text, ha='center', va='bottom', fontsize=10, fontweight='bold')
    
    plt.tight_layout()
    plt.savefig('overall_summary.png', dpi=150, bbox_inches='tight')
    print("График сохранен как overall_summary.png")


""" Консольная статистика """
def generate_report(data):
    print("Итоговые показатели по пользовательскому тестированию")
    
    total_attempts = data.get('total_attempts', 0)
    successful = data.get('successful_logins', 0)
    failed = data.get('failed_logins', 0)
    
    print(f"\nОбщая статистика:")
    print(f"   Всего попыток аутентификации: {total_attempts}")
    print(f"   Успешных входов: {successful} ({successful/total_attempts*100:.1f}%)")
    print(f"   Неудачных попыток: {failed} ({failed/total_attempts*100:.1f}%)")
    
    print(f"\nВремя выполнения:")
    print(f"   Среднее время формульного фактора: {data.get('average_time_factor1', 0):.1f} секунд")
    print(f"   Среднее время графического фактора: {data.get('average_time_factor2', 0):.1f} секунд")
    
    print(f"\nОшибки:")
    print(f"   Число ошибок, допущенных в формульном факторе: {data.get('factor1_errors', 0)}")
    print(f"   Число ошибок, допущенных в графическом факторе: {data.get('factor2_errors', 0)}")
    print(f"   Ошибок на попытку: {data.get('factor1_errors', 0)/total_attempts:.2f} / {data.get('factor2_errors', 0)/total_attempts:.2f}")
    
    # Анализ по пользователям
    logs = data.get('detailed_logs', [])
    if logs:
        user_counts = {}
        for log in logs:
            email = log.get('email', 'unknown')
            user_counts[email] = user_counts.get(email, 0) + 1
        
        print(f"\nАнализ по пользователям:")
        print(f"   Всего уникальных пользователей: {len(user_counts)}")
        
        sorted_users = sorted(user_counts.items(), key=lambda x: x[1], reverse=True)
        if sorted_users:
            print(f"   Самый активный пользователь: {sorted_users[0][0]} ({sorted_users[0][1]} попыток)")
            print(f"   Среднее попыток на пользователя: {total_attempts/len(user_counts):.1f}")
    
    print(f"\nИтог по статистике:")
    
    success_rate = successful/total_attempts*100
    if success_rate > 90:
        print("Высокая надежность системы (>90% успеха)")
    elif success_rate > 80:
        print("Средняя надежность системы (80-90% успеха)")
    else:
        print("Низкая надежность системы (<80% успеха)")
    
    avg_time_total = data.get('average_time_factor1', 0) + data.get('average_time_factor2', 0)
    if avg_time_total < 15:
        print("Хорошая скорость аутентификации (<15 секунд)")
    elif avg_time_total < 25:
        print("Средняя скорость аутентификации (15-25 секунд)")
    else:
        print("Низкая скорость аутентификации (>25 секунд)")


if __name__ == '__main__':
    # Загрузка данных
    data = load_statistics('auth_statistics.json')
    
    # Построение графиков
    plot_factor1_time_evolution(data)
    plot_factor2_time_evolution(data)
    plot_comparison_histograms(data)
    plot_error_distribution(data)
    plot_success_rate_analysis(data)
    plot_overall_summary(data)
    
    # Построение отчета
    generate_report(data)