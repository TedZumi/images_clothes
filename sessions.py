"""Модуль для управления сессиями аутентификации"""
import uuid
import time
import json
from typing import Optional, Dict, Tuple, Any, List


"""Управляет сессиями аутентификации"""
class SessionManager:
    
    def __init__(self, max_attempts: int = 3, session_timeout: int = 300):
        self.sessions: Dict[str, Dict] = {}
        self.max_attempts = max_attempts
        self.session_timeout = session_timeout
    
    """Создает новую сессию для формульной аутентификации"""
    def create_session(self, email: str, password_hash: str) -> str:
        session_id = str(uuid.uuid4())[:12]
        
        self.sessions[session_id] = {
            'email': email,
            'password': password_hash,
            'attempts_left': self.max_attempts,
            'created_at': time.time(),
            'formula': None,
            'answer': None,
            'transform_id': None,
            'type': 'formula'  # Тип сессии
        }
        
        print(f"[SESSION] Создана сессия {session_id[:8]}... для {email}")
        return session_id
    
    """Создает новую сессию для графической аутентификации"""
    def create_graphic_session(self, email: str, user_data: Dict, challenge_data: Dict) -> str:
        session_id = str(uuid.uuid4())[:12]
        
        self.sessions[session_id] = {
            'email': email,
            'user_data': user_data,  # Данные пользователя
            'challenge_data': challenge_data,  # Данные для challenge
            'attempts_left': self.max_attempts,
            'created_at': time.time(),
            'type': 'graphic',  # Тип сессии
            'user_images': user_data.get('images', [])
        }
        
        print(f"[SESSION] Создана графическая сессия {session_id[:8]}... для {email}")
        return session_id
    
    """Получает сессию по ID"""
    def get_session(self, session_id: str) -> Optional[Dict]:
        if session_id not in self.sessions:
            return None
        
        session = self.sessions[session_id]
        
        # Проверяем таймаут
        if time.time() - session['created_at'] > self.session_timeout:
            self.remove_session(session_id)
            return None
        
        return session
    
    """Обновляет данные сессии"""
    def update_session(self, session_id: str, **kwargs) -> bool:
        session = self.get_session(session_id)
        if not session:
            return False
        
        for key, value in kwargs.items():
            if key in session:
                session[key] = value
        
        return True
    
    """Удаляет сессию"""
    def remove_session(self, session_id: str) -> bool:
        if session_id in self.sessions:
            session_type = self.sessions[session_id].get('type', 'unknown')
            del self.sessions[session_id]
            print(f"[SESSION] Удалена сессия ({session_type}) {session_id[:8]}...")
            return True
        return False
    
    """Проверяет ответ пользователя для формульной аутентификации"""
    def verify_answer(self, session_id: str, user_answer: str) -> Tuple[bool, str, int]:
        session = self.get_session(session_id)
        
        if not session:
            return False, "Сессия не найдена или истекла", 0
        
        if user_answer == session['answer']:
            # Успех
            self.remove_session(session_id)
            return True, "Успешная аутентификация!", session['attempts_left']
        else:
            # Неправильный ответ
            session['attempts_left'] -= 1
            
            if session['attempts_left'] <= 0:
                self.remove_session(session_id)
                return False, "Попытки закончились", 0
            else:
                message = f"Неверный ответ. Осталось попыток: {session['attempts_left']}"
                return False, message, session['attempts_left']
    
    """Проверяет графический ответ пользователя"""
    def verify_graphic_answer(self, session_id: str, user_order: List[int], user_rotations: List[int]) -> Tuple[bool, str, int]:
        session = self.get_session(session_id)
        
        if not session:
            return False, "Сессия не найдена или истекла", 0
        
        if session.get('type') != 'graphic':
            return False, "Неверный тип сессии", 0
        
        # Получаем правильные данные
        challenge_data = session.get('challenge_data', {})
        correct_order = challenge_data.get('correct_order', [1, 2, 3, 4])
        correct_rotations = challenge_data.get('correct_rotations', [0, 0, 0, 0])
        
        # Проверяем ответ
        is_correct = (user_order == correct_order and user_rotations == correct_rotations)
        
        if is_correct:
            # Успех
            user_data = session.get('user_data', {})
            self.remove_session(session_id)
            return True, "Графическая аутентификация пройдена!", session['attempts_left']
        else:
            # Неправильный ответ
            session['attempts_left'] -= 1
            
            if session['attempts_left'] <= 0:
                self.remove_session(session_id)
                return False, "Попытки закончились", 0
            else:
                # Анализируем ошибку
                error_msg = "Неверная последовательность"
                if user_order != correct_order:
                    error_msg = "Неверный порядок изображений"
                elif user_rotations != correct_rotations:
                    error_msg = "Неверные повороты изображений"
                
                message = f"{error_msg}. Осталось попыток: {session['attempts_left']}"
                return False, message, session['attempts_left']
    
    """Получает данные для графического этапа"""
    def get_graphic_challenge_data(self, session_id: str) -> Optional[Dict]:
        session = self.get_session(session_id)
        if not session or session.get('type') != 'graphic':
            return None
        
        return session.get('challenge_data')
    
    """Проверяет, есть ли еще попытки"""
    def can_attempt(self, session_id: str) -> bool:
        session = self.get_session(session_id)
        if not session:
            return False
        
        return session.get('attempts_left', 0) > 0
    
    """Получает количество оставшихся попыток"""
    def get_attempts_left(self, session_id: str) -> int:
        session = self.get_session(session_id)
        if not session:
            return 0
        
        return session.get('attempts_left', 0)
    
    """Удаляет старые сессии"""
    def cleanup_old_sessions(self):
        now = time.time()
        expired = [
            sid for sid, session in self.sessions.items()
            if now - session['created_at'] > self.session_timeout
        ]
        
        for session_id in expired:
            self.remove_session(session_id)
        
        if expired:
            print(f"[SESSION] Удалено {len(expired)} старых сессий")
    
    """Возвращает статистику по сессиям"""
    def get_stats(self) -> Dict:
        self.cleanup_old_sessions()
        
        formula_sessions = [s for s in self.sessions.values() if s.get('type') == 'formula']
        graphic_sessions = [s for s in self.sessions.values() if s.get('type') == 'graphic']
        
        return {
            'total_sessions': len(self.sessions),
            'formula_sessions': len(formula_sessions),
            'graphic_sessions': len(graphic_sessions),
            'max_attempts': self.max_attempts,
            'session_timeout': self.session_timeout,
            'active_formula_sessions': [
                {
                    'id': sid[:8],
                    'email': s['email'],
                    'attempts': s['attempts_left'],
                    'transform': s.get('transform_id', '-'),
                    'age': int(time.time() - s['created_at'])
                }
                for sid, s in self.sessions.items() if s.get('type') == 'formula'
            ],
            'active_graphic_sessions': [
                {
                    'id': sid[:8],
                    'email': s['email'],
                    'attempts': s['attempts_left'],
                    'age': int(time.time() - s['created_at'])
                }
                for sid, s in self.sessions.items() if s.get('type') == 'graphic'
            ]
        }

    """Создает новую сессию для графической аутентификации"""
    def create_graphic_session(self, email: str, user_data: Dict, challenge_data: Dict) -> str:
        session_id = str(uuid.uuid4())[:12]
        
        # Сохраняем правильную последовательность в сессии
        self.sessions[session_id] = {
            'email': email,
            'user_data': user_data,
            'correct_order': challenge_data['correct_order'],
            'correct_rotations': challenge_data['correct_rotations'],
            'user_images': challenge_data['user_images'],
            'display_order': challenge_data['display_order'],
            'attempts_left': self.max_attempts,
            'created_at': time.time(),
            'type': 'graphic'
        }
        
        print(f"[SESSION] Создана графическая сессия {session_id[:8]}... для {email}")
        return session_id


# Глобальный экземпляр менеджера сессий
session_manager = SessionManager()