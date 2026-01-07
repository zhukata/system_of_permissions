FROM python:3.11-slim

WORKDIR /src

RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

COPY ars/requirements.txt /src/requirements.txt
RUN pip install --no-cache-dir -r /src/requirements.txt

# общий код
COPY common/ /src/common/

COPY ars/ /src/ars/

ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/src

CMD ["uvicorn", "ars.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
