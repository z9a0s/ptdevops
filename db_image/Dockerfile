FROM postgres:14.12-bullseye
COPY init.sql /docker-entrypoint-initdb.d/
RUN apt update && apt install -y nano
RUN mkdir /archive && chown -R postgres:postgres /archive
