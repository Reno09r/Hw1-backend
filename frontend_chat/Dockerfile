# Используем полный образ Node.js для установки зависимостей и сборки проекта
FROM node:18-alpine AS builder

WORKDIR /app

# Копируем package.json и package-lock.json для кеширования зависимостей
COPY package*.json ./
RUN npm install

# Копируем остальные файлы проекта
COPY . .

# Собираем продакшн-сборку. Результат будет в папке /app/dist
RUN npm run build

# --- Ступень 2: Финальный образ (Runner) ---
# Используем легковесный образ Nginx для отдачи статики
FROM nginx:1.25-alpine

# Копируем статичные файлы, собранные на предыдущем шаге, в директорию Nginx по умолчанию
COPY --from=builder /app/dist /usr/share/nginx/html

# Копируем кастомную конфигурацию Nginx для этого фронтенда
# Эта конфигурация поможет правильно обрабатывать роутинг в Single Page Application (SPA)
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Nginx по умолчанию слушает порт 80
EXPOSE 80

# Команда для запуска Nginx в foreground режиме
CMD ["nginx", "-g", "daemon off;"]