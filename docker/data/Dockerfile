FROM postgres:12-alpine as dumper
COPY emfcamp2022-anonymised.sql /docker-entrypoint-initdb.d/
RUN ["sed", "-i", "s/exec \"$@\"/echo \"skipping...\"/", "/usr/local/bin/docker-entrypoint.sh"]

ENV POSTGRES_USER=till
ENV POSTGRES_PASSWORD=till
ENV POSTGRES_DB=emfcamp
ENV PGDATA=/data

RUN ["/usr/local/bin/docker-entrypoint.sh", "postgres"]

FROM postgres:12-alpine
COPY --from=dumper /data $PGDATA
