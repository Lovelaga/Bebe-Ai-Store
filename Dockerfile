# Use the official Python image
FROM python:3.9-slim

# Set the working directory in the cloud
WORKDIR /app

# Copy the tools list
COPY requirements.txt .

# Install the tools
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of your app code
COPY . .

# Open port 8080 for the world to see
EXPOSE 8080

# Command to start the AI Store
CMD ["gunicorn", "-b", "0.0.0.0:8080", "app:app"]
