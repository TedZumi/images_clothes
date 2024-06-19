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
from profile import *
from clothes import *
import json


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
    clouthes_all = get_all_clothes(app, g.db)
    categories = get_categories(app, g.db)
    brends = get_brends(app, g.db)
    seasons = get_seasons(app, g.db)
    colors = get_colors(app, g.db)
    return render_template('index.html', clouthes_all=clouthes_all, categories=categories, brends=brends,
                           seasons=seasons, colors=colors)


@app.route('/choice/<int:person_id>/<string:position>', methods=['GET'])
@login_required
def choice_item(person_id, position):
    person_wardrobe = get_person_wardrobe(app, person_id, g.db)
    if position == 'top_1':
        clothes = add_top_1_items_list(app, person_wardrobe, g.db)
        position_name = 'верх 1'
    elif position == 'top_2':
        clothes = add_top_2_items_list(app, person_wardrobe, g.db)
        position_name = 'верх 2'
    elif position == 'through':
        clothes = add_through_items_list(app, person_wardrobe, g.db)
        position_name = 'низ'
    else:
        clothes = add_shoes_items_list(app, person_wardrobe, g.db)
        position_name = 'обувь'

    if not clothes:
        return render_template('choice.html', error="В вашем гардеробе отсутствуют позиции одежды для ",
                               position_name=position_name)
    else:
        return render_template('choice.html', person_id=person_id, clothes=clothes, position=position,
                               position_name=position_name, json=json)


@app.route('/create_image', methods=['GET', 'POST'])
@login_required
def create_image():
    person_id = current_user.get_id()

    return render_template('create_image.html',
                           person_id=person_id)


@app.route('/fashion')
@login_required
def fashion():
    return render_template('fashion.html')


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


@app.route('/wardrobe', methods=['GET'])
@login_required
def wardrobe():
    person_id = current_user.get_id()
    person_wardrobe = get_person_wardrobe(app, person_id, g.db)
    return render_template('wardrobe.html', person_wardrobe=person_wardrobe, person_id=person_id)


@app.route('/images', methods=['GET'])
@login_required
def images():
    person_id = current_user.get_id()
    person_image_ids = get_person_images(app, person_id, g.db)
    return render_template('images.html', person_image_ids=person_image_ids, person_id=person_id)


@app.route('/image', methods=['GET'])
@login_required
def image():
    image_id = request.args.get('image_id')
    image_name = request.args.get('image_name')
    image_data = []
    image = get_image(app, image_id, g.db)
    print(image)
    for image_id in image['clothes_ids']:
        clothes_info = get_clothes_info(app, image_id, g.db)
        if clothes_info:
            image_data.append(clothes_info)

    print(image_data)
    return render_template('image.html', image_name=image_name, image_data=image_data)


@app.route('/product_card/<int:clothes_id>')
@login_required
def product_card(clothes_id):
    person_id = current_user.get_id()
    clothes_data = get_clothes_info(app, clothes_id, g.db)
    return render_template('product_card.html', clothes_data=clothes_data, person_id=person_id)


api = API(app)  # Передаем app в API

if __name__ == '__main__':
    app.run(debug=False)