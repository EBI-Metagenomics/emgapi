#!/bin/bash

set -eux

entryPoint=${1:-}
pythonEnv=${PYTHONENV:-"python3.5"}
srcDir=${SRCDIR:-"${HOME}/src"}
venvDir=${VENVDIR:-"${HOME}/venv"}

create_venv() {
  $pythonEnv -m virtualenv $VENVDIR
}

activate_venv() {
  set +o nounset
  source $VENVDIR/bin/activate
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
  pip install -U -r $SRCDIR/requirements.txt
}

start() {
  echo "EMG API Start up..."
  cd $SRCDIR

  # python emg/manage.py check --deploy
  python emg/manage.py migrate --fake-initial
  python emg/manage.py collectstatic --noinput
  # python emg/manage.py runserver 0.0.0.0:8000

  (cd emg && python $SRCDIR/venv/bin/gunicorn \
    -p $SRCDIR/django.pid \
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


rm -f $SRCDIR/django.pid

if [ ! -z ${entryPoint} ] ; then
  eval $entryPoint
fi 
