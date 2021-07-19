FROM python:alpine

RUN adduser -s /sbin/nologin -S app && \
    mkdir -p /usr/src/app /run/backend && \
    chown app /usr/src/app /run/backend

RUN apk add --no-cache mariadb-connector-c-dev gcc musl-dev

WORKDIR /usr/src/app

# Dependencies
COPY --chown=app:nogroup requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt gunicorn

USER app

COPY . .

CMD ["gunicorn", "urlshortener.wsgi"]
