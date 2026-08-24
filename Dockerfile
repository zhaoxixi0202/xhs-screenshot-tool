FROM python:3.12-slim

ENV HOST=0.0.0.0
ENV PORT=8788
ENV CHROME_PATH=/usr/bin/chromium
ENV NODE_PATH=/usr/bin/node
ENV PYTHONUNBUFFERED=1

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        chromium \
        nodejs \
        fonts-noto-cjk \
        fonts-liberation \
        ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY . /app
EXPOSE 8788
CMD ["python", "app.py"]
