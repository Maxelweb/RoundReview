FROM python:3.12-slim-bullseye
COPY ./app /app/app
COPY ./database /app/database
COPY ./requirements.txt /app/requirements.txt
COPY ./main.py /app/main.py
WORKDIR /app
RUN pip install -r requirements.txt
CMD [ "python", "main.py" ]
