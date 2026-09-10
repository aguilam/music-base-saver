FROM node:22.23-bookworm-slim AS frontend
WORKDIR /app

COPY interfaces/music_saver/package*.json ./
RUN npm ci

COPY interfaces/music_saver/ ./

RUN npm run build

FROM python:3.12.14-slim-bookworm
WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY main.py .
COPY core ./core
COPY cli ./cli
COPY interfaces/base_interface.py interfaces/base_interface.py
COPY interfaces/subsonic_api interfaces/subsonic_api
COPY interfaces/music_saver/main.py interfaces/music_saver/main.py
COPY --from=frontend /app/dist ./interfaces/music_saver/dist

CMD ["python", "main.py"]