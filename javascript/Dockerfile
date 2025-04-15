FROM node:20-slim

# Copy package.json and install dependencies
COPY package.json package-lock.json* ./
RUN npm install

# Copy application code
COPY . ./

CMD ["node", "build/index.js"]
