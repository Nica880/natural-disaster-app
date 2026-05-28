# syntax=docker/dockerfile:1.7
#
# Camera simulator — static HTML + sample images served by nginx.
# Replaces `python3 -m http.server 5174` with a containerised equivalent.
#
FROM nginx:alpine
COPY . /usr/share/nginx/html
EXPOSE 80
