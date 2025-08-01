# syntax=docker/dockerfile:1

#TODO figure out why alpine does not work with numpy
FROM python:3.13
LABEL authors="Dolphin"

#ENTRYPOINT ["top", "-b"]

COPY ./requirements.txt /app/requirements.txt
WORKDIR /app
RUN pip install -r requirements.txt
COPY . /app

WORKDIR /app/DropRecoveryPredictor

CMD [ "python", "app.py"]