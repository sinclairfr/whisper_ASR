FROM python:3.9-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    software-properties-common \
    git \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Upgrade pip and install Python dependencies
COPY ../requirements.txt ./requirements.txt
RUN pip3 install --upgrade pip && \
    pip3 install -r requirements.txt

# Copy the app files
COPY ./app .

# EXPOSE 8503
EXPOSE 8503

# Expose port 7860 for Gradio
# EXPOSE 7860

ENTRYPOINT ["streamlit", "run", "streamlit_app.py", "--server.port","8503","--logger.level=debug","--server.enableCORS=true", "--server.address","0.0.0.0"]
# ENTRYPOINT ["python", "gradio_app.py"]
