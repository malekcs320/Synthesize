import openai
from dotenv import load_dotenv
import os ,json
import pika
from bson import ObjectId
from utils_recom import distances_from_embeddings, indices_of_nearest_neighbors_from_distances
from pymongo import MongoClient
from pymongo.server_api import ServerApi
import time
from datetime import datetime 

class Synthesizer:
    def __init__(self):
        #load env variables
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
        self.files_collection = db["files"]
        self.syntheses_collection=db["syntheses"]
        self.transcripts_collection=db["transcripts"]

        #openai prompts
        self.api_key = os.getenv("OPENAI_API_KEY")
        openai.api_key = self.api_key
        self.model_engine = "text-davinci-003"
        self.prompt = " based on some notes I have taken in class and the this transcription of my professor lecture, \
        Please arrange the synthesized document with subtitles to help me follow the different parts: \
        the transcription: \n {input_transcript} \
        the notes : \n {input_notes} . \
        please generate it  a full stylized html format  differenciate titles  paragraphs."
        self.quizz_prompt = " based on this synthesis, \
        give me a 3 question quizz with answers \
        please generate it in a full stylized html format and differenciate answers from question. my final goal is to make the answers invesible at first and only show them when the user clicks on a button and make them visible when the user reclicks on it\
        the synthesis: \n {input_document} \n "
        self.tags_prompt = " Extract keywords from this text:\n\n {input_document} \n "
        
        # TODO: Change title to be the name of the file 
        self.title = ""
        self.text = ""
        self.quizz=""
        self.tags=""
        self.embedding=list()
        self.recommendations=list()
        self.receive()
       
        
    def generate_summary(self, transcript, notes):
        # Call the OpenAI API to generate a summary of the input text
        response = openai.Completion.create(
            engine=self.model_engine,
            prompt=self.prompt.format(input_transcript=transcript, input_notes=notes),
            max_tokens=1024,
            n=1,
            stop=None,
            temperature=0,
        )
        return response.choices[0].text.strip()
    

    def generate_quizz(self, document):
        # Call the OpenAI API to generate a summary of the input text
        response = openai.Completion.create(
            engine=self.model_engine,
            prompt=self.quizz_prompt.format(input_document=document),
            max_tokens=1024,
            n=1,
            stop=None,
            temperature=0,
        )
        return response.choices[0].text.strip()
    
    def generate_tags_embeds(self, tags):
        tags_ = tags.replace("\n", " ")
        self.embedding = openai.Embedding.create(input = [tags_], model="text-embedding-ada-002")['data'][0]['embedding']
        return self.embedding
    

    def generate_tags(self, document):
        response = openai.Completion.create(
            model="text-davinci-003",
            prompt=self.tags_prompt.format(input_document=document),
            max_tokens=50,
            top_p=1.0,
            frequency_penalty=0.8,
            presence_penalty=0.0,
            temperature=0.5
        )
        tags = response.choices[0].text.strip()
        self.generate_tags_embeds(tags)
        return tags

    

    def generate_recommendations(self):
        recommendations = []
        # retrieve embeddings with id from db
        try:
            embeddings = self.syntheses_collection.find({}, {"_id": 1, "embedding": 1})
            embeddings = list(embeddings)
        except StopIteration:
            return []

        ids_dic = dict()
        for index in range(len(embeddings)):
            ids_dic[index] = embeddings[index]["_id"]
        # convert embeddings to list of lists
        embeddings = [embedding["embedding"] for embedding in embeddings]

        # compute distances between tags and embeddings and keep only distances < 0.1
        distances = distances_from_embeddings(self.embedding, embeddings)
        distances = [distance for distance in distances if distance < 0.2]
        indices = []

        if len(distances) >= 3:
            indices = indices_of_nearest_neighbors_from_distances(distances)[:3]
            _ids = [ids_dic[index] for index in indices]
            # retrieve synthesis names with indices
            recommendations = self.syntheses_collection.find({"_id": {"$in": _ids}}, {"_id": 1, "title": 1})
            recommendations = list(recommendations)
        return recommendations


    def synthesize(self,file_id):
        
        file = ""
        transcript=""
        notes=""
        try:
            file = self.files_collection.find({"_id":ObjectId(file_id) }).limit(1).next()
            transcript_id = file['transcript_id']
            transcript = self.transcripts_collection.find({"_id":ObjectId(transcript_id) }).limit(1).next()['text']
            notes = file['notes']
        except StopIteration:
            print("Iteration Error")
        if not file:
            return "File not found."
        
        self.title = file['name']

        # Synthesize document using Synthesizer
        self.text = self.generate_summary(transcript, notes)
       
        #generate tags
        self.tags=self.generate_tags(self.text)

        #generate recommendations based on tags
        self.recommendations=self.generate_recommendations()

        # generate quizz
        self.quizz=self.generate_quizz(self.text)

        entity = {'title': self.title,'text':self.text , 'quizz': self.quizz, 'tags': self.tags, 'embedding': self.embedding, 'recommendations': self.recommendations, 'isPublic': False}

        return entity
    
    
    def receive(self):
        q_host = os.getenv('QUEUE_HOST')
        q_name = os.getenv('QUEUE_NAME')

        connection = pika.BlockingConnection(pika.ConnectionParameters(host=q_host))
        channel = connection.channel()
        channel.queue_declare(queue=q_name)

        def callback(ch, method, properties, body):
            jsonbody=json.loads(body)
            file_id=jsonbody["file_id"]
            now = datetime.now()
            print(f" [x] Received {file_id} at {now.strftime('%Y-%m-%d %H:%M:%S')}")

            start = time.time()
            entity = self.synthesize(file_id)
            end = time.time()
            print(f"execution time: {end - start}")
            
            new_synthesis = self.syntheses_collection.insert_one(entity)
            print(f"synthesis {new_synthesis.inserted_id} created")
            file = self.files_collection.find_one_and_update({"_id":ObjectId(file_id) }, {"$set": {"synthesis_id": new_synthesis.inserted_id}})
            
            

        channel.basic_consume(queue=q_name, on_message_callback=callback, auto_ack=True)
        channel.start_consuming()
    
    
if __name__ == "__main__":
    synthesizer=Synthesizer()