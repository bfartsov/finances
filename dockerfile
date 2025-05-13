FROM python:3.11 AS base
ENV PYTHONUNBUFFERED=1 \
    PYTHONFAULTHANDLER=1

RUN apt-get update && apt-get install -y \
    build-essential \
    python3-dev \
    libffi-dev \
    libssl-dev && rm -rf /var/lib/apt/lists/*

FROM base
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . /app/
EXPOSE 8501
ENTRYPOINT [ "streamlit", "run", "main.py"]
