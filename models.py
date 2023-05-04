from db import db

class Transcript(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.String(5000))

class Note:
    def __init__(self, text):
        self.text = text