# === Base Image for API ===
FROM python:3.11 AS api

WORKDIR /api
COPY api/ ./api/
RUN pip install --no-cache-dir -r api/requirements.txt

# === Base Image for UI ===
FROM node:20 AS ui

WORKDIR /ui
COPY ui/ ./ui/
RUN corepack enable && npm install && npm run build

# === Final Image ===
FROM python:3.11

WORKDIR /app
COPY --from=api /api /app/api
COPY --from=ui /ui/.output /app/ui

EXPOSE 8021 8022

CMD ["bash", "-c", "uvicorn api.main:app --host 0.0.0.0 --port 8021 & npx serve -s /app/ui -l 8022"]
