from flask_login import UserMixin

class User(UserMixin):
    def __init__(self, doc):
        print("This is the doc:", doc)
        self.id = str(doc["_id"])
        self.username = doc["username"]
