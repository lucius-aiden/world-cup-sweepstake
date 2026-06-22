FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY config ./config
COPY src ./src
COPY README.md .

RUN mkdir -p data output

CMD ["python", "-m", "src.main", "run-once"]

