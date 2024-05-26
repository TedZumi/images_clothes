from flask import Flask, render_template, url_for, \
    request, redirect, g
from api import API
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from UserLogin import UserLogin
from sqlalchemy import create_engine, MetaData, select, insert, Table
from sqlalchemy.sql.expression import exists
import re
import os
from data_base import Database
from werkzeug.security import generate_password_hash, check_password_hash
import mimetypes
import auth
from profile import get_person_wardrobe


app = Flask(__name__, static_folder='static', template_folder='templates')
app.secret_key = os.urandom(24)
app.config['DATABASE'] = "postgresql+psycopg2://postgres:tedzumi@127.0.0.1/images_clothes"
app.config['STATIC_URL_PATH'] = '/static'

# Настройка MIME-типов
mimetypes.add_type('text/javascript', '.js', True)
mimetypes.add_type('text/css', '.css', True)

login_manager = LoginManager(app)
login_manager.login_view = 'login'


@app.before_request
def before_request():
    g.db = Database(app.config['DATABASE'])
    g.db.session = g.db.Session() # Создаем сессию SQLAlchemy


@app.teardown_appcontext
def close_connection(exception):
    db = g.pop('db', None)
    if db is not None:
        db.session.close() # Закрываем сессию SQLAlchemy


@login_manager.user_loader
def load_user(user_id):
    print("Loading user")
    return UserLogin().fromDB(user_id, g.db)


@login_manager.unauthorized_handler
def unauthorized_callback():
    return redirect(url_for('login'))


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    person_id = current_user.get_id()
    logout_url = url_for('logout')

    if request.method == 'POST':
        password = request.form['password']
        new_password = request.form['new_password']
        repeat_new_password = request.form['repeat_new_password']

        print(password, new_password, repeat_new_password)
        result = auth.update_pass(app, person_id, password, new_password, repeat_new_password, g.db)
        if result:
            return render_template('profile.html', error=result, logout_url=logout_url, person_id=person_id)
        else:
            return render_template('profile.html', error="Пароль успешно изменен", logout_url=logout_url,
                                   person_id=person_id)
    return render_template('profile.html', logout_url=logout_url, person_id=person_id)


@app.route('/wardrobe', methods=['GET', 'POST'])
@login_required
def wardrobe():
    person_id = current_user.get_id()
    person_wardrobe = get_person_wardrobe(app, person_id, g.db)
    return render_template('wardrobe.html', person_wardrobe=person_wardrobe)


api = API(app)  # Передаем app в API


if __name__ == '__main__':
    app.run(debug=True)