PYTHONPATH="${PYTHONPATH}:$(pwd)/emgcli" EMG_CONFIG=config/local.yml python3 emgcli/manage.py "$@"
