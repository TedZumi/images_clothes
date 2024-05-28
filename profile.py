from data_base import Database
from user import User


def get_person_wardrobe(app, person_id, dbase):
    with app.app_context():
        wardrobe = dbase.get_wardrobe(person_id)
        return wardrobe


def get_clothes_info(app, clothes_id, dbase):
    with app.app_context():
        clothes_info = dbase.get_clothes_by_id(clothes_id)
        return clothes_info


def del_clothes(app, person_id, clothes_id, dbase):
    with app.app_context():
        dbase.delete_clothes_from_person_wardrobe(person_id, clothes_id)


def add_clothes(app, person_id, clothes_id, dbase):
    with app.app_context():
        dbase.add_clothes_to_person_wardrobe(person_id, clothes_id)