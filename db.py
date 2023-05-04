from pymongo import MongoClient
from pymongo.server_api import ServerApi

class Database:
    def __init__(self, uri, db_name):
        self.client = MongoClient(uri, server_api=ServerApi('1'))
        self.db = self.client[db_name]

    def insert_transcript(self, transcript):
        self.db.transcripts.insert_one(transcript)

    def get_transcript_by_id(self, transcript_id):
        return self.db.transcripts.find_one({'_id': transcript_id})