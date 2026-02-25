FROM node:20-alpine

WORKDIR /app

COPY package*.json ./
RUN npm ci

COPY . .

EXPOSE 4200

CMD ["sh", "-c", "node set-env.js && npx ng serve --host 0.0.0.0 --port 4200 --configuration production"]
