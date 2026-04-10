class TwoFactorUser:
    def __init__(self, person_id, name, email, password, images, image_sequence, dbase):
        # Хранит данные пользователя, включая новые поля
        pass
    
    def has_two_factor_enabled(self):
        # Проверяет, есть ли 4 изображения и заполнена последовательность
        # Возвращает True/False
        pass
    
    @staticmethod
    def get_by_email(email, dbase):
        # Получает пользователя из таблицы person
        # Запрашивает: person_id, name, email, password, images, image_sequence
        # Возвращает объект TwoFactorUser или None
        pass