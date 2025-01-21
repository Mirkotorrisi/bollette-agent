# Usa una base ufficiale Python
FROM python:3.10-slim

# Imposta la directory di lavoro all'interno del container
WORKDIR /app

# Copia solo il Pipfile e il Pipfile.lock (se presente) nella directory di lavoro
COPY Pipfile Pipfile.lock* /app/

# Installa pipenv
RUN pip install --no-cache-dir pipenv

# Installa le dipendenze del progetto senza creare un ambiente virtuale
RUN pipenv install --system --deploy

# Copia il resto del codice del progetto nella directory di lavoro
COPY . /app

# Esponi la porta (se necessaria per il tuo servizio)
EXPOSE 3000

# Comando di default per avviare il tuo servizio
CMD ["python", "app.py"]
