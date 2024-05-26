from flask import Flask, request, jsonify
from user import User
from data_base import Database
from auth import login as auth_login, logout as auth_logout, registration as auth_registration
from flask_login import current_user


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