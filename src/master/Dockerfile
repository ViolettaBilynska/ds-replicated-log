FROM python:3.9-slim

WORKDIR /app/src

COPY src/master/requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY src/master/master.py master.py
COPY src/ src/

EXPOSE 5000

CMD ["uvicorn", "master:app", "--host", "0.0.0.0", "--port", "5000"]