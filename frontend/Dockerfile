# Immagine del front-end per lo sviluppo: server Vite con ricaricamento automatico
FROM node:22-alpine

WORKDIR /app

# Prima le dipendenze (strato riutilizzato finché package.json non cambia), poi il codice
COPY package.json package-lock.json ./
RUN npm ci

COPY . .

EXPOSE 5173
CMD ["npm", "run", "dev"]
