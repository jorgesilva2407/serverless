FROM --platform=linux/amd64 python:3.12-alpine

WORKDIR /app

COPY requirements.txt /app/requirements.txt

RUN pip install -r /app/requirements.txt

COPY dashboard.py /app/dashboard.py

EXPOSE 8050

CMD ["python", "/app/dashboard.py"]