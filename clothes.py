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