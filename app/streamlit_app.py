import os
from pathlib import Path
import whisper
import streamlit as st
from pydub import AudioSegment
from audiorecorder import audiorecorder
import time
import shutil
    
# Set Streamlit page configuration
st.set_page_config(
    page_title="Text-to-speech with whisper",
    page_icon="💬",
    initial_sidebar_state="auto",
)

# Define directories for uploading, downloading, and storing transcripts
UPLOAD_DIR = Path("audios/")
DOWNLOAD_DIR = Path("downloads/")
TRANSCRIPT_DIR = Path("transcripts/")

# Map of supported audio formats and their corresponding conversion methods
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

# Set the title of the Streamlit app
st.title("🗣 Text-to-Speech with OpenAI Whisper")


# Function to convert uploaded/recorded audio to MP3 format
def convert_to_mp3(input_file):
    file_extension = input_file.name.split('.')[-1].lower()
    unique_file_name = input_file.name
    
    # Ensure the directories exist
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)
    TRANSCRIPT_DIR.mkdir(parents=True, exist_ok=True)
    
    input_path = UPLOAD_DIR / unique_file_name
    output_path = DOWNLOAD_DIR / (unique_file_name.split('.')[0] + '.mp3')
    
    # Save the uploaded file to the input_path
    with input_path.open("wb") as f:
        f.write(input_file.read())
    
    # Check if the file is already in MP3 format
    if file_extension == 'mp3':
        # If the file is already an MP3, copy it to the output directory and then remove the original
        shutil.copy(str(input_path), str(output_path))
        os.remove(str(input_path))
    else:
        try:
            # If the file is not an MP3, convert it
            convert_method = FORMAT_METHOD_MAP.get(file_extension)
            if convert_method:
                audio_data = convert_method(str(input_path))
                audio_data.export(str(output_path), format="mp3")
            else:
                return None  # Return None if the file format is not supported
        except IndexError:
            st.error('Failed to convert the MP4 file. It might not contain a valid audio stream.')
            return None
        except Exception as e:
            st.error(f"Failed to convert the file. Error: {e}")
            return None
    return output_path


def transcribe_audio(file_path, model_type):
    if model_type in ["Base","Small"]:
        model = whisper.load_model(model_type, device="cuda")
        result = model.transcribe(file_path)
    else:
        model = whisper.load_model(model_type, device="cpu")
        # Transcribe audio with the model without using FP16
        result = model.transcribe(file_path, fp16=False)
    
    st.toast(f'Detected language : {result["language"]}')
    return result["text"]

def write_transcript(transcript, txt_file_path):
    with open(txt_file_path, "w") as f:
        f.write(transcript)

# User interface for selecting the method of providing audio
option = st.selectbox('Select', ["Record Audio","Upload Audio"], placeholder="Select the method...", index=0)

uploaded_file = None
audio_path = None

# Handling audio recording or uploading based on user selection
if option == "Record Audio":
    source = "record"
    # Initialize the audio recorder
    audio = audiorecorder("Click to record", "Click to stop recording")
    
    if not audio.empty() and audio.duration_seconds > 0:
        # Generate a unique file name using a timestamp
        timestamp = int(time.time())
        unique_file_name = f"recorded_audio_{timestamp}.mp3"
        
        # Define the path for the recorded audio
        audio_path = UPLOAD_DIR / unique_file_name
        
        # Ensure the UPLOAD_DIR exists
        UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
        
        # Save the recorded audio to a file
        audio.export(audio_path, format="mp3")
        
        # Open the recorded audio file for processing
        uploaded_file = audio_path.open("rb")

        # Display audio properties
        st.write(f"Frame rate: {audio.frame_rate}, Frame width: {audio.frame_width}, Duration: {audio.duration_seconds} seconds")
else:
    source = "file"
    st.info('This tool supports the following audio formats : WAV, MP3, MP4, OGG, WMA, AAC, FLAC, FLV')
    uploaded_file = st.file_uploader("Upload audio file", type=list(FORMAT_METHOD_MAP.keys()))

# Process the uploaded/recorded audio and generate transcript
if uploaded_file is None:
    st.error('Please upload or record an audio file.')
else:
    with st.spinner(f"Audio file is being processed."):
        if source == "record":
            output_audio_path = audio_path
        else:
            output_audio_path = convert_to_mp3(uploaded_file)
        
        # Check if output_audio_path is not None before reading bytes
        if output_audio_path is not None:
            audio_bytes = output_audio_path.read_bytes()
        else:
            # Handle the case where output_audio_path is None
            st.error('Failed to process the audio file.')
            pass  # Skip the rest of the loop for this iteration
    
    st.markdown("---")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("Play back your file :")
        st.audio(audio_bytes)
    with col2:
        model_type = st.radio("Please choose your model :", ('Base', 'Small','Medium'),index=1).lower()

    if st.button("Generate Transcript"):
        with st.spinner(f"Generating Transcript..."):
            transcript = transcribe_audio(str(output_audio_path), model_type)
            transcript_file_path = TRANSCRIPT_DIR / (output_audio_path.stem + ".txt")
            write_transcript(transcript, transcript_file_path)
            transcript_content = transcript_file_path.read_text()

        # Split the transcript into lines based on line breaks
        lines = transcript_content.split('.')

        # Add a hyphen to the beginning of each non-empty line
        formatted_lines = [f"- {line}" if line.strip() else line for line in lines]

        # Join the formatted lines to create the final formatted transcript
        formatted_transcript = '\n'.join(formatted_lines)

        # Create an expander for the transcript
        with st.expander("View Transcript"):
            # Display the transcript inside the expander
            st.text_area("Transcript", formatted_transcript, height=200)
        
        if st.download_button(label="Download the transcript 📝", data=transcript_content, file_name=transcript_file_path.name, mime='text/plain'):
            st.success('✅ Download Successful !!')
    