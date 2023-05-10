from flask import Flask, jsonify, request, render_template
from synthesizer import Synthesizer
from dotenv import load_dotenv
import os
from bson import ObjectId
from pymongo import MongoClient
from pymongo.server_api import ServerApi




app = Flask(__name__)
load_dotenv()


#connect to db and get collections
db_uri = os.getenv("MONGO_HOST")
db_name = os.getenv("DB_NAME")
db_port = os.getenv("MONGO_PORT")
client = MongoClient(host=db_uri, port=int(db_port), server_api=ServerApi('1'))

# Send a ping to confirm a successful connection
try:
    client.admin.command('ping')
    print("Pinged your deployment. You successfully connected to MongoDB!")
except Exception as e:
    print(e)

db = client[db_name]
collection = db["synthesis"]

@app.route('/', methods=['GET', 'POST'])
def index():
    transcripts = collection.find()
    transcript = transcripts[0] # assuming only one transcript in the database
    
    #convert ObjectId to string
    transcript['_id'] = str(transcript['_id'])
    transcript_dict = dict(transcript)

    if request.method == 'POST':
        return jsonify({"document": transcript_dict})
    
    return render_template('index.html')

@app.route("/synthesis", methods=["GET"])
def synthesize():
    _id = request.args.get('_id')    



    # check is string is valid ObjectId
    if not ObjectId.is_valid(_id):
        return jsonify({})
    
    synthesis = collection.find({"_id":ObjectId(_id) }).limit(1)
    try:
        synthesis = synthesis.next()
    except StopIteration:
        return jsonify({})


    synthesis["_id"]=str(synthesis["_id"])
    synthesis = dict(synthesis)
    synthesis["recommendations"]  = [{'_id': str(rec['_id']), 'title': rec.get('title','NO TITLE'), 'tags': rec.get('tags','NO TAGS') } for rec in synthesis["recommendations"]]
    # Return synthesized document
    return synthesis


    
    

if __name__ == "__main__":
    app.run(debug=True)
