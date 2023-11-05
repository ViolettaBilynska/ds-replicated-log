FROM python:3.9-slim

WORKDIR /app/src

COPY src/secondary/requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY src/secondary/secondary.py secondary.py
COPY src/ src/

CMD uvicorn secondary:app --host 0.0.0.0 --port $SECONDARY_PORT