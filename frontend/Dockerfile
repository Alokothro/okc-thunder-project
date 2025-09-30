# Use Node 16
FROM node:16-alpine

# Set working directory
WORKDIR /app

# Copy package files
COPY package*.json ./

# Install all dependencies including devDependencies (needed for Angular CLI)
RUN npm ci --legacy-peer-deps

# Copy source files
COPY . .

# Build Angular app
RUN npx ng build --configuration production

# Expose port
EXPOSE 8080

# Start server
CMD ["node", "server.js"]