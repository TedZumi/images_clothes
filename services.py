import random
from typing import Optional, Tuple
from sessions import session_manager
from formula_factor import DynamicTasksTool


class AuthService:    
    def __init__(self, dbase):
        self.dbase = dbase
        self.engine = None
        self.use_real_engine = False
        
        try:
            self.engine = DynamicTasksTool(dbase)
            self.use_real_engine = True
        except ImportError:
            print("FormulaFactorEngine не найден")
    
    """Генерация формулы для аутентификации"""
    def generate_formula(self, email: str, password: str) -> Tuple[Optional[str], Optional[str], str, str]:
        print(f"[AUTH] Генерация формулы для {email}")
        
        if not self.use_real_engine:
            return None, None, "", "Система формул временно недоступна"
        
        session_id = session_manager.create_session(email, password)
        
        # Генерация формулы
        try:
            with self.dbase.Session() as session:
                # raw_conn = session.connection().connection  # .connection даёт psycopg2 соединение
                # engine = self.engine(raw_conn)  
                
                transforms = self.engine.get_applicable_transformations(password)
                if not transforms:
                    return None, None, "", "Для вашего пароля нет доступных преобразований"
            
                # Выбираем преобразование
                simple_transforms = [t for t in transforms if t.get('complexity', 0) <= 2]
                transform = random.choice(simple_transforms if simple_transforms else transforms[:3])
                
                # Генерируем параметры
                params = {}
                if transform.get('parameter_schema'):
                    params = self.engine.generate_random_parameters(transform, password)
                
                # Вычисляем ответ
                answer = self.engine.apply_transformation(password, transform, params)
                
                # Форматируем формулу
                formula = transform['description_template']
                for key, value in params.items():
                    formula = formula.replace(f"{{{key}}}", str(value))
                
                # Сохраняем в сессию
                session_manager.update_session(
                    session_id,
                    formula=formula,
                    answer=answer,
                    transform_id=transform.get('transformation_id', 'unknown')
                )
                
                print(f"[AUTH] Сгенерирована формула: {transform.get('transformation_id')}")
                return formula, answer, session_id, ""
            
        except Exception as e:
            print(f"[AUTH ERROR] Ошибка генерации формулы: {e}")
            import traceback
            traceback.print_exc()
            return None, None, "", f"Ошибка системы: {str(e)}"
    
    """Проверка ответа на формулу"""
    def verify_formula(self, session_id: str, user_answer: str) -> Tuple[bool, str, int]:
        return session_manager.verify_answer(session_id, user_answer)