import json
import psycopg2
from sqlalchemy import create_engine, text, insert, MetaData,\
    Table, Column, Integer, String, ARRAY, update
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from flask_login import UserMixin


class User(UserMixin):
    def __init__(self, id, username, email, password_hash, wardrobe=None, images=None):
        self.id = id
        self.username = username
        self.email = email
        self.password_hash = password_hash
        self.wardrobe = wardrobe or []  # Initialize as an empty list if not provided
        self.images = images or []

    def get_id(self):
        return str(self.id)  # Return the id as a string


class Database:
    def __init__(self, db_url):
        self.engine = create_engine(db_url)
        self.Session = sessionmaker(bind=self.engine)
        self.metadata = MetaData()
        self.person = Table('person', self.metadata, autoload_with=self.engine)  # Load table from database
        self.person = Table('person', self.metadata, autoload_with=self.engine)  # Load person table

    def getUser(self, user_id):
        with self.Session() as session:
            result = session.execute(
                text("SELECT * FROM person WHERE person_id = :user_id"),
                {"user_id": user_id}
            ).fetchone()

            if result:
                # Create a User object from the database result
                user = User(
                    id=result[0],
                    username=result[1],
                    email=result[2],
                    password_hash=result[3],
                    wardrobe=result[4],  # Assume wardrobe is at index 4 after modification
                    images=result[5]  # Assume images is at index 5 after modification
                )
                return user
            else:
                return None

    def add_person(self, name, email, password):
        with self.Session() as session:
            new_person = {"name": name, "email": email, "password": password}
            try:
                metadata = MetaData()
                person = Table('person', metadata, autoload_with=self.engine)
                stmt = insert(person).values(new_person)
                session.execute(stmt)
                session.commit()
                print(f"Пользователь {name} успешно добавлен.")
            except Exception as e:
                # Handle the error
                print(f"Error inserting data: {e}")

    def getUser_email(self, email):
        with self.Session() as session:
            result = session.execute(
                text("SELECT * FROM person WHERE email = :email"),
                {"email": email}
            ).fetchone()

            if result:
                return {
                    'id': result[0],
                    'username': result[1],
                    'email': result[2],
                    'password_hash': result[3],
                    'wardrobe': result[4],
                    'images': result[5]
                }
            else:
                return False

    def getUser_password(self, password):
        with self.Session() as session:
            result = session.execute(
                text("SELECT * FROM person WHERE password = :password"),
                {"password": password}
            ).fetchone()

            if result:
                return {
                    'id': result[0],
                    'username': result[1],
                    'email': result[2],
                    'password_hash': result[3],  # Добавьте поле password_hash
                    'wardrobe': result[4],
                    'images': result[5]
                }
            else:
                return None

    def update_password(self, user_id, new_password_hash):
        with self.Session() as session:
            try:
                stmt = update(self.person).where(self.person.c.person_id == user_id).values(password=new_password_hash)
                session.execute(stmt)
                session.commit()
                print(f"Password updated for user with ID {user_id}")
            except Exception as e:
                print(f"Error updating password: {e}")

    """Получает информацию из таблицы clothes по clothes_id."""
    def get_clothes_by_id(self, clothes_id):
        with self.Session() as session:
            result = session.execute(
                text("SELECT * FROM clothes WHERE clothes_id = :clothes_id"),
                {"clothes_id": clothes_id}
            ).fetchone()
            if result:
                return {
                    'clothes_id': result[0],
                    'type': result[1],
                    'category': result[2],
                    'gender': result[3],
                    'brend': result[4],
                    'season': result[5],
                    'color': result[6],
                    'image': result[7]
                }
            else:
                return None

    """Получает массив clothes_id из гардероба пользователя."""
    def get_wardrobe(self, person_id):
        with self.Session() as session:
            result = session.execute(
                text("SELECT wardrobe FROM person WHERE person_id = :person_id"),
                {"person_id": person_id}
            ).fetchone()

            if result:
                return result[0]  # Возвращаем массив clothes_id
            else:
                return []

# создание БД
def create_bd():
    connection = psycopg2.connect(dbname='images_clothes', user='postgres',
                            password='tedzumi', host='127.0.0.1', port="5432")
    cursor = connection.cursor()
    connection.autocommit = True

    cursor.execute (
        """ CREATE TABLE clothes (
            clothes_id INTEGER PRIMARY KEY,
            type VARCHAR(255),
            category VARCHAR(255),
            gender VARCHAR(6),
            brend VARCHAR(255),
            season VARCHAR(255),
            color VARCHAR(255),
            image VARCHAR(255));
        """
    )
    print("Таблица clothes успешно создана в PostgreSQL")

    cursor.execute (
        """ CREATE TABLE images (
            image_id INTEGER PRIMARY KEY,
            image INTEGER[10]);
        """
    )
    print("Таблица images успешно создана в PostgreSQL")

    cursor.execute (
        """ CREATE TABLE person (
            person_id INTEGER PRIMARY KEY,
            name VARCHAR(255),
            email VARCHAR(255),
            password VARCHAR(255),
            wardrobe INTEGER[1000],
            images INTEGER[1000]);
        """
    )
    print("Таблица person успешно создана в PostgreSQL")
    cursor.close()
    connection.close()


def add_clothes():
    connection = psycopg2.connect(dbname='images_clothes', user="postgres",
                                  password="tedzumi", host='127.0.0.1', port="5432")

    cursor = connection.cursor()
    postgres_insert_query = """ INSERT INTO clothes (clothes_id, type, category, gender, brend, season, color, image) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"""

    with open('clothes_parse/male_clothes.json', 'r', encoding='utf-8') as json_file:
        female_clothes = json.load(json_file)

    ind = 309
    list_1 = ['Обувь', 'Одежда']
    for type in list_1:
        if type == 'Обувь':
            list_2 = ['Ботинки', 'Кроссовки и кеды', 'Мокасины и топсайдеры', 'Сандалии', 'Сапоги', 'Туфли']
        else:
            list_2 = ['Брюки', 'Джемперы, свитеры и кардиганы', 'Джинсы', 'Комбинезоны', 'Пиджаки и костюмы',
                      'Рубашки', 'Спортивные костюмы', 'Футболки и поло', 'Худи и свитшоты', 'Шорты']
        for category in list_2:
            for key in female_clothes[type][category]:
                brend = female_clothes[type][category][key]['Бренд']
                season = female_clothes[type][category][key]['Сезон']
                color = female_clothes[type][category][key]['Цвет']
                image = female_clothes[type][category][key]['Фото']
                print(ind, type, category, brend, season, color, image)

                record_to_insert = (ind, type, category, 'male', brend, season, color, image)
                cursor.execute(postgres_insert_query, record_to_insert)
                ind += 1

    connection.commit()
    count = cursor.rowcount
    print(count, "Запись успешно добавлена в таблицу clothes")

