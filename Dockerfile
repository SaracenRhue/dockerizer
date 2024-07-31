FROM python:3.11-alpine

WORKDIR /app

COPY . .

RUN mkdir /project

VOLUME [ "/project" ]

CMD ["python", "main.py"]