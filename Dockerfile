FROM python:3.11-alpine

WORKDIR /app

# Добавляем src в PYTHONPATH
ENV PYTHONPATH=/app/src

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Делаем скрипт исполняемым
RUN chmod +x /app/start.sh

CMD ["/app/start.sh"]
