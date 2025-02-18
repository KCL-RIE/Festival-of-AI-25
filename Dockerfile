# === Base Image for API ===
FROM python:3.11 AS api

WORKDIR /api
COPY api/ ./  # Fix: Ensure everything in /api is copied
RUN pip install --no-cache-dir -r requirements.txt

# === Base Image for UI ===
FROM node:20 AS ui

WORKDIR /ui
COPY ui/package.json ui/package-lock.json ./  # Copy package.json first for caching
RUN npm install

COPY ui/ ./  # Now copy the rest of the UI code
RUN npm run build

# === Final Image ===
FROM python:3.11

WORKDIR /app
COPY --from=api /api /app/api
COPY --from=ui /ui/dist /app/ui  

EXPOSE 8021 8022

CMD ["bash", "-c", "uvicorn api.main:app --host 0.0.0.0 --port 8021 & npx serve -s /app/ui -l 8022"]
