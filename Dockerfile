# Image de base avec Node.js déjà installé
FROM node:20-slim

# Installer Python, pip et FFmpeg
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copier et installer les dépendances Node
COPY package.json ./
RUN npm install

# Copier et installer les dépendances Python
COPY requirements.txt ./
RUN pip3 install --break-system-packages -r requirements.txt

# Copier le reste du code
COPY . .

# Port utilisé par le serveur
EXPOSE 3000

# Démarrer le serveur Node (qui appelle pipeline.py en sous-processus)
CMD ["node", "server.js"]
