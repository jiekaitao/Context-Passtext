import pyaudio
from vosk import Model, KaldiRecognizer
import os
import json
from collections import deque
from datetime import datetime, timedelta

# Constants
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 16000
CHUNK = 4000
RECORD_SECONDS = 5

# Load Vosk model
model = Model("./vosk-model-en-us-0.22")

# Initialize PyAudio
audio = pyaudio.PyAudio()

# Function to maintain the last five minutes of transcripts
def get_last_five_minutes(transcripts):
    now = datetime.now()
    five_minutes_ago = now - timedelta(minutes=5)
    return ' '.join(t for t, timestamp in transcripts if timestamp > five_minutes_ago)

# Main function for continuous capture and transcription
def continuous_transcription():
    stream = audio.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True, frames_per_buffer=CHUNK)
    recognizer = KaldiRecognizer(model, RATE)
    
    capturing_question = False
    question_transcripts = []
    all_transcripts = deque()  # to keep all the transcriptions

    print("Starting transcription...")
    while True:
        data = stream.read(CHUNK, exception_on_overflow=False)
        now = datetime.now()
        if recognizer.AcceptWaveform(data):
            result_json = recognizer.Result()
            result = json.loads(result_json)
            transcript = result.get("text", "")
            all_transcripts.append((transcript, now))  # Append with timestamp

            if "panera" in transcript.lower() and not capturing_question:
                print("----QUESTION STARTED----")
                capturing_question = True
                question_transcripts = []

            if capturing_question:
                question_transcripts.append(transcript)
                if "bread" in transcript.lower():
                    capturing_question = False
                    question = ' '.join(question_transcripts)
                    last_five_minutes = get_last_five_minutes(all_transcripts)
                    print("----QUESTION ENDED, PUSHING PROMPT----")
                    push_prompt(question, last_five_minutes)
            elif transcript:  # Only print when transcript is not empty
                print(transcript)
        else:
            result_json = recognizer.PartialResult()
            result = json.loads(result_json)
            transcript = result.get("partial", "")
            if transcript:  # Only print when partial transcript is not empty
                print(transcript, end='\r')

def push_prompt(question, last_five_minutes):
    prompt = f"""I have a question on the material I am studying: {question}.
    For context, here is the last five minutes of my lecture: {last_five_minutes}
    I have also attached a screenshot of exactly what I'm looking at for reference."""
    print(prompt)

# Start continuous transcription
continuous_transcription()
