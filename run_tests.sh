#!/bin/sh

# Check PEP-8
if ! flake8; then
  echo "PEP-8 checking failed"
  exit 1
fi

export PYTHONWARNINGS=error:RuntimeWarning,error:RemovedInDjango18Warning,error:RemovedInDjango19Warning
coverage run manage.py test --settings=cts.settings.dev "$@" && coverage report
