FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

COPY ars/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# общий код
COPY common/ /app/common/
RUN pip install -e /app/common

COPY ars/ /app/ars/

ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

CMD ["uvicorn", "ars.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
