FROM python:3

WORKDIR /app

COPY blivedm.py .
COPY main.py .
COPY requirements.txt .

RUN pip install -r requirements.txt

VOLUME /app/settings

CMD [ "main.py" ]

ENTRYPOINT ["python3"]