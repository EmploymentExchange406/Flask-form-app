# Use official Python image
FROM python:3.11

# Set working directory
WORKDIR /app

# Use official Python image
FROM python:3.11

# Set working directory inside container
WORKDIR /app

# Copy all project files into /app
COPY . .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose Flask port
EXPOSE 5000

# Run your app using gunicorn
CMD ["gunicorn", "flask_app:app"]
