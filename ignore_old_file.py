import sounddevice as sd
import wavio as wv
import whisper
import multiprocessing
from pydub import AudioSegment
from pydub.playback import play
import pyautogui
import os
import random
from datetime import datetime, timedelta
from collections import deque
import AppKit
from pynput import keyboard

# Class for colored console output
class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

# Constants
SCREENSHOT_DIR = "./saved_screenshots"
RECORD_SECONDS = 5
RATE = 16000
CHANNELS = 1

question_started = False


# Function to play audio louder
def play_louder(file_path, volume_increase=0.50):
    audio = AudioSegment.from_file(file_path)
    louder_audio = audio + (10 * volume_increase)
    play(louder_audio)

# Function to get last five minutes from transcripts
def get_last_five_minutes(transcripts):
    now = datetime.now()
    five_minutes_ago = now - timedelta(minutes=5)
    return ' '.join(t for t, timestamp in transcripts if timestamp > five_minutes_ago)

# Function to capture a screenshot
def capture_screenshot():
    filename = f"{SCREENSHOT_DIR}/last_screenshot.png"
    if not os.path.exists(SCREENSHOT_DIR):
        os.makedirs(SCREENSHOT_DIR)
    screenshot = pyautogui.screenshot()
    screenshot.save(filename)
    return filename

# Function to copy text and image to clipboard
def copy_to_clipboard(prompt, image_path):
    clipboard = AppKit.NSPasteboard.generalPasteboard()
    clipboard.clearContents()

    # Copy image to clipboard
    img = AppKit.NSImage.alloc().initWithContentsOfFile_(image_path)
    if img is None:
        print(f"Error loading image from file: {image_path}")
        return
    clipboard.writeObjects_([img])

    # Copy text to clipboard
    ns_string = AppKit.NSString.stringWithString_(prompt)
    ns_data = ns_string.dataUsingEncoding_(AppKit.NSUTF8StringEncoding)
    clipboard.setData_forType_(ns_data, AppKit.NSStringPboardType)

    print("Image and prompt copied to clipboard")

# Function to record audio
def record(conn):
    print('Recording')
    while True:
        recording = sd.rec(int(RECORD_SECONDS * RATE), samplerate=RATE, channels=CHANNELS)
        sd.wait()
        wv.write("recording0.wav", recording, RATE, sampwidth=2)
        conn.send(True)

# Function to transcribe audio
def transcribe(conn):
    model = whisper.load_model("medium.en")
    capturing_question = False
    question_transcripts = []
    all_transcripts = deque()

    global question_started

    while True:
        if conn.recv():
            audio = whisper.load_audio("recording0.wav")
            audio = whisper.pad_or_trim(audio)
            mel = whisper.log_mel_spectrogram(audio).to(model.device)
            options = whisper.DecodingOptions(language='en', fp16=False)
            result = whisper.decode(model, mel, options)
            transcript = result.text

            # Clean up transcript
            for phrase in ["Thanks for watching!", "Thank you.", "I'll see you next time.", ".", "Question started", "I'm sorry", "Bye", "bye", "I'll see you guys next time", "Okay", "Questions started", "Question ended", "Passing it on to chat GPT now", "I'm not sure what I'm doing here", "Passing it on to chat GPT", "Thanks", "Thank you for watching", "I'm going to play a little bit of the game", "I'm not sure what to do"]:
                transcript = transcript.replace(phrase, "")
            if transcript:
                print(transcript)

            all_transcripts.append((transcript, datetime.now()))

            if capturing_question:
                question_transcripts.append(transcript)

            if question_started:
                capturing_question = True
                question_started = False
                question_transcripts = []

            if ("red" or "bread") in transcript.lower():
                transcript.replace("Red", "")
                transcript.replace("red", "")
                transcript.replace("Bread", "")
                transcript.replace("bread", "")
                transcript.replace("questions started", "")
                capturing_question = False
                question = ' '.join(question_transcripts)
                last_five_minutes = get_last_five_minutes(all_transcripts)
                screenshot_path = capture_screenshot()
                prompt = f"Please note that the following text may be finicky because it's transcribed. Just ignore any words that seem out of place... don't even mention them. Use your discretion on what I actually intended to say. \n\n My question is: {question}.\n\n\nFor context, here is the last five minutes of my lecture: {last_five_minutes}. Also attached is a screenshot of the current lecture slide."
                print(bcolors.OKGREEN + "\n\nQuestion Ended\n\n" + bcolors.ENDC)
                copy_to_clipboard(prompt, screenshot_path)
                print(prompt)
                rand = random.randint(1, 3)
                play_louder(f"./voices/ended_{rand}.mp3")

# Listener function for the keyboard shortcut
def on_activate():
    global question_started
    # Send a signal to start capturing the question
    question_started = True
    rand = random.randint(1, 4)
    print(bcolors.OKBLUE + "\n\nQuestion Started\n\n" + bcolors.ENDC)
    play_louder(f"./voices/started_{rand}.mp3")

def for_canonical(f):
    return lambda k: f(listener.canonical(k))

# Main function
if __name__ == "__main__":
    to_recorder, from_recorder = multiprocessing.Pipe()

    recorder = multiprocessing.Process(target=record, args=(to_recorder,))
    transcriber = multiprocessing.Process(target=transcribe, args=(from_recorder,))

    recorder.start()
    transcriber.start()

    # Define the hotkey
    hotkey = keyboard.HotKey(
        keyboard.HotKey.parse('<ctrl>+q'), on_activate)

    # Create a listener for the hotkey
    listener = keyboard.Listener(
        on_press=for_canonical(hotkey.press),
        on_release=for_canonical(hotkey.release))
    listener.start()

    recorder.join()
    transcriber.join()
    listener.join()
