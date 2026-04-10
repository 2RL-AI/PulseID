FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        pcscd libpcsclite-dev swig gcc build-essential \
        libccid && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
RUN chmod +x entrypoint.sh

EXPOSE 5005

ENTRYPOINT ["./entrypoint.sh"]
CMD ["gunicorn", "wsgi:app", "--bind", "0.0.0.0:5005", "--workers", "1", "--threads", "4", "--timeout", "120"]
