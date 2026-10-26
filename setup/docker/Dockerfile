# 1) use the same python version as the project lock
FROM python:3.12-slim
WORKDIR /app
ENV FLASK_HOST=0.0.0.0

# 2) install our shared dependencies before copying application files
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 3) seed local mongodb and start flask
COPY . .
CMD ["python", "setup/setup.py"]
