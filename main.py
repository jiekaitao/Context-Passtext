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
import json

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

transcript = []
question_ended = False

# Function to play audio louder
def play_louder(file_path, volume_increase=0.50):
    audio = AudioSegment.from_file(file_path)
    louder_audio = audio + (10 * volume_increase)
    play(louder_audio)

# Function to get last five minutes from transcripts
def get_last_five_minutes(transcripts):
    now = datetime.now()
    five_minutes_ago = now - timedelta(minutes=15)
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

    all_transcripts = deque()

    while True:
        if conn.recv():
            audio = whisper.load_audio("recording0.wav")
            audio = whisper.pad_or_trim(audio)
            mel = whisper.log_mel_spectrogram(audio).to(model.device)
            options = whisper.DecodingOptions(language='en', fp16=False)
            result = whisper.decode(model, mel, options)
            last_transcript = result.text

            # Clean up transcript
            for phrase in ["Thanks for watching!", "Thank you.", "I'll see you next time.", ".", "Question started", "I'm sorry", "Bye", "bye", "I'll see you guys next time", "Okay", "Questions started", "Question ended", "Passing it on to chat GPT now", "I'm not sure what I'm doing here", "Passing it on to chat GPT", "Thanks", "Thank you for watching", "I'm going to play a little bit of the game", "I'm not sure what to do", "I'm not going to lie", "I'm not going to lie", "Shhh", "I'm not gonna lie", "🎶 Music 🎶", "🎶 Music Outro 🎶", "I'll see you guys in the next one", "I'll see you in the next video", "Music", "🎵"]:
                last_transcript = last_transcript.replace(phrase, "")
            # Append the transcript to all_transcripts
            if last_transcript.strip():
                all_transcripts.append((last_transcript, datetime.now()))
                print(last_transcript)

            # Check if question ended by reading variables.json
            try:
                with open("variables.json", "r") as file:
                    data = json.load(file)
                    last_keystroke_time = datetime.fromisoformat(data.get('last_keystroke', ''))
                    if datetime.now() - last_keystroke_time < timedelta(seconds=5):
                        # The rest of your code when the question ends
                        last_five_minutes = get_last_five_minutes(all_transcripts)
                        screenshot_path = capture_screenshot()
                        prompt = (f"Please note that the following text may be finicky because it's transcribed. "
                                  f"Also attached is a screenshot of the current lecture slide. Just ignore any words that seem out of place... "
                                  f"don't even mention them. Use your discretion on what I actually intended to say. \n\n\n"
                                  f"For context, I'll attach the last five minutes of what was spoken in my study room. "
                                  f"(it contains my question. There may be multiple questions in there. "
                                  f"You can refer to the screenshot, but don't say obvious stuff like 'I see that you've uploaded a screenshot.' And unless specified otherwisre, I only want you to answer my question. If I want you to walk me through the whole problem, I'll say so."
                                  f"Make sure you only respond to the latest question, which is most likely towards the end of the text, "
                                  f"and not any questions you've responded to already). Sometimes I may precede my question with 'Question,' Wheverever you can, refer back to what my professor said to help me make connections."
                                  f"\n\n\n"
                                  f"Here's the last 5 minutes of my lecture: {last_five_minutes}")
                        print(bcolors.OKGREEN + "\n\nQuestion Ended\n\n" + bcolors.ENDC)
                        copy_to_clipboard(prompt, screenshot_path)
                        print(prompt)
                        rand = random.randint(1, 11)
                        play_louder(f"./voices/ended_{rand}.mp3")
            except (FileNotFoundError, json.JSONDecodeError, KeyError) as e:
                print(f"Error reading from variables.json: {e}")

# Listener function for the keyboard shortcut
def on_activate():
    # Path to the JSON file
    json_file_path = "variables.json"

    data = {}

    # Update the timestamp for the last keystroke
    data['last_keystroke'] = datetime.now().isoformat()

    # Write the updated data back to the file
    with open(json_file_path, "w") as file:
        json.dump(data, file, indent=4)

    # print("Updated last_keystroke timestamp.")


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

