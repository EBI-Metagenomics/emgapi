#!/bin/bash

set -eux

entryPoint=${1:-}
pythonEnv=${PYTHONENV:-"python3.5"}
srcDir=${SRCDIR:-"${HOME}/src"}
venvDir=${VENVDIR:-"${HOME}/venv"}

create_venv() {
  $pythonEnv -m virtualenv $venvDir
}

activate_venv() {
  set +o nounset
  source $venvDir/bin/activate
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
  echo "Installing EMG..."
  pip install -U $srcDir
  pip install -U "django-redis>=4.4"
}

start() {
  echo "EMG API Start up..."

  # emgcli check --deploy
  emgcli migrate --fake-initial
  emgcli collectstatic --noinput

  # emgcli runserver 0.0.0.0:8000
  # emgunicorn
  gunicorn -p ~/emgvar/django.pid --bind 0.0.0.0:8000 --workers 5 --reload emgcli.wsgi:application

}

docker() {

  create_venv
  is_db_running "-u root -h mysql -P 3306"
  activate_venv
  pip install "git+git://github.com/ola-t/django-rest-framework-json-api@develop#egg=djangorestframework-jsonapi"
  install
  start

}

rm -f $srcDir/var/django.pid

if [ ! -z ${entryPoint} ] ; then
  eval $entryPoint
fi 
