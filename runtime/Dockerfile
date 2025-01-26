# Use Python as the base image
FROM python:3.10-slim

# Set the working directory
WORKDIR /app

# Copy the runtime script and requirements
COPY runtime.py /app/runtime.py
COPY requirements.txt /app/requirements.txt

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Run the runtime
CMD ["python", "-u","/app/runtime.py"]


