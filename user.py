from flask import Flask, request, jsonify


class User:
    def __init__(self, id, username, email, password_hash, wardrobe, images, dbase):
        self.id = id
        self.username = username
        self.email = email
        self.password_hash = password_hash
        self.wardrobe = wardrobe
        self.images = images
        self.dbase = dbase

    @staticmethod
    def get(user_id, dbase):
        user_data = dbase.getUser(user_id)
        if user_data:
            return User(user_data.id, user_data.username, user_data.email, user_data.password_hash, user_data.wardrobe, user_data.images, dbase)
        else:
            return None

    @staticmethod
    def get_by_email(email, dbase):
        user_data = dbase.getUser_email(email)
        if user_data:
            return User(user_data['id'], user_data['username'], user_data['email'], user_data['password_hash'], user_data['wardrobe'], user_data['images'], dbase)
        else:
            return None

    @staticmethod
    def get_by_password(password, dbase):
        user_data = dbase.getUser_password(password)
        if user_data:
            return User(user_data['id'], user_data['username'], user_data['email'], user_data['password_hash'], dbase)
        else:
            return None

    @staticmethod
    def get_all(dbase):
        users = []
        for user_data in dbase.getAllUsers():
            users.append(User(user_data['id'], user_data['username'], user_data['email'], user_data['password_hash'], dbase))
        return users

    def to_json(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'password_hash': self.password_hash,
            'wardrobe': self.wardrobe,
            'images': self.images
        }

    @staticmethod
    def create(name, email, password_hash, dbase):
        dbase.add_person(name, email, password_hash)
        return User.get_by_email(email, dbase)

    @staticmethod
    def add_new_password(user_id, new_password_hash, dbase):
        dbase.update_password(user_id, new_password_hash)
        # return User.get_by_email(email, dbase)