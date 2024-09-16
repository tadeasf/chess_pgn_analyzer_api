# Use an official Python runtime as a parent image
FROM python:3.12-slim

# Set the working directory in the container
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Install any needed packages specified in pyproject.toml
RUN pip install --no-cache-dir rye
RUN rye sync

# Make port 8000 available to the world outside this container
EXPOSE 8000

# Run the application
CMD ["python", "run.py"]
