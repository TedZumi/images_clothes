import re
import json
import random
from typing import Dict, List, Any
from dataclasses import dataclass
from copy import deepcopy


# Хранение информации о преобразовании
@dataclass
class DynamicTask:
    transformation_id: str
    category: str
    description_template: str
    function_name: str
    parameter_schema: Dict[str, Any]
    complexity: int
    applicability_conditions: List[str]
    is_active: bool
    
    def to_dict(self) -> Dict:
        """Конвертация в словарь"""
        return {
            'transformation_id': self.transformation_id,
            'category': self.category,
            'description_template': self.description_template,
            'function_name': self.function_name,
            'parameter_schema': self.parameter_schema,
            'complexity': self.complexity,
            'applicability_conditions': self.applicability_conditions,
            'is_active': self.is_active
        }


class DynamicTasksTool:
    def __init__(self, dbase):
        self.db = dbase
        print(type(self.db))
        self.transformations_cache = None
        self._safe_eval_globals = {
            'max': max,
            'min': min,
            'abs': abs,
            'len': len,
            'int': int,
            'float': float,
            'str': str,
            'bool': bool
        }
    
    # Анализ пароля пользователя  
    def analyze_password(self, password: str) -> Dict:
        return {
            
            'length': len(password),
            
            # Есть ли буквы (латиница или кириллица)
            'has_letters': bool(re.search(r'[a-zA-Zа-яА-Я]', password)),
            
            # Есть ли цифры
            'has_digits': bool(re.search(r'\d', password)),
            
            # Есть ли гласные (латиница и кириллица)
            'has_vowels': bool(re.search(r'[aeiouAEIOUаеёиоуыэюяАЕЁИОУЫЭЮЯ]', password)),
            
            # Есть ли заглавные буквы
            'has_uppercase': bool(re.search(r'[A-ZА-Я]', password)),
            
            # Есть ли строчные буквы
            'has_lowercase': bool(re.search(r'[a-zа-я]', password)),
            
            # Количество цифр в пароле
            'digits_count': len(re.findall(r'\d', password)),
            
            # Количество букв в пароле
            'letters_count': len(re.findall(r'[a-zA-Zа-яА-Я]', password)),
        }
    
    # Загрузка формульных преобразований из БД
    def _load_transformations(self) -> List[Dict]:

        if self.transformations_cache is not None:
            return self.transformations_cache
        
        # Получаем данные через БД
        tasks = self.db.get_dynamic_tasks()
        
        transformations = []
        
        for row in tasks:
            try:
                
                # Запоминаем ID для сообщений об ошибках
                transformation_id = row[0]
                
                # Обработка JSON параметров
                param_schema = row[4]
                if param_schema is None:
                    param_schema = {}
                elif isinstance(param_schema, str):
                    # Если вдруг вернулась строка
                    try:
                        # Парсим JSON в словарь
                        param_schema = json.loads(param_schema)
                    except:
                        param_schema = {}
                
                # Обработка JSON условий
                applicability_conditions = row[6]
                
                if applicability_conditions is None:
                    applicability_conditions = []
                elif isinstance(applicability_conditions, str):
                    # Если вдруг вернулась строка
                    try:
                        applicability_conditions = json.loads(applicability_conditions)
                    except:
                        applicability_conditions = []
                
                transformation = DynamicTask(
                    transformation_id=transformation_id,

                    category=row[1],
                    description_template=row[2],
                    function_name=row[3],
                    parameter_schema=param_schema,
                    complexity=row[5],
                    applicability_conditions=applicability_conditions,
                    is_active=row[7]
                )
                
                # Превращаем в словарь и добавляем в список
                transformations.append(transformation.to_dict())
                
            except Exception as e:
                print(f"Ошибка загрузки преобразования {row[0]}: {e}")
                continue
        
        self.transformations_cache = transformations
        print(f"Загружено {len(transformations)} преобразований")
        return transformations
    
    # Безопасное вычисление выражения
    def _safe_eval(self, expression: str, local_vars: Dict) -> Any:
        
        # Убираем кавычки если они есть
        expression = expression.strip('"\' ')
        
        # Проверка на опасные паттерны
        dangerous_patterns = ['__', 'import', 'eval', 'exec', 'open', 'file', 'globals', 'locals']
        for pattern in dangerous_patterns:
            if pattern in expression:
                raise ValueError(f"Выражение содержит опасный паттерн '{pattern}'")
        
        # Проверка допустимых символов (не буквенные)
        allowed_symbols = set('0123456789+-*/().<>!= \t\n\r')
        
        # Все буквы и буквенные слова
        letters_found = set(c for c in expression if c.isalpha())
        words_found = re.findall(r'[a-zA-Z_][a-zA-Z0-9_]*', expression)
        
        # Если есть буквы - проверяем, что это разрешенные идентификаторы
        if letters_found:
            # Список разрешенных имен:
            # базовые функции из safe_eval_globals
            # переменные из local_vars
            # специальные имена True/False/None
            allowed_names = set(self._safe_eval_globals.keys()) | set(local_vars.keys())
            
            # Проверяем каждое найденное слово
            for word in words_found:
                if word not in allowed_names:
                    raise ValueError(
                        f"Использование '{word}' запрещено. "
                        f"Разрешены только: {sorted(allowed_names)}"
                    )
        
        # Проверка остальных символов (не букв)
        for i, c in enumerate(expression):
            if not c.isalpha() and c not in allowed_symbols:
                # Отображаем ошибку
                context = expression[max(0, i-10):min(len(expression), i+10)]
                pointer = ' ' * (i - max(0, i-10)) + '^'
                raise ValueError(
                    f"Недопустимый символ '{c}' (код: {ord(c)}) в позиции {i}\n"
                    f"Контекст: ...{context}...\n"
                    f"           {pointer}"
                )
        
        # Безопасное вычисление
        try:
            # Создаем безопасное окружение
            safe_globals = {
                "__builtins__": {}
            }
            
            # Локальные переменные: разрешенные функции + переданные переменные
            safe_locals = {
                **self._safe_eval_globals,  
                **local_vars                  
            }
            
            # Вычисляем
            result = eval(expression, safe_globals, safe_locals)
            
            # Проверка типа результата
            if not isinstance(result, (int, float, bool, str)):
                raise ValueError(f"Результат имеет недопустимый тип: {type(result)}")
            
            return result
            
        except NameError as e:
            # Перехватываем ошибки о несуществующих именах
            raise ValueError(f"Использовано неизвестное имя: {e}")
        except SyntaxError as e:
            raise ValueError(f"Синтаксическая ошибка в выражении: {e}")
        except ZeroDivisionError as e:
            raise ValueError(f"Деление на ноль: {e}")
        except Exception as e:
            raise ValueError(f"Ошибка вычисления '{expression}': {type(e).__name__}: {e}")
    
    # Наличие одного условия применимости
    def _check_condition(self, condition: str, analysis: Dict, L: int) -> bool:
        """Проверяет одно условие применимости"""
        condition = condition.strip('"\' ')
        
        # Булевые условия (has_xxx)
        if condition.startswith('has_'):
            return analysis.get(condition, False)
        
        # Числовые сравнения
        operators = ['>=', '<=', '>', '<', '==', '!=', '=']
        for op in operators:
            if op in condition:
                left_part, right_part = condition.split(op, 1)
                left = left_part.strip()
                right = right_part.strip()
                
                # Вычисляем левую часть
                if left in analysis:
                    left_value = analysis[left]
                elif left == 'L':
                    left_value = L
                else:
                    try:
                        left_value = self._safe_eval(left, {'L': L, **analysis})
                    except ValueError:
                        return False  # Не можем вычислить - условие ложно
                
                # Вычисляем правую часть
                try:
                    right_value = self._safe_eval(right, {'L': L})
                except ValueError:
                    # Если не число и не выражение, пробуем как строку
                    right_value = right
                
                # Выполняем сравнение
                if op == '>=' or op == '=>':
                    return left_value >= right_value
                elif op == '<=' or op == '=<':
                    return left_value <= right_value
                elif op == '>':
                    return left_value > right_value
                elif op == '<':
                    return left_value < right_value
                elif op == '==' or op == '=':
                    return left_value == right_value
                elif op == '!=':
                    return left_value != right_value
        
        # Если не распознали формат
        return False
    
    # Обработка динамических параметров в формуле
    def _process_parameters(self, transform: Dict, L: int) -> Dict:
        # Создаем копию преобразования
        transform = deepcopy(transform)  
        param_schema = transform.get('parameter_schema', {})
        
        if isinstance(param_schema, dict):
            for param_name, param_config in param_schema.items():
                if isinstance(param_config, dict):
                    for key, value in param_config.items():
                        if isinstance(value, str):
                            try:
                                # Заменяем выражения с L
                                computed = self._safe_eval(value, {'L': L})
                                transform['parameter_schema'][param_name][key] = computed
                            except ValueError:
                                # Оставляем как есть ("j != i")
                                pass
        
        # Добавляем вычисленные параметры для удобства
        transform['_processed_params'] = {
            'L': L,
            'is_1_based': True  # Флаг, что индексы от 1
        }
        
        return transform
    
    # Получение списка преобразований, применимых к паролю
    def get_applicable_transformations(self, password: str) -> List[Dict]:
        # Анализируем пароль
        analysis = self.analyze_password(password)
        L = analysis['length']
        
        # Загружаем преобразования
        transformations = self._load_transformations()
        
        applicable = []
        
        for transform in transformations:
            if not transform.get('is_active', True):
                continue
            
            # Проверяем все условия
            conditions_met = True
            for condition in transform.get('applicability_conditions', []):
                if not self._check_condition(condition, analysis, L):
                    conditions_met = False
                    break
            
            if conditions_met:
                # Обрабатываем параметры
                processed_transform = self._process_parameters(transform, L)
                applicable.append(processed_transform)
        
        # Сортируем по сложности
        applicable.sort(key=lambda x: x.get('complexity', 0))
        
        return applicable
    
    # Генерация случайных параметров для преобразований
    def generate_random_parameters(self, transform: Dict, password: str) -> Dict:
        L = len(password)
        param_schema = transform.get('parameter_schema', {})
        
        if not param_schema:
            return {}  # Преобразование без параметров
        
        params = {}
        
        # T2
        if transform['transformation_id'] == 'T2':
            min_val = param_schema.get('n', {}).get('min', 1)
            max_val = param_schema.get('n', {}).get('max', L-1)
            if max_val >= min_val:
                params['n'] = random.randint(min_val, max_val)
            else:
                params['n'] = 1
        
        # T3
        elif transform['transformation_id'] == 'T3':
            i_min = param_schema.get('i', {}).get('min', 1)
            i_max = param_schema.get('i', {}).get('max', L)
            j_min = param_schema.get('j', {}).get('min', 1)
            j_max = param_schema.get('j', {}).get('max', L)
            
            i = random.randint(i_min, i_max)
            
            attempts = 0
            max_attempts = 10
            while attempts < max_attempts:
                j = random.randint(j_min, j_max)
                if j != i:
                    params['i'] = i
                    params['j'] = j
                    break
                attempts += 1
            
            if 'i' not in params:
                params['i'] = 1
                params['j'] = L if L > 1 else 2
        
        # T5, T6
        elif transform['transformation_id'] in ['T5', 'T6']:
            min_val = param_schema.get('d', {}).get('min', 1)
            max_val = param_schema.get('d', {}).get('max', 3)
            params['d'] = random.randint(min_val, max_val)
        
        # T11
        elif transform['transformation_id'] == 'T11':
            min_val = param_schema.get('d', {}).get('min', 1)
            max_val = param_schema.get('d', {}).get('max', 9)
            params['d'] = random.randint(min_val, max_val)
        
        # T12
        elif transform['transformation_id'] == 'T12':
            min_val = param_schema.get('x', {}).get('min', 0)
            max_val = param_schema.get('x', {}).get('max', L-1)
            if max_val >= min_val and L > 0:
                params['x'] = random.randint(min_val, max_val)
            else:
                params['x'] = 0
        
        # T13
        elif transform['transformation_id'] == 'T13':
            pass  # Нет параметров
        
        # T14
        elif transform['transformation_id'] == 'T14':
            # x - номер буквы
            x_min = param_schema.get('x', {}).get('min', 1)
            x_max = param_schema.get('x', {}).get('max', L)
            if x_max >= x_min:
                params['x'] = random.randint(x_min, x_max)
            else:
                params['x'] = 1
            
            # n - цифра от 0 до 9
            n_min = param_schema.get('n', {}).get('min', 0)
            n_max = param_schema.get('n', {}).get('max', 9)
            params['n'] = random.randint(n_min, n_max)
        
        # T15
        elif transform['transformation_id'] == 'T15':
            # x - номер цифры
            x_min = param_schema.get('x', {}).get('min', 1)
            x_max = param_schema.get('x', {}).get('max', L)
            if x_max >= x_min:
                params['x'] = random.randint(x_min, x_max)
            else:
                params['x'] = 1
            
            # letter - случайная буква
            import string
            params['letter'] = random.choice(string.ascii_letters)
        
        # T16
        elif transform['transformation_id'] == 'T16':
            pass  # Нет параметров
        
        # T17
        elif transform['transformation_id'] == 'T17':
            min_val = param_schema.get('x', {}).get('min', 1)
            max_val = param_schema.get('x', {}).get('max', L)
            if max_val >= min_val and L > 0:
                params['x'] = random.randint(min_val, max_val)
            else:
                params['x'] = 1
        
        return params
    
    # Получение списка преобразований, применимых к паролю с параметрами
    def get_transformations_with_parameters(self, password: str) -> List[Dict]:
        applicable = self.get_applicable_transformations(password)
        
        for transform in applicable:
            # Генерируем параметры для преобразований, которые их требуют
            if transform.get('parameter_schema'):
                params = self.generate_random_parameters(transform, password)
                transform['generated_parameters'] = params
            else:
                transform['generated_parameters'] = {}
        
        return applicable
    
    # Выбор случайного преобразования, генерация параметров, активация
    def apply_random_transformation(self, password: str) -> Dict[str, Any]:
        applicable = self.get_applicable_transformations(password)
        
        if not applicable:
            return {
                'original': password,
                'transformed': password,
                'transformation_id': None,
                'description': 'Нет применимых преобразований',
                'parameters': {}
            }
        
        # Выбираем случайное преобразование
        transform = random.choice(applicable)
        
        # Генерируем параметры если нужно
        params = {}
        if transform.get('parameter_schema'):
            params = self.generate_random_parameters(transform, password)
        
        # Применяем преобразование
        result = self.apply_transformation(password, transform, params)
        
        return {
            'original': password,
            'transformed': result,
            'transformation_id': transform['transformation_id'],
            'description': transform['description_template'],
            'parameters': params
        }
     
    # Применение преобразований
    def apply_transformation(self, password: str, transform: Dict, params: Dict = None) -> str:
        # Применяет  соответствующее преобразование к паролю с заданными параметрами
        
        if params is None:
            params = {}
        
        # Применяем соответствующую функцию
        func_name = transform.get('function_name', '')
        
        if func_name == 'reverse':
            return self._reverse(password, params)
        elif func_name == 'rotate':
            return self._rotate(password, params)
        elif func_name == 'swap':
            return self._swap(password, params)
        elif func_name == 'swap_first_last':
            return self._swap_first_last(password, params)
        elif func_name == 'increment_digits':
            return self._increment_digits(password, params)
        elif func_name == 'decrement_digits':
            return self._decrement_digits(password, params)
        elif func_name == 'uppercase':
            return self._uppercase(password, params)
        elif func_name == 'lowercase':
            return self._lowercase(password, params)
        elif func_name == 'keyboard_en_ru':
            return self._keyboard_en_ru(password, params)
        elif func_name == 'vowel_next':
            return self._vowel_next(password, params)
        elif func_name == 'delete_char_forward':
            return self._delete_char_forward(password, params)
        elif func_name == 'letter_to_number_forward':
            return self._letter_to_number_forward(password, params)
        elif func_name == 'replace_letter_with_digit_forward':
            return self._replace_letter_with_digit_forward(password, params)
        elif func_name == 'replace_digit_with_letter_forward':
            return self._replace_digit_with_letter_forward(password, params)
        elif func_name == 'sort_chars_forward':
            return self._sort_chars_forward(password, params)
        elif func_name == 'make_xth_letter_case_forward':
            return self._make_xth_letter_case_forward(password, params)
        else:
            raise ValueError(f"Неизвестное преобразование: {func_name}")
    
    
    # Реализации преобразований
    # Обратный порядок
    def _reverse(self, password: str, params: Dict) -> str:
        return password[::-1]
    
    # Циклический сдвиг
    def _rotate(self, password: str, params: Dict) -> str:
        n = params.get('n', 1)
        n = n % len(password)
        return password[-n:] + password[:-n]
    
    # Обмен символов
    def _swap(self, password: str, params: Dict) -> str:

        # Получаем 1-based индексы
        i = params.get('i', 1)
        j = params.get('j', 2)
        
        # Конвертируем 1-based в 0-based 
        i = i - 1
        j = j - 1
        
        # Проверяем валидность индексов
        if i < 0 or i >= len(password) or j < 0 or j >= len(password):
            return password
        
        # Создаем список символов
        chars = list(password)
        
        # Меняем местами
        chars[i], chars[j] = chars[j], chars[i]
        return ''.join(chars)
    
    # Обмен первого и последнего символа
    def _swap_first_last(self, password: str, params: Dict) -> str:
        if len(password) < 2:
            return password
        chars = list(password)
        chars[0], chars[-1] = chars[-1], chars[0]
        return ''.join(chars)
    
    # Увеличение цифр
    def _increment_digits(self, password: str, params: Dict) -> str:
        d = params.get('d', 1) 
        result = []
        for char in password:
            if char.isdigit():
                new_digit = (int(char) + d) % 10
                result.append(str(new_digit))
            else:
                result.append(char)
        return ''.join(result)
    
    # Уменьшение цифр
    def _decrement_digits(self, password: str, params: Dict) -> str:
        d = params.get('d', 1)
        result = []
        for char in password:
            if char.isdigit():
                new_digit = (int(char) - d) % 10
                result.append(str(new_digit))
            else:
                result.append(char)
        return ''.join(result)
    
    # Перевод в верхний регистр
    def _uppercase(self, password: str, params: Dict) -> str:
        return password.upper()
    
    # Перевод в нижний регистр
    def _lowercase(self, password: str, params: Dict) -> str:
        return password.lower()
    
    # Смена клавиатурной раскладки
    def _keyboard_en_ru(self, password: str, params: Dict) -> str:

        # Таблица преобразования английско-русская
        en_to_ru = {
            'q': 'й', 'w': 'ц', 'e': 'у', 'r': 'к', 't': 'е',
            'y': 'н', 'u': 'г', 'i': 'ш', 'o': 'щ', 'p': 'з',
            '[': 'х', ']': 'ъ', 'a': 'ф', 's': 'ы', 'd': 'в',
            'f': 'а', 'g': 'п', 'h': 'р', 'j': 'о', 'k': 'л',
            'l': 'д', ';': 'ж', "'": 'э', 'z': 'я', 'x': 'ч',
            'c': 'с', 'v': 'м', 'b': 'и', 'n': 'т', 'm': 'ь',
            ',': 'б', '.': 'ю', '/': '.',
            'Q': 'Й', 'W': 'Ц', 'E': 'У', 'R': 'К', 'T': 'Е',
            'Y': 'Н', 'U': 'Г', 'I': 'Ш', 'O': 'Щ', 'P': 'З',
            '{': 'Х', '}': 'Ъ', 'A': 'Ф', 'S': 'Ы', 'D': 'В',
            'F': 'А', 'G': 'П', 'H': 'Р', 'J': 'О', 'K': 'Л',
            'L': 'Д', ':': 'Ж', '"': 'Э', 'Z': 'Я', 'X': 'Ч',
            'C': 'С', 'V': 'М', 'B': 'И', 'N': 'Т', 'M': 'Ь',
            '<': 'Б', '>': 'Ю', '?': ','
        }
        
        # Таблица преобразования русско-английская
        ru_to_en = {v: k for k, v in en_to_ru.items()}
        
        result = []
        
        for char in password:
            # Пробуем английско-русскую замену
            if char in en_to_ru:
                result.append(en_to_ru[char])
            # Пробуем русско-английскую замену
            elif char in ru_to_en:
                result.append(ru_to_en[char])
            # Символ не в таблицах (цифры, спецсимволы)
            else:
                result.append(char)
        
        return ''.join(result)
    
    # Замена гласных на следующие по алфавиту
    def _vowel_next(self, password: str, params: Dict) -> str:

        vowels_en = 'aeiouAEIOU'
        vowels_ru = 'аеёиоуыэюяАЕЁИОУЫЭЮЯ'
        
        result = []
        for char in password:
            if char in vowels_en:
                idx = vowels_en.index(char)
                next_idx = (idx + 1) % len(vowels_en)
                result.append(vowels_en[next_idx])
            elif char in vowels_ru:
                idx = vowels_ru.index(char)
                next_idx = (idx + 1) % len(vowels_ru)
                result.append(vowels_ru[next_idx])
            else:
                result.append(char)
        return ''.join(result)
    

    # Новые функции
    # Удаление символа
    def _delete_char_forward(self, password: str, params: Dict) -> str:
        x = params.get('x', 0)
        if 0 <= x < len(password):
            return password[:x] + password[x+1:]
        return password
    
    # Замена букв на их номера в алфавите
    def _letter_to_number_forward(self, password: str, params: Dict) -> str:
        result = []
        for ch in password:
            if ch.isalpha():
                result.append(str(ord(ch.lower()) - ord('a') + 1))
            else:
                result.append(ch)
        return ''.join(result)

    # Замена буквы на цифру
    def _replace_letter_with_digit_forward(self, password: str, params: Dict) -> str:
        x = params.get('x', 1)
        n = params.get('n', 0)
        if not 0 <= n <= 9:
            return password
        letters_found = 0
        result = list(password)
        for i, ch in enumerate(result):
            if ch.isalpha():
                letters_found += 1
                if letters_found == x:
                    result[i] = str(n)
                    break
        return ''.join(result)

    # Замена цифры на букву
    def _replace_digit_with_letter_forward(self, password: str, params: Dict) -> str:
        x = params.get('x', 1)
        letter = params.get('letter', 'A')
        if len(letter) != 1 or not letter.isalpha():
            return password
        digits_found = 0
        result = list(password)
        for i, ch in enumerate(result):
            if ch.isdigit():
                digits_found += 1
                if digits_found == x:
                    result[i] = letter
                    break
        return ''.join(result)

    # Сортировка символов по алфавиту
    def _sort_chars_forward(self, password: str, params: Dict) -> str:
        return ''.join(sorted(password))    

    # Одна буква заглавная остальные строчные
    def _make_xth_letter_case_forward(self, password: str, params: Dict) -> str:
        x = params.get('x', 1)
        letters_found = 0
        result = []
        for ch in password:
            if ch.isalpha():
                letters_found += 1
                if letters_found == x:
                    result.append(ch.upper())
                else:
                    result.append(ch.lower())
            else:
                result.append(ch)
        return ''.join(result)

    # Валидация параметров преобразования
    def validate_parameters(self, transform: Dict, params: Dict) -> List[str]:

        errors = []
        param_schema = transform.get('parameter_schema', {})
        
        for param_name, param_config in param_schema.items():
            if param_name not in params:
                errors.append(f"Отсутствует параметр: {param_name}")
                continue
            
            value = params[param_name]
            min_val = param_config.get('min')
            max_val = param_config.get('max')
            
            # Проверка диапазона
            if min_val is not None and value < min_val:
                errors.append(f"Параметр {param_name} должен быть ≥ {min_val}")
            if max_val is not None and value > max_val:
                errors.append(f"Параметр {param_name} должен быть ≤ {max_val}")
            
            # Проверка ограничений
            constraint = param_config.get('constraint')
            if constraint:
                try:
                    # Заменяем ссылки на другие параметры
                    constraint_expr = constraint
                    for other_param in param_schema.keys():
                        if other_param in params:
                            constraint_expr = constraint_expr.replace(
                                other_param, str(params[other_param])
                            )
                    
                    # Проверяем constraint
                    if not self._safe_eval(constraint_expr, {}):
                        errors.append(f"Нарушено ограничение: {constraint}")
                except Exception as e:
                    errors.append(f"Ошибка проверки ограничения: {e}")
        
        return errors


if __name__ == "__main__":
    engine = DynamicTasksTool(None)
    
    test_password = "_MyTestPassword978354_"
    result = engine.analyze_password(test_password)
    
    print(f"Анализ пароля '{test_password}':")
    for key, value in result.items():
        print(f"параметр: {key}, значение {value}")