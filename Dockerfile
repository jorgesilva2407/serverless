FROM python:3.12-alpine

WORKDIR /app

COPY requirements.txt /app/requirements.txt

RUN pip install -r /app/requirements.txt

COPY dashboard.py /app/dashboard.py

CMD ["python", "/app/dashboard.py"]