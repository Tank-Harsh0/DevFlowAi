# =============================================================================
# Stage 1 — Development
# Used by docker-compose.yml for hot-reload development.
# The production build stage below is available for deploying static assets.
# =============================================================================
FROM node:22-alpine AS development

WORKDIR /app

# Copy dependency manifests first so Docker can cache the npm install layer.
COPY package.json package-lock.json ./

RUN npm ci

# Source is mounted as a volume at runtime (see docker-compose.yml).
# This COPY is here so the image can also be used standalone without a volume.
COPY . .

EXPOSE 5173

# Bind to 0.0.0.0 so Vite is reachable from outside the container.
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]

# =============================================================================
# Stage 2 — Build
# Produces a minified static bundle from the TypeScript source.
# =============================================================================
FROM node:22-alpine AS build

WORKDIR /app

COPY package.json package-lock.json ./
RUN npm ci

COPY . .
RUN npm run build

# =============================================================================
# Stage 3 — Production
# Serves the compiled static assets with a lightweight HTTP server.
# Not used in local development; kept here for CI/CD and staging deployments.
# =============================================================================
FROM nginx:1.27-alpine AS production

# Copy compiled assets from the build stage.
COPY --from=build /app/dist /usr/share/nginx/html

# Minimal nginx config: single-page-app routing (all paths → index.html).
RUN printf 'server {\n\
    listen 80;\n\
    root /usr/share/nginx/html;\n\
    index index.html;\n\
    location / {\n\
        try_files $uri $uri/ /index.html;\n\
    }\n\
}\n' > /etc/nginx/conf.d/default.conf

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
