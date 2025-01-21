FROM python:3.10-slim

WORKDIR /app

COPY Pipfile Pipfile.lock* /app/

RUN pip install --no-cache-dir pipenv

RUN pipenv install --system --deploy

COPY . /app

EXPOSE 8082

CMD ["python", "app.py"]
