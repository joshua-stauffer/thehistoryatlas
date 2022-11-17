FROM node:14 as build
WORKDIR /app
COPY package*.json ./
RUN npm ci
RUN npm install react-scripts
ENV PATH /app/node_modules/.bin:$PATH
RUN npm run build

FROM nginx:stable-alpine
COPY --from=build /app/build /usr/share/nginx/html
COPY nginx/nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]


