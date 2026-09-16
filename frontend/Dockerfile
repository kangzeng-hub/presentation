FROM node:20-alpine AS build
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
ARG VITE_API_BASE_URL=http://localhost:4010
ENV VITE_API_BASE_URL=${VITE_API_BASE_URL}
RUN npm run build
FROM node:20-alpine
WORKDIR /app
RUN npm install --global serve@14
COPY --from=build /app/dist ./dist
EXPOSE 3000
CMD ["serve", "-s", "dist", "-l", "3000"]
