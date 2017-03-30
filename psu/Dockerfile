FROM ubuntu:latest
MAINTAINER PSU Developers <something@psu.edu>

RUN set -u
RUN source docker/urllib.sh

ENV DB_READY 0
ENV MAX_TRIES 50
ENV MYSQL_ROOT_PASSWORD 123456

ENV PORT=${DOCKERPORT:-80}

ENV APP_URL=${APP_URL:-}

ENV proto=$(_protocol $APP_URL)

ENV SOLR=4.10.4
ENV SOLRDELAY=${SOLRDELAY:-10} # interval to wait for dependent docker services to initialize
ENV TRIES=0






