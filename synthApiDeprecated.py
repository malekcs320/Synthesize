from flask import Flask, jsonify, request, render_template
from synthesizer import Synthesizer
from dotenv import load_dotenv
import os
from bson import ObjectId
from pymongo import MongoClient
from pymongo.server_api import ServerApi
import openai




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
def synthesis():
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

#get all synthesis 
@app.route("/syntheses/public", methods=["GET"])
def get_syntheses():
    syntheses = collection.find({"isPublic":True})
    syntheses = list(syntheses)
    for synthesis in syntheses:
        synthesis["_id"]=str(synthesis["_id"])
        synthesis = dict(synthesis)
        synthesis["recommendations"]  = [{'_id': str(rec['_id']), 'title': rec.get('title','NO TITLE'), 'tags': rec.get('tags','NO TAGS') } for rec in synthesis["recommendations"]]
    return jsonify(syntheses)


@app.route("/synthesize", methods=["POST"])
def synthesize():
    openai.api_key = "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"
    prompt =" Can you please help me generate a synthesis document to aid me in my studies using my class \
                        notes and lecture transcription. Please use the information from both sources to provide a \
                        comprehensive overview of the key concepts, themes, and ideas covered in the class.\n \
                        Here is the transcription: \n {input_transcript} \n \
                        And here is the notes : \n {input_notes}  \n \
                        Please generate your prompt in a html format and differenciate titles from paragraphs."
    
    transcript = "Quantum mechanics is a fundamental theory in physics that provides a description of the physical properties of nature at the scale of atoms and subatomic particles.[2]: 1.1  It is the foundation of all quantum physics including quantum chemistry, quantum field theory, quantum technology, and quantum information science. Classical physics, the collection of theories that existed before the advent of quantum mechanics, describes many aspects of nature at an ordinary (macroscopic) scale, but is not sufficient for describing them at small (atomic and subatomic) scales. Most theories in classical physics can be derived from quantum mechanics as an approximation valid at large (macroscopic) scale.[3] Quantum mechanics differs from classical physics in that energy, momentum, angular momentum, and other quantities of a bound system are restricted to discrete values (quantization); objects have characteristics of both particles and waves (wave–particle duality); and there are limits to how accurately the value of a physical quantity can be predicted prior to its measurement, given a complete set of initial conditions (the uncertainty principle). Quantum mechanics arose gradually from theories to explain observations that could not be reconciled with classical physics, such as Max Planck's solution in 1900 to the black-body radiation problem, and the correspondence between energy and frequency in Albert Einstein's 1905 paper, which explained the photoelectric effect. These early attempts to understand microscopic phenomena, now known as the 'old quantum theory', led to the full development of quantum mechanics in the mid-1920s by Niels Bohr, Erwin Schrödinger, Werner Heisenberg, Max Born, Paul Dirac and others. The modern theory is formulated in various specially developed mathematical formalisms. In one of them, a mathematical entity called the wave function provides information, in the form of probability amplitudes, about what measurements of a particle's energy, momentum, and other physical properties may yield. Overview and fundamental concepts Quantum mechanics allows the calculation of properties and behaviour of physical systems. It is typically applied to microscopic systems: molecules, atoms and sub-atomic particles. It has been demonstrated to hold for complex molecules with thousands of atoms,[4] but its application to human beings raises philosophical problems, such as Wigner's friend, and its application to the universe as a whole remains speculative.[5] Predictions of quantum mechanics have been verified experimentally to an extremely high degree of accuracy.[note 1] A fundamental feature of the theory is that it usually cannot predict with certainty what will happen, but only give probabilities. Mathematically, a probability is found by taking the square of the absolute value of a complex number, known as a probability amplitude. This is known as the Born rule, named after physicist Max Born. For example, a quantum particle like an electron can be described by a wave function, which associates to each point in space a probability amplitude. Applying the Born rule to these amplitudes gives a probability density function for the position that the electron will be found to have when an experiment is performed to measure it. This is the best the theory can do; it cannot say for certain where the electron will be found. The Schrödinger equation relates the collection of probability amplitudes that pertain to one moment of time to the collection of probability amplitudes that pertain to another."
    notes = "-schrodinger equation (important for exam) \n - understand the time evolution of a quantum state is described by the Schrödinger equation: \n \
    -Uncertainty principle \n - Heisenberg \n -main mathematical formulas in quantum mechanics."


    # Synthesize document using Synthesizer
    response = openai.Completion.create(
            engine= "text-davinci-003",
            prompt=prompt.format(input_transcript=transcript, input_notes=notes),
            max_tokens=1024,
            n=1,
            stop=None,
            temperature=0.5,
        ).choices[0].text.strip()


    return jsonify({"document": response})

    
    

if __name__ == "__main__":
    app.run(debug=True)
