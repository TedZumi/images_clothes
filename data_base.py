import json
import psycopg2
from dotenv import load_dotenv
import os
from sqlalchemy import create_engine, text, insert, MetaData,\
    Table, Column, Integer, String, ARRAY, update
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from flask_login import UserMixin
from sqlalchemy.exc import IntegrityError


class User(UserMixin):
    def __init__(self, id, username, email, password_hash, wardrobe=None):
        self.id = id
        self.username = username
        self.email = email
        self.password_hash = password_hash
        self.wardrobe = wardrobe or []

    def get_id(self):
        return str(self.id)  # Return the id as a string


class Database:
    def __init__(self, db_url):
        self.engine = create_engine(db_url)
        self.Session = sessionmaker(bind=self.engine)
        self.metadata = MetaData()
        self.person = Table('person', self.metadata, autoload_with=self.engine)  # Load table from database

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
                    wardrobe=result[4]
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
                    'wardrobe': result[4]
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
                    'wardrobe': result[4]
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

    """Получает все поля из таблицы clothes."""
    def get_all_clothes(self):
        with self.Session() as session:
            results = session.execute(text("SELECT * FROM clothes")).fetchall()
            clothes_list = []
            for result in results:
                clothes_list.append({
                    'clothes_id': result[0],
                    'type': result[1],
                    'category': result[2],
                    'gender': result[3],
                    'brend': result[4],
                    'season': result[5],
                    'color': result[6],
                    'image': result[7]
                })
            return clothes_list

    """ Возвращает отфильтрованный список одежды с использованием SQL-запроса. """
    def get_filtered_clothes(self, type=None, category=None, gender=None, brend=None, season=None, color=None, limit=50,
                             offset=0):
        sql_query = """
        SELECT * FROM clothes
        WHERE 
            (:type IS NULL OR type = :type)
            AND (:category IS NULL OR category = :category)
            AND (:gender IS NULL OR gender = :gender)
            AND (:brend IS NULL OR brend = :brend)
            AND (:season IS NULL OR season = :season)
            AND (:color IS NULL OR color = :color)
        LIMIT :limit OFFSET :offset
        """

        with self.Session() as session:
            results = session.execute(
                text(sql_query),
                {
                    'type': type,
                    'category': category,
                    'gender': gender,
                    'brend': brend,
                    'season': season,
                    'color': color,
                    'limit': limit,
                    'offset': offset
                }
            ).fetchall()

        # Преобразуем результаты в список словарей для JSON
        filtered_clothes = [
            {
                'clothes_id': result[0],
                'type': result[1],
                'category': result[2],
                'gender': result[3],
                'brend': result[4],
                'season': result[5],
                'color': result[6],
                'image': result[7]
            } for result in results
        ]
        print(f"Отфильтрованный список: {filtered_clothes}")  # Вывод отфильтрованного списка

        return filtered_clothes

    """Возвращает список одежды с ограничением по количеству и смещением."""
    def get_all_clothes_limit(self, offset, limit):
        with self.Session() as session:
            if limit is None:
                # Выполните запрос без LIMIT, чтобы получить все товары
                results = session.execute(
                    text("SELECT * FROM clothes OFFSET :offset"),
                    {"offset": offset}
                ).fetchall()
            else:
                # Выполните запрос с LIMIT
                results = session.execute(
                    text("SELECT * FROM clothes LIMIT :limit OFFSET :offset"),
                    {"limit": limit, "offset": offset}
                ).fetchall()

            clothes_list = []
            for result in results:
                clothes_list.append({
                    'clothes_id': result[0],
                    'type': result[1],
                    'category': result[2],
                    'gender': result[3],
                    'brend': result[4],
                    'season': result[5],
                    'color': result[6],
                    'image': result[7]
                })
            return clothes_list

    """Возвращает список всех уникальных категорий одежды."""
    def get_all_categories(self):
        with self.Session() as session:
            results = session.execute(
                text("SELECT DISTINCT category FROM clothes")
            ).fetchall()
            categories = [result[0] for result in results]
            return categories

    """Возвращает список всех уникальных брендов одежды."""
    def get_all_brends(self):
        with self.Session() as session:
            results = session.execute(
                text("SELECT DISTINCT brend FROM clothes")
            ).fetchall()
            brends = [result[0] for result in results]
            return brends

    """Возвращает список всех уникальных сезонов одежды."""
    def get_all_seasons(self):
        with self.Session() as session:
            results = session.execute(
                text("SELECT DISTINCT season FROM clothes")
            ).fetchall()
            season = [result[0] for result in results]
            return season

    """Возвращает список всех уникальных сезонов одежды."""
    def get_all_colors(self):
        with self.Session() as session:
            results = session.execute(
                text("SELECT DISTINCT color FROM clothes")
            ).fetchall()
            color = [result[0] for result in results]
            return color

    """Удаляет запись из таблицы clothes по clothes_id."""
    def delete_clothes_by_id(self, clothes_id):
        with self.Session() as session:
            try:
                # Используем delete() для удаления записи
                session.execute(
                    text("DELETE FROM clothes WHERE clothes_id = :clothes_id"),
                    {"clothes_id": clothes_id}
                )
                session.commit()
                return True  # Удаление успешно
            except Exception as e:
                print(f"Ошибка при удалении вещи: {e}")
                return False  # Возникла ошибка

    """Удаляет запись из таблицы person, удаляя clothes_id из массива wardrobe."""
    def delete_clothes_from_person_wardrobe(self, person_id, clothes_id):
        with self.Session() as session:
            try:
                # Используем update() для обновления записи
                session.execute(
                    text(
                        "UPDATE person SET wardrobe = array_remove(wardrobe, :clothes_id) WHERE person_id = :person_id"),
                    {"clothes_id": clothes_id, "person_id": person_id}
                )
                session.commit()
                return True  # Удаление успешно
            except Exception as e:
                print(f"Ошибка при удалении вещи из гардероба: {e}")
                return False  # Возникла ошибка

    """Добавляет clothes_id в массив wardrobe записи person."""
    def add_clothes_to_person_wardrobe(self, person_id, clothes_id):
        with self.Session() as session:
            try:
                # Проверяем, есть ли уже эта вещь в гардеробе
                result = session.execute(
                    text("SELECT 1 FROM person WHERE person_id = :person_id AND :clothes_id = ANY(wardrobe)"),
                    {"person_id": person_id, "clothes_id": clothes_id}
                )

                # Если вещь уже есть, ничего не делаем
                if result.fetchone() is not None:
                    return True  # Добавление не требуется, т.к. вещь уже в гардеробе

                # Если вещи нет, добавляем ее в гардероб
                session.execute(
                    text("UPDATE person SET wardrobe = COALESCE(wardrobe, ARRAY[]::INTEGER[]) || :clothes_id WHERE person_id = :person_id"),
                    {"clothes_id": clothes_id, "person_id": person_id}
                )
                session.commit()
                return True  # Добавление успешно
            except Exception as e:
                print(f"Ошибка при добавлении вещи в гардероб: {e}")
                return False

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

    """Добавляет образ в таблицу images и связывает его с элементами одежды в clothes_items."""
    def add_outfit_to_image(self, clothes_ids, image_name, person_id):
        with self.Session() as session:
            try:
                # Вставляем образ в таблицу images
                result = session.execute(
                    text("INSERT INTO images (image_name) VALUES (:image_name) RETURNING image_id"),
                    {"image_name": image_name}
                )
                image_id = result.fetchone()[0]

                # Вставляем элементы одежды в таблицу clothes_items
                for clothes_id in clothes_ids:
                    session.execute(
                        text("INSERT INTO clothes_items (image_id, clothes_id) VALUES (:image_id, :clothes_id)"),
                        {"image_id": image_id, "clothes_id": clothes_id}
                    )

                # Связываем образ с пользователем
                session.execute(
                    text("INSERT INTO person_images (image_id, person_id) VALUES (:image_id, :person_id)"),
                    {"image_id": image_id, "person_id": person_id}
                )

                session.commit()
                return image_id
            except IntegrityError as e:
                print(f"Ошибка добавления образа в таблицу images: {e}")
                return None
            except Exception as e:
                print(f"Ошибка добавления образа в таблицу images: {e}")
                return None

    """Добавляет image_id к массиву images в таблице person по person_id."""
    def add_image_to_person(self, person_id, image_id):
        with self.Session() as session:
            try:
                # Получаем текущий массив images для person_id
                result = session.execute(
                    text("SELECT images FROM person WHERE person_id = :person_id"),
                    {"person_id": person_id}
                )
                current_images = result.fetchone()[0]

                # Если массив images пустой, создаем новый
                if current_images is None:
                    current_images = []

                # Добавляем image_id в массив
                current_images.append(image_id)

                # Обновляем строку в таблице person
                session.execute(
                    text("UPDATE person SET images = :images WHERE person_id = :person_id"),
                    {"images": current_images, "person_id": person_id}
                )

                session.commit()
                return True
            except IntegrityError as e:
                print(f"Ошибка добавления изображения к person: {e}")
                return False
            except Exception as e:
                print(f"Ошибка добавления изображения к person: {e}")
                return False

    """Удаляет образ по image_id из таблицы images и связанные записи из clothes_items."""
    def delete_image(self, image_id):
        with self.Session() as session:
            try:
                # Удаляем записи из clothes_items, связанные с image_id
                session.execute(
                    text("DELETE FROM clothes_items WHERE image_id = :image_id"),
                    {"image_id": image_id}
                )

                # Удаляем запись из person_images, связанную с image_id
                session.execute(
                    text("DELETE FROM person_images WHERE image_id = :image_id"),
                    {"image_id": image_id}
                )

                # Удаляем запись из images
                session.execute(
                    text("DELETE FROM images WHERE image_id = :image_id"),
                    {"image_id": image_id}
                )

                session.commit()
                return True
            except Exception as e:
                print(f"Ошибка при удалении образа: {e}")
                return False

    """Возвращает данные образа по его image_id, включая связанные элементы одежды."""
    def get_image_by_id(self, image_id):
        with self.Session() as session:
            try:
                # Выполняем запрос для получения данных образа и связанных элементов одежды
                result = session.execute(
                    text("""
                        SELECT 
                            i.image_name,
                            array_agg(ci.clothes_id) AS clothes_ids
                        FROM 
                            images i
                        LEFT JOIN 
                            clothes_items ci ON i.image_id = ci.image_id
                        WHERE 
                            i.image_id = :image_id
                        GROUP BY 
                            i.image_id, i.image_name
                    """),
                    {"image_id": image_id}
                )
                image_data = result.fetchone()

                # Если образ найден, возвращаем данные
                if image_data:
                    image_name = image_data[0]
                    clothes_ids = image_data[1]
                    return {"image_name": image_name, "clothes_ids": clothes_ids}
                else:
                    return None  # Образ не найден
            except Exception as e:
                print(f"Ошибка получения образа: {e}")
                return None

    """Возвращает массив images для заданного person_id."""
    def get_images_by_person_id(self, person_id):
        with self.Session() as session:
            try:
                # Выполняем запрос для получения массива image_id
                result = session.execute(
                    text("SELECT i.image_id FROM person_images pi JOIN images i ON pi.image_id = i.image_id WHERE pi.person_id = :person_id"),
                    {"person_id": person_id}
                )
                image_ids = [row[0] for row in result]  # Получаем список image_id

                # Возвращаем список image_id
                return image_ids

            except Exception as e:
                print(f"Ошибка получения массива images: {e}")
                return None


# Загружаем переменные из .env
load_dotenv()

# Получаем значения переменных из .env
db_name = os.getenv("DBNAME")
db_user = os.getenv("USER")
db_password = os.getenv("PASSWORD")


def add_clothes():
    connection = psycopg2.connect(dbname=db_name, user=db_user,
                                  password=db_password, host='127.0.0.1', port="5432")

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


# создание БД
def create_bd():
    connection = psycopg2.connect(dbname=db_name, user=db_user,
                                  password=db_password, host='127.0.0.1', port="5432")
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




