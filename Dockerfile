# Используем официальный образ Python
FROM python:3.11-slim

# Устанавливаем рабочую директорию
WORKDIR /app

# Копируем все файлы из текущей директории в /app
COPY . .

# Устанавливаем зависимости Python
RUN pip install --no-cache-dir fastapi uvicorn

# Устанавливаем JDK 17
RUN apt-get update && \
    apt-get install -y --no-install-recommends openjdk-17-jre-headless && \
    rm -rf /var/lib/apt/lists/*

# Проверяем, существует ли JAR-файл в проекте
RUN if [ ! -f "bsl-language-server.jar" ]; then \
        echo "JAR-файл не найден. Устанавливаем curl и скачиваем JAR-файл..."; \
        apt-get update && \
        apt-get install -y curl && \
        curl -L -o bsl-language-server.jar https://github.com/1c-syntax/bsl-language-server/releases/download/v0.24.0-rc9/bsl-language-server-0.24.0-rc9-exec.jar; \
        apt-get remove -y curl && \
        apt-get autoremove -y && \
        rm -rf /var/lib/apt/lists/*; \
    else \
        echo "JAR-файл уже существует. Пропускаем скачивание."; \
    fi

# Устанавливаем права на запись
RUN chmod -R 777 /app

# Открываем порт 5000
EXPOSE 5000

# Запускаем сервер
CMD ["python3", "server.py"]
