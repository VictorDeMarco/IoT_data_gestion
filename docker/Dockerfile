FROM python:3.10.2-bullseye
WORKDIR /app
COPY docker/requirements.txt .

RUN pip3 install -r requirements.txt

COPY . .

CMD ["python3", "-m","flask","run","--host=0.0.0.0"]