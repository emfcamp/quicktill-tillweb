FROM alpine:3.13.2 AS builder

ARG THTTPD_VERSION=2.29

RUN apk add gcc musl-dev make

RUN wget https://acme.com/software/thttpd/thttpd-${THTTPD_VERSION}.tar.gz \
  && tar xzvf thttpd-${THTTPD_VERSION}.tar.gz \
  && mv /thttpd-${THTTPD_VERSION} /thttpd

RUN cd /thttpd && ./configure && make CCOPT='-O2 -s -static' thttpd

RUN adduser -D static

FROM emftillweb-app AS app
WORKDIR /app
ENV DJANGO_SETTINGS_MODULE=tillweb_infra.settings_production
COPY null-secret /app/config/secret_key
RUN ./manage.py collectstatic --no-input

FROM scratch
EXPOSE 80
COPY --from=builder /etc/passwd /etc/passwd
COPY --from=builder /thttpd/thttpd /
COPY --from=app /app/static /web/static/
USER static
WORKDIR /web
CMD [ "/thttpd", "-D", "-h", "0.0.0.0", "-d", "/web", "-u", "static", "-l", "-", "-M", "60" ]
