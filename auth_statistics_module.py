""" Сервис, собирающий статистику по аутентификации в json """
import json
import time
import os


class AuthStatistics:
    def __init__(self, stats_file='auth_statistics.json'):
        self.stats_file = stats_file
        self.user_sessions = {}
        
        if not os.path.exists(self.stats_file):
            self._create_initial_file()
        print(f"[STATS] Инициализирован, файл: {stats_file}")
    
    # Создание первоначального файла (если его нет)
    def _create_initial_file(self):
        data = {
            "total_attempts": 0,
            "successful_logins": 0,
            "failed_logins": 0,
            "average_time_factor1": 0.0,
            "average_time_factor2": 0.0,
            "factor1_errors": 0,
            "factor2_errors": 0,
            "detailed_logs": []
        }
        with open(self.stats_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
    
    # Запись данных в файл json
    def _save_data(self, data):
        try:
            with open(self.stats_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"[STATS] Ошибка сохранения: {e}")
            return False
    
    # Получение данных из файла json
    def _load_data(self):
        try:
            with open(self.stats_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return self._create_initial_file()
    
    # Отслеживание старта сессии
    def start_auth_session(self, email):
        if email not in self.user_sessions:
            self.user_sessions[email] = {
                'factor1_start': time.time(),
                'factor1_errors': 0,
                'factor2_errors': 0
            }
            print(f"[STATS] Сессия начата для {email}")
    
    # Стоп для первого фактора
    def end_factor1(self, email, success):
        if email in self.user_sessions:
            session = self.user_sessions[email]
            session['factor1_time'] = time.time() - session['factor1_start']
            session['factor1_success'] = success
            
            if not success:
                session['factor1_errors'] += 1
            
            print(f"[STATS] Фактор 1: {email} - время {session['factor1_time']:.1f}с")
    
    # Старт второго фактора
    def start_factor2(self, email):
        if email not in self.user_sessions:
            print(f"[STATS] Сессия для {email} не найдена, создаем")
            self.start_auth_session(email)
        
        # Устанавливаем время начала только если еще не установлено
        if 'factor2_start' not in self.user_sessions[email]:
            self.user_sessions[email]['factor2_start'] = time.time()
            print(f"[STATS] Фактор 2 начат для {email}")
        else:
            print(f"[STATS] Фактор 2 уже начат ранее для {email}")
    
    # Стоп для второго фактора
    def end_factor2(self, email, success):
        if email in self.user_sessions:
            session = self.user_sessions[email]
            
            # Рассчитываем время
            if 'factor2_start' in session:
                elapsed = time.time() - session['factor2_start']
                session['factor2_time'] = elapsed
                print(f"[STATS] Фактор 2: {email} - время {elapsed:.1f}с")
            else:
                session['factor2_time'] = 0.0
                print(f"[STATS] Ошибка, второй фактор не найден для {email}")
            
            session['factor2_success'] = success
            
            if not success:
                session['factor2_errors'] += 1
        else:
            print(f"[STATS] Ошибка, сессия для {email} не найдена")
    
    # Сохранение результатов аутентификации
    def save_auth_result(self, email, success):
        print(f"[STATS] Сохранение для {email}, успех={success}")
        
        session = self.user_sessions.get(email, {})
        
        # Создание записи
        log_entry = {
            'email': email,
            'success': success,
            'factor1_time': round(session.get('factor1_time', 0.0), 2),
            'factor2_time': round(session.get('factor2_time', 0.0), 2),
            'factor1_errors': session.get('factor1_errors', 0),
            'factor2_errors': session.get('factor2_errors', 0)
        }
        
        print(f"[STATS] Лог: Ф1={log_entry['factor1_time']}с, Ф2={log_entry['factor2_time']}с")
        
        data = self._load_data()
        # Обновление статистики
        data['total_attempts'] += 1
        if success:
            data['successful_logins'] += 1
        else:
            data['failed_logins'] += 1
        
        data['factor1_errors'] += log_entry['factor1_errors']
        data['factor2_errors'] += log_entry['factor2_errors']
        
        # Расчет среднего времени
        if success and log_entry['factor1_time'] > 0 and log_entry['factor2_time'] > 0:
            successful_count = data['successful_logins']
            if successful_count > 0:
                if successful_count > 1:
                    data['average_time_factor1'] = round(
                        (data['average_time_factor1'] * (successful_count - 1) + log_entry['factor1_time']) / successful_count, 
                        2
                    )
                    data['average_time_factor2'] = round(
                        (data['average_time_factor2'] * (successful_count - 1) + log_entry['factor2_time']) / successful_count, 
                        2
                    )
                else:
                    data['average_time_factor1'] = log_entry['factor1_time']
                    data['average_time_factor2'] = log_entry['factor2_time']
        
        # Добавление записи в лог
        data['detailed_logs'].append(log_entry)

        self._save_data(data)
        
        # Удаление сессии
        if email in self.user_sessions:
            del self.user_sessions[email]
    
    # Отображение сводки в консоли
    def print_summary(self):
        print(f"\n[STATS] Итоговый обзор статистики")
        
        data = self._load_data()
        
        print(f"Всего попыток: {data['total_attempts']}")
        print(f"Успешных: {data['successful_logins']}")
        print(f"Неудачных: {data['failed_logins']}")
        
        if data['total_attempts'] > 0:
            success_rate = (data['successful_logins'] / data['total_attempts']) * 100
            print(f"Процент успеха: {success_rate:.1f}%")
        
        print(f"Среднее время Фактор 1: {data['average_time_factor1']}с")
        print(f"Среднее время Фактор 2: {data['average_time_factor2']}с")
        print(f"Ошибок Фактор 1: {data['factor1_errors']}")
        print(f"Ошибок Фактор 2: {data['factor2_errors']}")
        print(f"Детальных записей: {len(data['detailed_logs'])}")
        print(f"Активных сессий: {len(self.user_sessions)}")


stats_collector = AuthStatistics()