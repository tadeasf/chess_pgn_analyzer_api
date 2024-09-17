# Use an official Python runtime as a parent image
FROM python:3.12-slim

# Set the working directory in the container
WORKDIR /app

# Install necessary tools and wget
RUN apt-get update && apt-get install -y \
    wget \
    && rm -rf /var/lib/apt/lists/*

# Download and install pre-built Stockfish
RUN wget https://github.com/official-stockfish/Stockfish/releases/download/sf_16/stockfish-ubuntu-x86-64-modern.tar \
    && tar -xvf stockfish-ubuntu-x86-64-modern.tar \
    && mv stockfish /usr/local/bin/stockfish \
    && rm -rf stockfish-ubuntu-x86-64-modern.tar \
    && chmod +x /usr/local/bin/stockfish

# Copy the current directory contents into the container at /app
COPY . /app

# Install dependencies from requirements.lock, but allow pip to resolve conflicts
RUN pip install --no-cache-dir -r requirements.lock --use-pep517

# Make port 8000 available for the FastAPI app and 8501 for Streamlit
EXPOSE 8000 8501

# Create a script to run both FastAPI and Streamlit
RUN echo '#!/bin/bash\n\
ls -l /usr/local/bin/stockfish\n\
file /usr/local/bin/stockfish\n\
/usr/local/bin/stockfish --version\n\
uvicorn src.chess_pgn_analyzer_api.main:app --host 0.0.0.0 --port 8000 &\n\
streamlit run utils/dashboard.py --server.port 8501 --server.address 0.0.0.0\n\
wait' > /app/start.sh && \
    chmod +x /app/start.sh

# Run the script
CMD ["/app/start.sh"]