set -u
source docker/urllib.sh

DB_READY=0
MAX_TRIES=50
MYSQL_ROOT_PASSWORD=123456

PORT=${DOCKERPORT:-80}

APP_URL=${APP_URL:-}
if [ -z "$APP_URL" ]; then
  echo "Please set the APP_URL environment variable"
  echo "e.g., 'export APP_URL=\"http://192.168.56.99\"'"
  exit -1
fi

proto=$(_protocol $APP_URL)
if [[ $proto != "http" && $proto != "https" ]]; then
  echo "ERROR - Your APP_URL needs a valid protocol (http://... or https://...)"
  exit -1
fi

SOLR=4.10.4
SOLRDELAY=${SOLRDELAY:-10} # interval to wait for dependent docker services to initialize
TRIES=0

docker stop openoni-dev || true
docker rm openoni-dev || true

# $1 = name of container, $2 = container running status
container_start () {
  echo "Existing $1 container found"
  if [ "$2" == "false" ]; then
    docker start $1
  fi
}

# Make sure settings_local.py exists so the app doesn't crash
if [ ! -f onisite/settings_local.py ]; then
  touch onisite/settings_local.py
fi

# Make sure we have a default urls.py
if [ ! -f onisite/urls.py ]; then
  cp onisite/urls_example.py onisite/urls.py
fi
