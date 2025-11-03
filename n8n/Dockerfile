# Используем официальный Node.js образ (LTS)
FROM node:20-alpine

# Устанавливаем зависимости для n8n
RUN apk add --no-cache \
    bash \
    curl \
    su-exec \
    tini \
    python3 \
    make \
    g++ \
    tzdata

# Создаём рабочую директорию
WORKDIR /data

# Устанавливаем n8n глобально
RUN npm install -g n8n@latest

# Создаём пользователя n8n (без root)
RUN adduser -D -h /home/node -u 1000 node

# Папка для данных и разрешения
RUN mkdir -p /home/node/.n8n && \
    chown -R node:node /home/node /data

# Переменные окружения по умолчанию
ENV N8N_USER_FOLDER=/home/node/.n8n
ENV N8N_LOG_LEVEL=info
ENV EXECUTIONS_PROCESS=main
ENV NODE_ENV=production
ENV TZ=Asia/Almaty

# Открываем порт
EXPOSE 5678

# Переходим под пользователя node
USER node

# Используем tini как init-процесс (чисто завершает процессы)
ENTRYPOINT ["tini", "--"]

# Команда запуска
CMD ["n8n", "start"]
