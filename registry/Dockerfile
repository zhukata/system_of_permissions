FROM python:3.11-slim

WORKDIR /src

RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

COPY registry/requirements.txt /src/requirements.txt
RUN pip install --no-cache-dir -r /src/requirements.txt

# общий код
COPY common/ /src/common/

COPY registry/ /src/registry/

ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

CMD ["uvicorn", "registry.app.main:app", "--host", "0.0.0.0", "--port", "8001"]
