FROM python:3.10-slim
LABEL maintainer='mykm3ua@gmail.com'

ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY . .

RUN pip install -r requirements.txt

CMD ["python", "train_station_api/manage.py", "runserver", "0.0.0.0:8000"]