# Immagine leggera con Python 3.12
FROM python:3.12-slim

# Evita file .pyc e mostra subito i log
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Prima le dipendenze: Docker le tiene in cache finché requirements.txt non cambia
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Poi il codice dell'applicazione
COPY . .

EXPOSE 8000

# All'avvio: aggiorna lo schema del database, poi avvia il server
CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000"]
