FROM python:3.10-slim

# Install Playwright system dependencies
RUN apt-get update && apt-get install -y \
    wget gnupg ca-certificates curl \
    libnss3 libxss1 libasound2 libatk1.0-0 libcups2 \
    libdbus-1-3 libxshmfence1 libdrm2 libgbm1 libgtk-3-0 \
    libxcomposite1 libxdamage1 libxrandr2 libpango-1.0-0 \
    libatk-bridge2.0-0 libatspi2.0-0 libxext6 libxfixes3 \
    libx11-6 libx11-xcb1 libxcb1 libxcomposite1 libxshmfence1 \
    fonts-liberation libu2f-udev libvulkan1 libxkbcommon0 \
    && rm -rf /var/lib/apt/lists/*

# Install playwright chromium dependencies (OFFICIAL SCRIPT)
RUN pip install playwright && playwright install --with-deps chromium

WORKDIR /app
COPY . .

RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 10000

CMD ["uvicorn", "app:app", "--host=0.0.0.0", "--port=10000"]
