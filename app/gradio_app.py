import gradio as gr
import os
from pathlib import Path
import whisper
from pydub import AudioSegment
import torch
from scipy.io.wavfile import write as wavwrite
import time
import random
import string

# Define directories and format map
UPLOAD_DIR = Path("audios/")
DOWNLOAD_DIR = Path("downloads/")
TRANSCRIPT_DIR = Path("transcripts_gradio/")
FORMAT_METHOD_MAP = {
    "wav": AudioSegment.from_wav,
    "mp3": AudioSegment.from_mp3,
    "ogg": AudioSegment.from_ogg,
    "wma": lambda path: AudioSegment.from_file(path, "wma"),
    "aac": lambda path: AudioSegment.from_file(path, "aac"),
    "flac": lambda path: AudioSegment.from_file(path, "flac"),
    "flv": AudioSegment.from_flv,
    "mp4": lambda path: AudioSegment.from_file(path, "mp4"),
}

def generate_unique_filename(extension=".wav"):
    """Generate a unique filename using timestamp and random string."""
    timestamp = int(time.time())
    random_str = ''.join(random.choices(string.ascii_lowercase + string.digits, k=5))
    return f"audio_{timestamp}_{random_str}{extension}"

def convert_to_mp3(input_data):
    """Convert uploaded/recorded audio to MP3 format."""
    # Check if the input is a tuple (indicating recorded audio)
    if isinstance(input_data, tuple):
        sample_rate, audio_data = input_data
        unique_file_name = generate_unique_filename()
        wav_path = UPLOAD_DIR / unique_file_name
        wavwrite(str(wav_path), sample_rate, audio_data)
        input_file_path = str(wav_path)
    else:
        input_file_path = input_data

    file_extension = os.path.splitext(input_file_path)[-1].lower().lstrip('.')
    unique_file_name = os.path.basename(input_file_path)
    
    # Ensure the directories exist
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)
    TRANSCRIPT_DIR.mkdir(parents=True, exist_ok=True)
    
    input_path = Path(input_file_path)
    output_path = DOWNLOAD_DIR / (unique_file_name.split('.')[0] + '.mp3')
    
    # Convert to MP3 if not already in that format
    if file_extension != 'mp3':
        convert_method = FORMAT_METHOD_MAP.get(file_extension)
        if convert_method:
            audio_data = convert_method(str(input_path))
            audio_data.export(str(output_path), format="mp3")
        else:
            return None
    else:
        os.rename(input_path, output_path)
    return output_path

def transcribe_audio(file_path, model_type):
    """Transcribe audio using the specified model."""
    model = whisper.load_model(model_type, device="cuda")
    result = model.transcribe(file_path)
    return result["text"]

def write_transcript(transcript, txt_file_path):
    """Write the transcript to a file."""
    with open(txt_file_path, "w") as f:
        f.write(transcript)

def asr_interface(upload_audio, record_audio, model_type):
    """Main function for Gradio interface."""
    # Check which audio input is used (uploaded or recorded)
    audio = upload_audio if upload_audio else record_audio

    output_audio_path = convert_to_mp3(audio)
    if output_audio_path:
        transcript = transcribe_audio(str(output_audio_path), model_type)
        transcript_file_path = TRANSCRIPT_DIR / (output_audio_path.stem + ".txt")
        write_transcript(transcript, transcript_file_path)
        return transcript_file_path.read_text()
    return "Failed to process the audio file."

# Set up Gradio UI
iface = gr.Interface(
    fn=asr_interface,
    inputs=[
        gr.Audio(type="filepath", label="Upload Audio"),
        gr.Audio(source="microphone", label="Record Audio"),
        gr.Radio(["base", "small"], label="Choose your model", value="base")
    ],
    outputs=gr.Textbox(label="Transcript"),
    live=True,
    title="Text-to-speech with OpenAI Whisper",
    description="Upload or record an audio file to get its transcript using OpenAI's Whisper.",
)
iface.launch()