FROM python:3.11

RUN mkdir /file_downloader

WORKDIR /file_downloader

COPY requirements.txt .

RUN pip install -r requirements.txt

COPY . .

#WORKDIR services

ENV PYTHONPATH=/file_downloader

RUN chmod a+x docker/*.sh
#CMD gunicorn main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind=0.0.0.0:8000