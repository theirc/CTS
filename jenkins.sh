#!/bin/sh -ex

export LC_ALL=en_US.UTF-8

DB_NAME=cts
DB_COUNT=`psql -l | egrep '^ '$DB_NAME' ' | wc -l`
if [ $DB_COUNT -eq 0 ]; then createdb $DB_NAME; fi

# See where we came from:
git remote -v

# Create a clean test env
rm -f .coverage
rm -rf env
find . -name "*.pyc" -exec rm -rf {} \;
virtualenv -q --clear --python=/usr/bin/python2.7 env
. env/bin/activate
pip install -U pip
pip install -U setuptools
pip install -q -r requirements/dev.txt

# Run the tests
./run_tests.sh --noinput
