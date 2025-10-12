from app import db
from flask_login import UserMixin

class User(UserMixin):
    def __init__(self, doc):
        self.id = str(doc["user_id"])
        self.username = doc["name"]