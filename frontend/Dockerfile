FROM nginx:alpine

RUN apk add --no-cache npm

WORKDIR /usr/src/app

# Dependencies
COPY package*.json .
RUN npm install

COPY . .
RUN mv config.nginx /etc/nginx/nginx.conf
RUN npm run build && cp -r dist/* /usr/share/nginx/html
