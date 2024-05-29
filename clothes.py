from data_base import Database


def get_all_clothes(app, dbase):
    with app.app_context():
        clothes = dbase.get_all_clothes()
        return clothes


def get_categories(app, dbase):
    with app.app_context():
        categories = dbase.get_all_categories()
        return categories


def get_brends(app, dbase):
    with app.app_context():
        brends = dbase.get_all_brends()
        return brends


def get_seasons(app, dbase):
    with app.app_context():
        seasons = dbase.get_all_seasons()
        return seasons


def get_colors(app, dbase):
    with app.app_context():
        colors = dbase.get_all_colors()
        return colors


def add_top_1_items_list(app, wardrobe, dbase):
    top_1_categories = ['Блузы и рубашки', 'Джемперы, свитеры и кардиганы', 'Комбинезоны', 'Платья и сарафаны', 'Спортивные костюмы', 'Футболки и поло', 'Рубашки', 'Худи и свитшоты']
    top_1_clothes = []
    with app.app_context():
        for item in wardrobe:
            clothes_data = dbase.get_clothes_by_id(item)  # Получаем данные об одежде
            if clothes_data.get('category') in top_1_categories:  # Проверяем категорию
                top_1_clothes.append(clothes_data)  # Добавляем данные в список
    return top_1_clothes  # Возвращаем список одежды


def add_top_2_items_list(app, wardrobe, dbase):
    top_2_categories = ['Пиджаки и костюмы']
    top_2_clothes = []
    with app.app_context():
        for item in wardrobe:
            clothes_data = dbase.get_clothes_by_id(item)  # Получаем данные об одежде
            if clothes_data.get('category') in top_2_categories:  # Проверяем категорию
                top_2_clothes.append(clothes_data)  # Добавляем данные в список
    return top_2_clothes  # Возвращаем список одежды


def add_through_items_list(app, wardrobe, dbase):
    through_categories = ['Брюки', 'Джинсы', 'Шорты', 'Юбки']
    through_clothes = []
    with app.app_context():
        for item in wardrobe:
            clothes_data = dbase.get_clothes_by_id(item)  # Получаем данные об одежде
            if clothes_data.get('category') in through_categories:  # Проверяем категорию
                through_clothes.append(clothes_data)  # Добавляем данные в список
    return through_clothes  # Возвращаем список одежды


def add_shoes_items_list(app, wardrobe, dbase):
    shoes_categories = ['Балетки', 'Босоножки', 'Ботинки', 'Кроссовки и кеды', 'Мокасины и топсайдеры', 'Сандалии', 'Сапоги', 'Туфли']
    shoes_clothes = []
    with app.app_context():
        for item in wardrobe:
            clothes_data = dbase.get_clothes_by_id(item)  # Получаем данные об одежде
            if clothes_data.get('category') in shoes_categories:  # Проверяем категорию
                shoes_clothes.append(clothes_data)  # Добавляем данные в список
    return shoes_clothes  # Возвращаем список одежды