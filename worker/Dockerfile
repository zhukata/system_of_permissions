FROM python:3.11-slim

WORKDIR /src

RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

COPY worker/requirements.txt /src/requirements.txt
RUN pip install --no-cache-dir -r /src/requirements.txt

# общий код
COPY common/ /src/common/

COPY worker/ /src/worker/

ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/src

CMD ["python", "-m", "worker.app.workers.access_request_worker"]
