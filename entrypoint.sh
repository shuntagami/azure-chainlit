#!/bin/sh
set -e

service ssh start
exec chainlit run app.py --host 0.0.0.0 --port 8000
