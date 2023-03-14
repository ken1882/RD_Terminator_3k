bash -c '/home/compeador/miniconda3/bin/gunicorn --workers 1 --bind=0.0.0.0:12678 --timeout 300 --capture-output --log-level debug -m 007 app:app'
