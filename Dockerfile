FROM python:3.12-slim

WORKDIR /app

COPY Pipfile Pipfile.lock* /app/

# Installa pipenv
RUN pip install --no-cache-dir pipenv

RUN pipenv requirements > requirements.txt && \
    pip install --no-cache-dir -r requirements.txt

COPY . /app

EXPOSE 8082

CMD ["python", "app.py"]
