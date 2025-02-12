FROM python:3.9-slim

# Install system dependencies including X11, Qt, and MySQL dependencies
RUN apt-get update && apt-get install -y \
    python3-pyqt5 \
    pyqt5-dev-tools \
    qttools5-dev-tools \
    libgl1-mesa-glx \
    x11-xserver-utils \
    default-libmysqlclient-dev \
    pkg-config \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first to leverage Docker cache
COPY requirements.txt .

# Install Python packages including MySQL connector and nanoid
RUN pip install --no-cache-dir -r requirements.txt \
    && pip install --no-cache-dir mysqlclient PyMySQL nanoid

# Copy the rest of the application
COPY . .

# Set environment variable for display
ENV DISPLAY=:0

# Command to run the application
CMD ["python", "src/main.py"] 