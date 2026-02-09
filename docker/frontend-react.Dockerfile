# Development stage
FROM node:20-alpine AS development

WORKDIR /app

# Copy package files
COPY frontend-react/package.json frontend-react/package-lock.json* frontend-react/yarn.lock* ./

# Install dependencies
RUN if [ -f yarn.lock ]; then yarn install --frozen-lockfile; \
    elif [ -f package-lock.json ]; then npm ci; \
    else npm install; fi

# Copy application code
COPY frontend-react/ .

# Expose port
EXPOSE 3000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost:3000 || exit 1

# Start development server
CMD ["npm", "start"]

# Production build stage
FROM node:20-alpine AS builder

WORKDIR /app

COPY frontend-react/package.json frontend-react/package-lock.json* frontend-react/yarn.lock* ./

RUN if [ -f yarn.lock ]; then yarn install --frozen-lockfile; \
    elif [ -f package-lock.json ]; then npm ci; \
    else npm install; fi

COPY frontend-react/ .

RUN npm run build

# Production runtime stage
FROM nginx:alpine AS production

COPY --from=builder /app/build /usr/share/nginx/html

# Copy custom nginx config if needed
# COPY docker/nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
