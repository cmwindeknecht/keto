# Development stage
FROM node:20-alpine AS development

WORKDIR /app

# Copy env files for development
COPY .env .env.local* ./

# Copy package files
COPY frontend-react/package.json frontend-react/package-lock.json* ./

# Install dependencies
RUN npm ci || npm install

# Copy application code
COPY frontend-react/ .

# Expose port
EXPOSE 3000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost:3000 || exit 1

# Start development server
CMD ["npm", "run", "dev"]

# Production build stage
FROM node:20-alpine AS builder

WORKDIR /app

# Copy env files for build
COPY .env .env.local* ./

COPY frontend-react/package.json frontend-react/package-lock.json* ./

RUN npm ci || npm install

COPY frontend-react/ .

# Build Next.js app (uses NEXT_PUBLIC_* from .env.local)
RUN npm run build

# Production runtime stage
FROM node:20-alpine AS production

WORKDIR /app

# Copy node_modules from builder
COPY --from=builder /app/node_modules ./node_modules

# Copy built app from builder
COPY --from=builder /app/.next ./.next
COPY --from=builder /app/package.json ./
COPY --from=builder /app/public ./public

# Expose port
EXPOSE 3000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost:3000 || exit 1

# Start Next.js production server
CMD ["npm", "start"]
