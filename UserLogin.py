from flask_login import UserMixin

class UserLogin(UserMixin):
    def fromDB(self, user_id, db):
        self.__user = db.getUser(user_id)
        return self

    def create(self, user):
        self.__user = user
        return self

    def is_authenticated(self):
        return True

    def is_active(self):
        return True

    def is_anonymous(self):
        return False

    def get_id(self):
        return str(self.__user.id)
    # def get_id(self):
    #     print(f"self.__user: {self.__user}")  # Вывод объекта User
    #     print(f"Атрибуты self.__user: {dir(self.__user)}")
    #     print(f"self.__user.person_id: {self.__user.person_id}")  # Вывод person_id
    #     return str(self.__user.person_id)