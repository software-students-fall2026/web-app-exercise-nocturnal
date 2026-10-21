# 1) use the same python version as the project lock file
FROM python:3.12-slim
WORKDIR /app

# 2) install the shared requirements before copying app files
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 3) copy the allowed files and run database setup before flask
COPY . .
CMD ["python", "setup/setup.py"]
