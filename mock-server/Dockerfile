FROM node:20-alpine
WORKDIR /app
COPY mock-server/package.json /app/package.json
COPY mock-server/server.mjs /app/server.mjs
COPY contracts/openapi.yaml /contracts/openapi.yaml
ENV CONTRACT_PATH=/contracts/openapi.yaml
EXPOSE 4010
CMD ["node", "server.mjs"]
