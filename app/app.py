import os
from pathlib import Path
import whisper
import streamlit as st
from pydub import AudioSegment

st.set_page_config(
    page_title="Automatic Speech Recognition with whisper",
    page_icon="💬",
    # layout="wide",
    initial_sidebar_state="auto",
)

UPLOAD_DIR = Path("audios/")
DOWNLOAD_DIR = Path("downloads/")
TRANSCRIPT_DIR = Path("transcripts/")

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

# @st.cache(persist=True, allow_output_mutation=False, show_spinner=True, suppress_st_warning=True)
def convert_to_mp3(input_file):
    file_extension = input_file.name.split('.')[-1].lower()
    convert_method = FORMAT_METHOD_MAP.get(file_extension)
    
    if convert_method:
        # Ensure the directories exist
        UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
        DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)
        
        input_path = UPLOAD_DIR / input_file.name
        output_path = DOWNLOAD_DIR / (input_file.name.split('.')[0] + '.mp3')
        
        # Save the uploaded file to the input_path
        with input_path.open("wb") as f:
            f.write(input_file.getvalue())
        
        audio_data = convert_method(str(input_path))
        audio_data.export(str(output_path), format="mp3")
        return output_path
    return None


# @st.cache(persist=True, allow_output_mutation=False, show_spinner=True, suppress_st_warning=True)
def transcribe_audio(file_path, model_type):
    model = whisper.load_model(model_type)
    result = model.transcribe(file_path)
    return result["text"]

# @st.cache(persist=True, allow_output_mutation=False, show_spinner=True, suppress_st_warning=True)
def write_transcript(transcript, txt_file_path):
    with open(txt_file_path, "w") as f:
        f.write(transcript)

st.title("🗣 Automatic Speech Recognition with OpenAI Whisper")
st.info('This toom supports the following audio formats : WAV, MP3, MP4, OGG, WMA, AAC, FLAC, FLV')
uploaded_file = st.file_uploader("Upload audio file", type=list(FORMAT_METHOD_MAP.keys()))

if uploaded_file:
    with st.spinner(f"Audio file is being processed."):
        output_audio_path = convert_to_mp3(uploaded_file)
        audio_bytes = output_audio_path.read_bytes()
    
    st.markdown("---")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("Play back your file :")
        st.audio(audio_bytes)
    with col2:
        model_type = st.radio("Please choose your model (Small is the most common)", ('Tiny', 'Base', 'Small'),index=2).lower()

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
else:
    st.error('Please upload your audio file.')
