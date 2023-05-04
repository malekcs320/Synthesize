from flask import Flask, jsonify, request
from synthesizer import Synthesizer

app = Flask(__name__)

# Create a synthesizer object
synthesizer = Synthesizer()

@app.route('/synthesize', methods=['GET'])
def synthesize():
    # Get the input text 
    transcript = request.json['input_transcript']
    notes = request.json['notes']

    # Generate a summary using the synthesizer object
    summary = synthesizer.generate_summary(transcript, notes)

    # Return the summary as a JSON response
    return jsonify({'summary': summary})
