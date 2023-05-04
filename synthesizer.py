import openai
from dotenv import load_dotenv
import os

class Synthesizer:
    def __init__(self):

        load_dotenv()
        self.api_key = os.getenv("OPENAI_API_KEY")
        
        openai.api_key = self.api_key
        self.model_engine = "text-davinci-003"
        
        # GPT-3 prompt
        self.prompt = " based on some notes I have taken in class and the this transcription of my professor lecture, \
        generate a synthesized document for me to help me study. \
        Please arrange the synthesized document with subtitles to help me follow the different parts: \
        the transcription: \n {input_transcript}\
        the notes : \n {input_notes} \n "
        
    def generate_summary(self, transcript, notes):
        # Call the OpenAI API to generate a summary of the input text
        response = openai.Completion.create(
            engine=self.model_engine,
            prompt=self.prompt.format(input_transcript=transcript, input_notes=notes),
            max_tokens=1000,
            n=1,
            stop=None,
            temperature=0.5,
        )
        return response.choices[0].text.strip()
