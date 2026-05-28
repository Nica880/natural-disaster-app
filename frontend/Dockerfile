# syntax=docker/dockerfile:1.7
#
# Frontend (Vite + React) — multi-stage:
#   1) node:alpine  — installs deps and runs `vite build`
#   2) nginx:alpine — serves the static bundle (~30 MB final image)
#
# `VITE_API_BASE` is baked into the bundle at build time, so override it via
# `--build-arg VITE_API_BASE=...` if you deploy on a host other than the
# developer's laptop.
#
ARG VITE_API_BASE=http://localhost:8000

FROM node:20-alpine AS build
WORKDIR /app

# Cache the dep layer.
COPY package.json package-lock.json* ./
RUN npm ci --no-audit --no-fund

COPY . .

ARG VITE_API_BASE
ENV VITE_API_BASE=${VITE_API_BASE}
RUN npm run build


FROM nginx:alpine AS runtime
COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