"""The requirements to advance to COP3504C was recently updated and has become more stringent with the recent demand for CS degrees. Unfortunately, I (and several other students with prior knowledge in the course I've talked to) felt that the information in the course was repetitive—especially at the start of the course. I'm not an extremely experienced programmer and the tail end of the course DID teach me new information (such as Big O notation and basic algorithms). I've picked up an amateur's experience in full stack web development with MySQL, PHP, front-end, and Django. (I've spent about 2,500 hours in total working on a click-to-deploy peer tutoring website in High School) Although I've never had a formal education (and, again, I did learn many new things in this course), I felt that the exercises I had to do was mostly frustrating busy-work. During the first month of the semester, I was interested in machine learning. I remember waiting for Zybooks to finish animating a demonstration of print("Hello World") while I was working on code to train a convolutional neural network to detect, using sound from stereo microphone inputs, the approximate positions of viral symptoms like coughs and sneezes in an auditorium. I want to clarify that I don't see myself as someone who is "too good for school." I did appreciate the formal education and review of certain topics in Python, but I feel that I could have had this review with a much better-matched pacing if I was in COP3504C. 
 

I've emailed several advising offices and professors to try to advance to COP3504C, but I was repeatedly denied for not having an AP CS A score of 4 or higher. It seems like "prior experience" was a substitute for this requirement in past years and they've removed that pathway in response to overwhelming demand right as I entered UF as a freshman this year. I think it would be more efficient for students' tuition and time purposes if more resources were allocated to teaching the advanced course as high school programming experience is becoming more common with resources such as GitHub student pack and the more competitive admissions scene. Every quiz was a comical 20 minute review of the study guide and then a 20 minute quiz. Those 40 minutes in addition to maybe two hours attending the mandatory lab was all the weekly work I did for this class for the majority of the semester. I spent more time on my 1 credit-hour ethics class than this class. In other words, I didn't feel like I've learned 4-credit hours worth of information: my tuition money and time was wasted.

I understand the other major behind why they removed "prior experience" as a substitute for the CS score: some students in past years made it into the class with overblown confidence and fell flat on their faces.

I don't understand why an ALEKS-like benchmark exam can't help students figure out if they can advance."""

"""I would like to say some words about the COP3504C requirements here because, sadly, I don't feel like I'm being heard when I bring it up with administration.

The requirements to advance to COP3504C was recently updated and has become more stringent possibly partially due to the recent uptick in demand for CS degrees. Unfortunately, I (and several other students who tried to switch to COP3504) felt that the information in the course was repetitive—especially at the start of the course. I'm not an extremely experienced programmer and the tail end of the course DID teach me new information (such as Big O notation and basic algorithms). I've picked up an amateur's experience in full stack web development with MySQL, PHP, front-end, and Django. (I've spent about 2,500 hours in total working on a click-to-deploy peer tutoring website in High School) Although I've never had a formal education (and, again, I did learn many new things in this course), I felt that the exercises I had to do was mostly frustrating busy-work. I want to clarify that I don't see myself as someone who is "too good for school." I did appreciate the formal education and review of certain topics in Python, but I feel that I could have had this review with a much better-matched pacing if I was in COP3504C. 


During drop/add and at the beginning of the semester, I've emailed several advising offices and professors to try to advance to COP3504C, but I was repeatedly denied for not having an AP CS A score of 4 or higher. It seems like "prior experience" was a substitute for this requirement in past years and they've removed that pathway in response to overwhelming demand right as I entered UF as a freshman this year. I think it would be more efficient for students' tuition and time purposes if more resources were allocated to teaching the advanced course as high school programming experience is becoming more common with resources such as GitHub student pack and the more competitive admissions scene. Every week's workload was a comical 20 minute review of the study guide and then the 20 minute online quiz. Those 40 minutes in addition to maybe two hours attending the mandatory lab was all the weekly work I did for this class for the majority of the semester. I spent more time on my 1 credit-hour ethics class than this class. In other words, I didn't feel like I've learned 4-credit hours worth of information: my tuition money and time was wasted.

A former COP3504C professor told me of another reason as to why "prior experience" was removed as a substitute for the CS score: some students in past years made it into the class with insufficient prior experience and struggled.

I don't understand why UF won't allocate additional resources to teaching more COP3504C sections and design an ALEKS-like benchmark exam to determine whether students can advance. Of course, the volume of students has intensified over the last few years and maybe there's some logistical issues I don't know about, but the current situation as I experience it does not tell me that UF's plan to become an "AI" university is student-focused."""