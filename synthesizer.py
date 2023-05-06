import openai
from dotenv import load_dotenv
import os ,json
from db import Database
import pika
from bson import ObjectId

class Synthesizer:
    def __init__(self):
        load_dotenv()
        db_uri = os.getenv("DB_URI")
        db = Database(db_uri, 'myDataBase').db
        self.transcript_collection = db["transcripts"]
        self.notes_collection=db["notes"]
        self.synthesis_collection=db["synthesis"]
        self.api_key = os.getenv("OPENAI_API_KEY")
        openai.api_key = self.api_key
        self.model_engine = "text-davinci-003"
        # GPT-3 prompt
        self.prompt = " based on some notes I have taken in class and the this transcription of my professor lecture, \
        generate a synthesized document for me to help me study. \
        Please arrange the synthesized document with subtitles to help me follow the different parts: \
        the transcription: \n {input_transcript}\
        the notes : \n {input_notes} \n "
        self.receive()
       
        
    def generate_summary(self, transcript, notes):
        # Call the OpenAI API to generate a summary of the input text
        response = openai.Completion.create(
            engine=self.model_engine,
            prompt=self.prompt.format(input_transcript=transcript, input_notes=notes),
            max_tokens=1024,
            n=1,
            stop=None,
            temperature=0.5,
        )
        return response.choices[0].text.strip()
    def receive(self):
        connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))
        channel = connection.channel()
        channel.queue_declare(queue='synthesize')
        def callback(ch, method, properties, body):
            jsonbody=json.loads(body)
            transcript_id=jsonbody["transcript_id"]
            notes_id=jsonbody["notes_id"]
            result=self.synthesize(transcript_id,notes_id)
            self.synthesis_collection.insert_one({'name': 'first synthesis','text':result , 'transcript_id':transcript_id , 'notes_id':notes_id})

        channel.basic_consume(queue='synthesize', on_message_callback=callback, auto_ack=True)

        print(' [*] Waiting for messages. To exit press CTRL+C')
        channel.start_consuming()
    def synthesize(self,transcript_id,notes_id):
        
        # Retrieve transcript from db with transcript_id
        # transcript_id=ObjectId(transcript_id)

        transcript=""
        notes=""
        try:
            transcript = self.transcript_collection.find({"_id":ObjectId(transcript_id) }).limit(1).next()  
            notes = self.notes_collection.find({"_id":ObjectId(notes_id) }).limit(1).next()  
        except StopIteration:
            print("Iteration Error")

        print(transcript)
        print(notes)
        if not transcript:
            return "Transcript not found."
        if not notes:
            return "Notes not found."
        
        #convert ObjectId to string
        transcript['_id'] = str(transcript['_id'])
        transcript_dict = dict(transcript)
        notes['_id'] = str(notes['_id'])
        notes_dict = dict(notes)
        # Synthesize document using Synthesizer
        document = self.generate_summary(transcript_dict['text'], notes_dict['text'])

        # Return synthesized document
        return document
if __name__ == "__main__":
    synthesizer=Synthesizer()