# Foodgram


**Foodgram**, «Продуктовый помощник». Онлайн-сервис и API для публикации и обмена рецептами. Пользователи могут подписываться на авторов, добавлять рецепты в «Избранное» и скачивать сводный список продуктов для выбранных блюд.

## Ссылки

* **Проект:** \<url\_репозитория>
* **Админ-зона:** http\://<домен>/admin/
* **Документация API:** http\://<домен>/api/docs/

## Развертывание на удалённом сервере

1. Клонировать репозиторий:

   ```bash
   git clone <url_репозитория>
   cd foodgram-st
   ```
2. Установить Docker и Docker Compose:

   ```bash
   sudo apt install curl
   curl -fsSL https://get.docker.com -o get-docker.sh
   sh get-docker.sh
   sudo apt-get install docker-compose-plugin
   ```
3. Скопировать файлы из папки `infra` на сервер:

   ```bash
   scp infra/docker-compose.yml infra/nginx.conf username@IP:/home/username/
   ```
4. Настроить Secrets для GitHub Actions (`Settings > Secrets`):

   ```text
   SECRET_KEY
   DOCKER_USERNAME
   DOCKER_PASSWORD
   HOST
   USER
   PASSPHRASE   # если ключ защищён
   SSH_KEY
   TELEGRAM_TO
   TELEGRAM_TOKEN
   DB_ENGINE=django.db.backends.postgresql
   DB_NAME=postgres
   POSTGRES_USER=postgres
   POSTGRES_PASSWORD=postgres
   DB_HOST=db
   DB_PORT=5432
   ```
5. Запустить контейнеры:

   ```bash
   sudo docker compose up -d
   ```
6. Выполнить миграции и собрать статику:

   ```bash
   sudo docker compose exec backend python manage.py migrate
   sudo docker compose exec backend python manage.py collectstatic --noinput
   ```
7. Загрузить данные и создать суперпользователя:

   ```bash
   sudo docker compose exec backend python manage.py loaddata ingredients.json
   sudo docker compose exec backend python manage.py createsuperuser
   ```
8. Остановить контейнеры:

   ```bash
   sudo docker compose down -v
   sudo docker compose stop
   ```

После каждого пуша в ветку `master`:

* Проверка кода на соответствие PEP8 (flake8)
* Сборка и публикация Docker-образов на Docker Hub
* Автоматический деплой и уведомление в Telegram

## Локальный запуск

1. Клонировать репозиторий и перейти в папку проекта:

   ```bash
   git clone <url_репозитория>
   cd foodgram-st
   ```
2. Переименовать `infra/myenv.env` в `.env` и заполнить параметрами:

   ```ini
   DB_ENGINE=django.db.backends.postgresql
   DB_NAME=postgres
   POSTGRES_USER=postgres
   POSTGRES_PASSWORD=postgres
   DB_HOST=db
   DB_PORT=5432
   ```
3. Запустить контейнеры:

   ```bash
   docker compose up -d
   ```

Проект будет доступен по адресу: [http://localhost/](http://localhost/)
Документация — [http://localhost/api/docs/](http://localhost/api/docs/)

---
**Автор:** 
Леонид Крипаков
