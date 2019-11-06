PYTHONPATH="${PYTHONPATH}:$(pwd)/emgcli" EMG_CONFIG=docker/config.yaml python emgcli/manage.py "$@"
