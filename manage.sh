PYTHONPATH="${PYTHONPATH}:$(pwd)/emgcli" EMG_CONFIG=config/local-mysql.yml python3 emgcli/manage.py "$@"
