FROM ubuntu:latest
MAINTAINER PSU Developers <something@psu.edu>

RUN set -u
RUN source docker/urllib.sh

ENV DB_READY 0
ENV MAX_TRIES 50
ENV MYSQL_ROOT_PASSWORD 123456

ENV PORT=${DOCKERPORT:-80}

ENV APP_URL=${APP_URL:-}
RUN if [ -z "$APP_URL" ]; then
  echo "Please set the APP_URL environment variable"
  echo "e.g., 'export APP_URL=\"http://192.168.56.99\"'"
  exit -1
fi

ENV proto=$(_protocol $APP_URL)
RUN if [[ $proto != "http" && $proto != "https" ]]; then
  echo "ERROR - Your APP_URL needs a valid protocol (http://... or https://...)"
  exit -1
fi

ENV SOLR=4.10.4
ENV SOLRDELAY=${SOLRDELAY:-10} # interval to wait for dependent docker services to initialize
ENV TRIES=0

RUN docker stop openoni-dev || true
RUN docker rm openoni-dev || true

# $1 = name of container, $2 = container running status
RUN container_start () {
  echo "Existing $1 container found"
  if [ "$2" == "false" ]; then
    docker start $1
  fi
}

# Make sure settings_local.py exists so the app doesn't crash
RUN if [ ! -f onisite/settings_local.py ]; then
  touch onisite/settings_local.py
fi

# Make sure we have a default urls.py
RUN if [ ! -f onisite/urls.py ]; then
  cp onisite/urls_example.py onisite/urls.py
fi
