# Use the official Python image as the base image
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app

# Copy the requirements.txt file to the container
COPY requirements.txt ./

# Install the Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code to the container
COPY . .

# Copy the gunicorn_config.py file to the container
COPY gunicorn_config.py .

# Set the environment variable for Flask
ENV FLASK_APP=main.py

# Expose the port on which the Flask app will run
EXPOSE 8000

# Start the Flask app with Gunicorn using the gunicorn_config.py file
CMD ["gunicorn", "--config", "gunicorn_config.py", "main:app"]