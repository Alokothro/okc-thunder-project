# Use Node 16
FROM node:16-alpine

# Set working directory
WORKDIR /app

# Copy package files first for better caching
COPY package*.json ./

# Install dependencies with legacy peer deps
RUN npm ci --legacy-peer-deps

# Copy all application files
COPY . .

# Build the Angular application
RUN npm run build

# Expose port (Railway uses PORT env var)
EXPOSE 8080

# Start the Express server
CMD ["node", "server.js"]