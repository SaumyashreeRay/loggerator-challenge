FROM python:3.11-slim-buster

WORKDIR /app

COPY .dockerignore ./

COPY ./requirements.txt ./requirements.txt

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Make port 1234 available outside this container
EXPOSE 1234

# Run loggerator_challenge.py when the container launches
CMD ["python", "loggerator_challenge.py"]
