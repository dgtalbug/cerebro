# docker/ui.Dockerfile — PLACEHOLDER.
# Builds the static UI and serves it from nginx-alpine. The hardened build
# (healthchecks, digest-pinned bases) lands with the production packaging work.

# ---- Stage 1: builder ----
FROM node:22-alpine AS builder
RUN npm install -g pnpm@11.1.2
WORKDIR /build
COPY ui/package.json ui/pnpm-lock.yaml ui/pnpm-workspace.yaml ./
RUN pnpm install --frozen-lockfile
COPY ui/ ./
ARG VITE_API_URL=/api
ENV VITE_API_URL=$VITE_API_URL
RUN pnpm build

# ---- Stage 2: runtime ----
FROM nginx:1.27-alpine AS runtime
COPY docker/nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=builder /build/dist /usr/share/nginx/html
EXPOSE 80
