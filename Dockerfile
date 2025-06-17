# syntax=docker/dockerfile:1

FROM python:3.13-alpine
LABEL authors="Dolphin"

#ENTRYPOINT ["top", "-b"]

COPY ./requirements.txt /app/requirements.txt
WORKDIR /app
RUN pip install -r requirements.txt
COPY . /app

CMD [ "flask","--app", "Drop-Recovery-Predictor", "run", "--debug", "--host=0.0.0.0" ]