FROM python:3.12-slim

WORKDIR /app

COPY pyproject.toml .
RUN pip install --no-cache-dir .

COPY config.py scraper.py bot.py main.py web_setup.py ./

RUN mkdir -p /app/data

ENV CONFIG_FILE=/app/data/config.json

CMD ["python", "main.py"]
