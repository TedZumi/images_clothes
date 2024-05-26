from data_base import Database
from user import User


def get_person_wardrobe(app, person_id, dbase):
    with app.app_context():
        wardrobe = dbase.get_wardrobe(person_id)
        return wardrobe