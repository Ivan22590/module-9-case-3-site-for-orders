#!/usr/bin/env bash
# ============================================================
# setup.sh — первичная настройка стека module_9_case_3_site_for_orders
# Запуск: bash setup.sh   (из папки проекта, один раз с sudo:
#                         sudo bash setup.sh)
# ============================================================
set -euo pipefail

cd "$(dirname "$0")"

echo "==> 1/5 Проверка docker и docker compose..."
if ! command -v docker >/dev/null 2>&1; then
    echo "Docker не установлен. Установите: curl -fsSL https://get.docker.com | sh"
    exit 1
fi
docker compose version >/dev/null 2>&1 || {
    echo "docker compose plugin не найден"; exit 1;
}

echo "==> 2/5 Доступ к docker.sock для обычного пользователя..."
# Целевой пользователь: тот, кто вызвал sudo, либо текущий
TARGET_USER="${SUDO_USER:-$USER}"
if getent group docker | grep -q ":${TARGET_USER}\$\|,${TARGET_USER}\$"; then
    echo "   ${TARGET_USER} уже в группе docker."
else
    echo "   Добавляю ${TARGET_USER} в группу docker..."
    if [ "$(id -u)" -eq 0 ]; then
        usermod -aG docker "${TARGET_USER}"
    else
        sudo usermod -aG docker "${TARGET_USER}"
    fi
    echo "   Готово. Перелогиньтесь (переподключите SSH/VS Code),"
    echo "   после чего docker будет работать без sudo."
fi

echo "==> 3/5 Загрузка переменных окружения..."
# shellcheck disable=SC1091
set -a; source .env; set +a
echo "   NGINX_PORT=${NGINX_PORT}, REGISTRY_PORT=${REGISTRY_PORT}"
echo "   Внешний доступ: http://$(hostname -I | awk '{print $1}'):${NGINX_PORT}"

echo "==> 4/5 Генерация htpasswd для registry..."
AUTH_DIR="registry/auth"
if [ ! -f "${AUTH_DIR}/htpasswd" ]; then
    mkdir -p "${AUTH_DIR}"
    docker run --rm --entrypoint htpasswd httpd:2-alpine \
        -Bbn "${REGISTRY_USER}" "${REGISTRY_PASSWORD}" > "${AUTH_DIR}/htpasswd"
    chmod 644 "${AUTH_DIR}/htpasswd"
    echo "   Файл ${AUTH_DIR}/htpasswd создан для пользователя: ${REGISTRY_USER}"
else
    echo "   ${AUTH_DIR}/htpasswd уже существует — пропускаю."
fi

echo "==> 5/5 Запуск стека (docker compose up -d --build)..."
docker compose up -d --build

echo
echo "============================================================"
echo "Готово! Проверьте в браузере:"
echo "  Фронтенд (nginx):  http://$(hostname -I | awk '{print $1}'):${NGINX_PORT}"
echo "  pgAdmin:           http://$(hostname -I | awk '{print $1}'):5050"
echo "                     login: ${PGADMIN_EMAIL} / пароль из .env"
echo "  Registry API:      http://$(hostname -I | awk '{print $1}'):${REGISTRY_PORT}"
echo
echo "Для docker push с локальной машины:"
echo "  docker login $(hostname -I | awk '{print $1}'):${REGISTRY_PORT}"
echo "  (логин: ${REGISTRY_USER}, пароль: REGISTRY_PASSWORD из .env)"
echo
echo "На локальной машине добавьте insecure-registries:"
echo "  { \"insecure-registries\": [\"$(hostname -I | awk '{print $1}'):${REGISTRY_PORT}\"] }"
echo "============================================================"