from flask import Flask, request, jsonify, redirect, url_for
from user import User
from data_base import Database
from auth import login as auth_login, logout as auth_logout, registration as auth_registration
from flask_login import current_user
from profile import get_clothes_info, del_clothes, add_clothes


# Модель одежды (при необходимости)
class Clothes:
    def __init__(self, clothes_id, type, category, gender, brend, season, color, image):
        self.clothes_id = clothes_id
        self.type = type
        self.category = category
        self.gender = gender
        self.brend = brend
        self.season = season
        self.color = color
        self.image = image


# Фильтр одежды
# class ClothesFilter(FilterSet):
#     type = Filter(field='type', method='eq')
#     category = Filter(field='category', method='eq')
#     gender = Filter(field='gender', method='eq')
#     brend = Filter(field='brend', method='eq')
#     season = Filter(field='season', method='eq')


class API:
    def __init__(self, app):
        self.app = app
        self.dbase = Database(app.config['DATABASE'])  # Создайте экземпляр Database

        # Маршруты API
        @self.app.route('/api/v1/users', methods=['GET'])
        def get_users():
            with app.app_context():
                users = [user.to_json() for user in User.get_all(self.dbase)]
                return jsonify({'users': users})

        @self.app.route('/api/v1/users/<int:user_id>', methods=['GET'])
        def get_user(user_id):
            with app.app_context():
                user = User.get(user_id, self.dbase)
                if user:
                    return jsonify(user.to_json())
                else:
                    return jsonify({'error': 'User not found'}), 404

        # Маршрут для получения пользователя по email
        @self.app.route('/api/v1/users/email/<string:email>', methods=['GET'])
        def get_user_by_email(email):
            with app.app_context():
                user = User.get_by_email(email, self.dbase)
                if user:
                    return jsonify(user.to_json())
                else:
                    return jsonify({'error': 'User not found'}), 404

        # Маршрут для добавления нового пользователя
        @self.app.route('/api/v1/users', methods=['POST'])
        def add_user():
            name = request.json.get('name')
            email = request.json.get('email')
            password = request.json.get('password')
            if not all([name, email, password]):
                return jsonify({'error': 'Missing fields'}), 400
            with app.app_context():
                user = User.create(name, email, password, self.dbase)
                return jsonify({'message': 'User created successfully', 'user': user.to_json()})

        # Маршруты для входа, выхода и регистрации
        @self.app.route('/login', methods=['POST', 'GET'])
        def login():
            return auth_login(app, self.dbase)

        @self.app.route('/logout', methods=['POST'])
        def logout():
            return auth_logout()

        @self.app.route('/registration', methods=['POST', 'GET'])
        def register():
            return auth_registration(app, self.dbase)

        # Маршрут для проверки авторизации
        @self.app.route('/api/v1/auth')
        def auth():
            if current_user.is_authenticated:
                return jsonify({'authenticated': True})
            else:
                return jsonify({'authenticated': False})

        # Маршрут для получения информации о гардеробе
        @self.app.route('/api/v1/wardrobe/<string:wardrobe_ids>')
        def get_wardrobe(wardrobe_ids):
            wardrobe_ids_list = wardrobe_ids.split(',')
            clothes_data = []
            for clothes_id in wardrobe_ids_list:
                clothes_info = self.dbase.get_clothes_by_id(clothes_id)
                if clothes_info:
                    clothes_data.append(clothes_info)
            return jsonify(clothes_data)

        @self.app.route('/api/v1/wardrobe/delete/<int:clothes_id>', methods=['DELETE'])
        def delete_clothes_item(clothes_id):
            person_id = request.args.get('person_id')
            if person_id:
                del_clothes(self.app, person_id, clothes_id, self.dbase)
                return jsonify({'message': 'Вещь успешно удалена из гардероба'}), 200
            else:
                return jsonify({'error': 'Не указан person_id'}), 400

        @self.app.route('/api/v1/wardrobe/add/<int:clothes_id>', methods=['POST'])
        def add_clothes_item(clothes_id):
            person_id = current_user.get_id()  # Получаем ID пользователя из сессии
            if person_id:
                add_clothes(self.app, person_id, clothes_id, self.dbase)  # Вызываем функцию добавления
                return jsonify({'message': 'Вещь успешно добавлена в гардероб'}), 200
            else:
                return jsonify({'error': 'Не авторизован'}), 401

        @self.app.route('/api/v1/clothes/filter', methods=['GET'])
        def filter_clothes():
            # Получение параметров фильтрации
            type = request.args.get('type')
            category = request.args.get('category')
            gender = request.args.get('gender')
            brend = request.args.get('brend')
            season = request.args.get('season')
            color = request.args.get('color')

            # Получаем offset
            offset = int(request.args.get('offset', 0))

            # Получаем limit
            limit = int(request.args.get('limit', 50))  # Обрабатываем limit

            # Получаем ВСЕ товары из базы данных
            clothes_all = self.dbase.get_all_clothes()  # Изменить метод на получение всех товаров

            # Фильтруем данные на стороне сервера
            filtered_clothes = []
            for clothes in clothes_all:
                if (
                        (not type or clothes['type'] == type) and
                        (not category or clothes['category'] == category) and
                        (not gender or clothes['gender'] == gender) and
                        (not brend or clothes['brend'] == brend) and
                        (not season or clothes['season'] == season) and
                        (not color or clothes['color'] == color)
                ):
                    filtered_clothes.append(clothes)

            # Ограничиваем количество товаров на стороне сервера
            filtered_clothes = filtered_clothes[offset:offset + limit]

            return jsonify({'clothes': filtered_clothes})
