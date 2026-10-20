FROM nginx:1.27-alpine

# Убираем дефолтный конфиг, кладём свой
RUN rm -f /etc/nginx/conf.d/default.conf
COPY nginx.conf /etc/nginx/conf.d/app.conf

# Статика фронтенда
COPY html/ /usr/share/nginx/html/