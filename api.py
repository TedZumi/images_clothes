from flask import Flask, request, jsonify, redirect, url_for
from user import User
from data_base import Database
from auth import login as auth_login, logout as auth_logout, registration as auth_registration
from flask_login import current_user
from profile import get_clothes_info, del_clothes, add_clothes, get_image
from clothes import add_new_image, update_person_images


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

        @self.app.route('/api/v1/wardrobe/<string:wardrobe_ids>')
        def get_wardrobe(wardrobe_ids):
            wardrobe_ids_list = wardrobe_ids.split(',')
            clothes_data = []
            for clothes_id in wardrobe_ids_list:
                clothes_info = self.dbase.get_clothes_by_id(clothes_id)
                if clothes_info:
                    clothes_data.append(clothes_info)

            # Получение параметров фильтрации из запроса
            search_filter = request.args.get('search')

            # Фильтрация данных
            filtered_clothes_data = []
            for clothes_item in clothes_data:
                if (
                        (not search_filter or search_filter.lower() in clothes_item['type'].lower()) or
                        (not search_filter or search_filter.lower() in clothes_item['category'].lower()) or
                        (not search_filter or search_filter.lower() in clothes_item['brend'].lower()) or
                        (not search_filter or search_filter.lower() in clothes_item['season'].lower())
                ):
                    filtered_clothes_data.append(clothes_item)

            return jsonify(filtered_clothes_data)

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
            limit = int(request.args.get('limit', 50))

            # Вызов метода из класса Database
            filtered_clothes = self.dbase.get_filtered_clothes(
                type=type,
                category=category,
                gender=gender,
                brend=brend,
                season=season,
                color=color,
                limit=limit,
                offset=offset
            )

            return jsonify({'clothes': filtered_clothes})

        @self.app.route('/api/v1/image/add/<string:image_ids>/<string:image_name>', methods=['POST'])
        def add_image(image_ids, image_name):
            person_id = current_user.get_id()
            image_ids_list = image_ids.split(',')
            print(image_ids_list)
            image_id = add_new_image(self.app, image_ids_list, image_name, self.dbase)
            if image_id is not None:
                update_person_images(self.app, person_id, image_id, self.dbase)
                return jsonify({'message': 'Вещь образ успешно добавлен'}), 200
            else:
                return jsonify({'error': 'Образ не был добален'}), 401

        @self.app.route('/api/v1/image/<int:image_id>', methods=['GET'])
        def get_person_image_data(image_id):
            image_data = get_image(self.app, image_id, self.dbase)
            clothes_data = []
            clothes_ids = image_data['clothes_ids']
            for clothes_id in clothes_ids:
                clothes_info = self.dbase.get_clothes_by_id(clothes_id)
                if clothes_info:
                    clothes_data.append(clothes_info)

            image_data['clothes_data'] = clothes_data
            image_data.pop('clothes_ids', None)

            return jsonify(image_data)

        @self.app.route('/api/v1/image/delete/<int:image_id>', methods=['DELETE'])
        def delete_image_item(image_id):
            data = request.get_json()  # Получаем данные из тела запроса
            person_id = data.get('person_id')
            print(person_id)
            if person_id:
                self.dbase.remove_image_from_person(person_id, image_id)
                self.dbase.delete_image(image_id)
                return jsonify({'message': 'Образ успешно удален'}), 200
            else:
                return jsonify({'error': 'Образ не был удален'}), 400
