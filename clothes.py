from data_base import Database


def get_all_clothes(app, dbase):
    with app.app_context():
        clothes = dbase.get_all_clothes()
        return clothes