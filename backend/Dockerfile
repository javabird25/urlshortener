FROM python:alpine

RUN adduser -H -s /sbin/nologin -S app && \
    mkdir -p /usr/src/app && \
    chown app /usr/src/app

USER app
WORKDIR /usr/src/app

# Dependencies
COPY requirements.txt .
RUN pip install --user -r requirements.txt

COPY . .

CMD ["echo", "hello"]