#!/bin/bash

set -eux

entryPoint=${1:-}
pythonEnv=${PYTHONENV:-python3.5}
homeDir=${HOMEDIR:-$HOME}

create_venv() {
  $pythonEnv -m virtualenv $homeDir/venv
}

activate_venv() {
  set +o nounset
  source $homeDir/venv/bin/activate
  set -o nounset
  python -V
}

is_db_running() {
  local conn=${1:-};

  echo "DB startup..."
  until mysql $conn -e 'show databases;'; do
    >&2 echo "MySQL is unavailable - sleeping"
    sleep 5
  done
  >&2 echo "MySQL now accepts connections, creating database..."
}

install() {
  echo "Installing EMG dependencies..."
  pip install -U pip
  pip install -U -r $homeDir/src/requirements.txt
}

start() {
  echo "EMG API Start up..."
  cd $homeDir/src

  # python emg/manage.py check --deploy
  python emg/manage.py migrate --fake-initial
  python emg/manage.py collectstatic --noinput
  # python emg/manage.py runserver 0.0.0.0:8000

  (cd emg && python $homeDir/venv/bin/gunicorn \
    -p $homeDir/src/django.pid \
    --bind 0.0.0.0:8000 \
    --workers 5 \
    --timeout 30 \
    --max-requests 0 \
    emg.wsgi:application)
}

docker() {

  create_venv
  is_db_running "-u root -h mysql -P 3306"
  activate_venv
  install
  start

}

jenkins() {

  create_venv
  activate_venv
  install
  BUILD_ID=dontKillMe start

}


rm -f $homeDir/src/django.pid

if [ ! -z ${entryPoint} ] ; then
  eval $entryPoint
fi 
