FROM python:3.9-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    software-properties-common \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy the requirements.txt file from one level before /app into the container
COPY ../requirements.txt ./requirements.txt

COPY ./app .

RUN pip3 install --upgrade pip
RUN pip3 install -r requirements.txt

EXPOSE 8502

ENTRYPOINT ["streamlit", "run", "app.py", "--server.port","8502","--server.baseUrlPath", "/whisper_asr","--logger.level=debug","--server.enableCORS=true", "--server.address","0.0.0.0"]
