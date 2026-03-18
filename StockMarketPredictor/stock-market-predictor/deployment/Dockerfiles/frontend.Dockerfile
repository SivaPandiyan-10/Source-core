FROM node:18 as build
WORKDIR /app
COPY ../../frontend/angular-dashboard/package.json ./
COPY ../../frontend/angular-dashboard/package-lock.json ./
RUN npm install
COPY ../../frontend/angular-dashboard .
RUN npm run build --prod

FROM nginx:alpine
COPY --from=build /app/dist/angular-dashboard /usr/share/nginx/html
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
