import whisper

# Function to transcribe an audio file
def transcribe_audio(file_path):
    # Load the Whisper model
    model = whisper.load_model("medium.en")

    # Load and preprocess the audio file
    audio = whisper.load_audio(file_path)
    audio = whisper.pad_or_trim(audio)
    mel = whisper.log_mel_spectrogram(audio).to(model.device)

    # Set the options for decoding
    options = whisper.DecodingOptions(language='en', fp16=False)

    # Transcribe the audio and return the text
    result = whisper.decode(model, mel, options)
    return result.text

# Main function
if __name__ == "__main__":
    # Path to the audio file
    audio_file_path = "audio.m4a"

    # Get the transcription
    transcription = transcribe_audio(audio_file_path)
    
    # Save the transcribed text to a file
    with open("output.txt", "w") as file:
        file.write(transcription)

    # Print a confirmation message
    print("Transcription completed and saved to output.txt")
