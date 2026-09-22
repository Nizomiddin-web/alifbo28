FROM python:3.12-slim

WORKDIR /app
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUTF8=1 PYTHONIOENCODING=utf-8 LANG=C.UTF-8

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY yozuv/ ./yozuv/
COPY bot/ ./bot/

RUN mkdir -p /app/data
VOLUME ["/app/data"]

CMD ["python", "-m", "bot.main"]
