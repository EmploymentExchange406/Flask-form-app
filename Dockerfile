# Use official Python image
FROM python:3.11

# Set working directory
WORKDIR /app

# Copy all files into the container
COPY . ./app

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose the port Flask runs on
EXPOSE 5000

# Command to run the app
CMD ["python", "flask_app.py"]

